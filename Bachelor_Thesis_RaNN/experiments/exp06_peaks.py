"""预登记独立峰值比较，两个行预算，全部参数/种子保存。"""
from .common import SEEDS, create_run, save_config, save_csv, summarize, save_plot, plt
from pathlib import Path
import argparse
import csv
import json
import traceback
import numpy as np
from src.pde_models import PeakInterfaceProblem
from src.adaptive_sampling import compare_sampling
from src.local_rann import validation_metrics,interior_points,interface_points
from src.metrics import errors

METHODS=["A","B","C","D","D_unused"]


def save_model_data(run):
    """单独导出所有已登记模型的解析数据，供公式和边界/跳跃核查。"""
    points=[interior_points(81**2,i,uniform=True) for i in [0,1]]
    traces=[]
    for width in [.12,.06]:
        for beta in [1,1000]:
            model=PeakInterfaceProblem(beta,1,"jumps",width=width);rows=[]
            for side in [0,1]:
                values,forcing,gradient=model.data(points[side],side)
                for p,u,f,g in zip(points[side],values,forcing,gradient):rows.append({"side":side,"x":p[0],"y":p[1],"exact":u,"forcing":f,"ux":g[0],"uy":g[1]})
            save_csv(run/"raw"/f"manufactured_width{width:g}_beta{beta}.csv",rows)
            gamma=interface_points(521);gu,gq=model.jumps(gamma)
            for p,a,b in zip(gamma,gu,gq):traces.append({"width":width,"beta_left":beta,"beta_right":1,"x":p[0],"y":p[1],"jump_value":a,"jump_flux":b})
    save_csv(run/"raw/manufactured_interface.csv",traces)


def plot_only(run):
    rows=list(csv.DictReader((run/"raw/peaks.csv").open(encoding="utf-8-sig")))
    for scale in [2.,4.]:
        fig,axes=plt.subplots(2,2,figsize=(11,8))
        for ax,(width,beta) in zip(axes.ravel(),[(.12,1),(.12,1000),(.06,1),(.06,1000)]):
            for method in METHODS:
                xs=[];ys=[]
                for rounds in [3,6]:
                    block=[r for r in rows if float(r["width"])==width and int(r["beta_left"])==beta and float(r["scale"])==scale and int(r["rounds"])==rounds and r["method"]==method and r["status"]=="ok"]
                    xs.append(320+224*rounds+240);ys.append(np.mean([float(r["relative_l2"]) for r in block]))
                ax.plot(xs,ys,"o-",label=method)
            ax.set(yscale="log",xlabel="Total scalar equations",ylabel="Independent relative L2",title=f"width={width}; beta=({beta},1)")
            ax.set_xticks([1232,1904]);ax.grid(alpha=.3);ax.legend(fontsize=8)
        fig.suptitle(f"Independent peaks; N=128/side; scale={scale:g}; all 5-seed means")
        fig.text(.1,.005,"Source: raw/peaks.csv; fine test=161x161/side; budgets fixed before run",fontsize=8)
        fig.tight_layout(rect=[0,.03,1,.95])
        save_plot(run,fig,f"peaks_budget_scale{scale:g}")
    path=run/"raw/representative_grid.csv"
    if path.exists():
        data=np.genfromtxt(path,delimiter=",",names=True,encoding="utf-8-sig");n=121
        fig,axes=plt.subplots(2,3,figsize=(13,8))
        for ax,key in zip(axes.ravel(),["exact"]+[m+"_abs_error" for m in METHODS]):
            mesh=ax.pcolormesh(data["x"].reshape(n,n),data["y"].reshape(n,n),data[key].reshape(n,n),shading="auto")
            fig.colorbar(mesh,ax=ax);ax.set(title=key,xlabel="x",ylabel="y",aspect="equal")
        fig.suptitle("Fixed representative: width=.06, beta=(1000,1), scale=4, rounds=6, seed=11")
        fig.text(.1,.005,"Source: raw/representative_grid.csv; all five methods shown, individual color scales",fontsize=8)
        fig.tight_layout(rect=[0,.03,1,.95])
        save_plot(run,fig,"peaks_representative")


def run_experiment(run_id=None):
    run=create_run("exp06",run_id)
    save_config(run,{"experiment":"exp06_peaks","widths":[.12,.06],"betas":[[1,1],[1000,1]],"scales":[2,4],"rounds":[3,6],
                     "methods":METHODS,"seeds":SEEDS,"neurons_per_side":128,"budget_mode":"equations","final_equations":[1232,1904],
                     "peak_amplitude":.75,"peak_center":[.46,.55],"scaling":"balanced","interface_weight":50,"boundary_weight":50,
                     "rcond":1e-12,"ridge":0,"candidate_counts":[2048,2048,1024],"exploration":.2,
                     "fine_validation":"161x161 midpoint per side;521 interface","coarse_validation":"81x81 midpoint per side",
                     "timing":"point generation,all candidate residuals,allocations and all SVD solves; final validation/plots excluded"})
    save_model_data(run)
    validation=[interior_points(161**2,i,uniform=True) for i in [0,1]]
    coarse=[interior_points(81**2,i,uniform=True) for i in [0,1]]
    gamma=interface_points(521)
    rows=[];trace_rows=[];coefficients={};representatives={}
    log=(run/"run.log").open("w",encoding="utf8")
    for width in [.12,.06]:
        for beta in [1,1000]:
            problem=PeakInterfaceProblem(beta,1,"jumps",width=width)
            for scale in [2.,4.]:
                for rounds in [3,6]:
                    for method in METHODS:
                        for seed in SEEDS:
                            row={"case_index":len(rows),"width":width,"beta_left":beta,"beta_right":1,"scale":scale,"rounds":rounds,"method":method,"seed":seed,"status":"ok"}
                            try:
                                scope="unused" if method=="D_unused" else "all"
                                solution,trace,elapsed=compare_sampling(problem,"D" if method=="D_unused" else method,seed,"equations",128,scale,rounds,indicator_scope=scope)
                                row.update(validation_metrics(solution,validation,gamma));row.update(solution.diagnostics);row["total_seconds"]=elapsed
                                exact=np.concatenate([problem.data(coarse[i],i)[0] for i in [0,1]])
                                predicted=np.concatenate([solution.evaluate(coarse[i],i)[0] for i in [0,1]])
                                row["coarse_relative_l2"]=errors(predicted,exact)["relative_l2"]
                                row["grid_error_relative_change"]=abs(row["relative_l2"]-row["coarse_relative_l2"])/row["relative_l2"]
                                if solution.diagnostics["n_equations"]!=560+224*rounds:raise AssertionError("行预算不守恒")
                                if not all(np.isfinite(v) for v in row.values() if isinstance(v,(int,float))):raise FloatingPointError("指标非有限")
                                coefficients[f"case_{len(rows)}"]=np.concatenate(solution.coefficients)
                                for entry in trace:trace_rows.append({**{k:row[k] for k in ["case_index","method","width","beta_left","scale","rounds","seed"]},**entry})
                                if width==.06 and beta==1000 and scale==4 and rounds==6 and seed==11:representatives[method]=solution
                            except Exception:
                                row["status"]="failed";row["error"]=traceback.format_exc();log.write(row["error"]+"\n")
                            rows.append(row);log.write(json.dumps(row,ensure_ascii=False)+"\n");log.flush();save_csv(run/"raw/peaks.csv",rows)
                            if len(rows)%25==0:print("completed",len(rows),"/400",flush=True)
    log.close()
    save_csv(run/"raw/allocation_trace.csv",trace_rows)
    np.savez_compressed(run/"raw/solution_coefficients.npz",**coefficients)
    metrics=["relative_l2","max_abs","interface_value_rms","interface_flux_rms","total_seconds","condition_raw","condition_retained","data_rank","n_points","n_interface","grid_error_relative_change"]
    save_csv(run/"tables/peaks_summary.csv",summarize(rows,["width","beta_left","scale","rounds","method"],metrics))
    pairs=[]
    for width in [.12,.06]:
        for beta in [1,1000]:
            for scale in [2.,4.]:
                for rounds in [3,6]:
                    for seed in SEEDS:
                        matched={r["method"]:r for r in rows if r["width"]==width and r["beta_left"]==beta and r["scale"]==scale and r["rounds"]==rounds and r["seed"]==seed and r["status"]=="ok"}
                        for target in ["D","D_unused"]:
                            for baseline in ["A","B","C"]:
                                if target in matched and baseline in matched:
                                    for metric in ["relative_l2","interface_flux_rms","total_seconds"]:
                                        a,b=matched[target][metric],matched[baseline][metric]
                                        pairs.append({"width":width,"beta_left":beta,"scale":scale,"rounds":rounds,"seed":seed,"target":target,"baseline":baseline,"metric":metric,
                                                      "target_value":a,"baseline_value":b,"difference":a-b,"ratio":a/b})
    save_csv(run/"tables/paired_differences.csv",pairs)
    if len(representatives)==len(METHODS):
        axis=(np.arange(121)+.5)/121;x,y=np.meshgrid(axis,axis);points=np.column_stack((x.ravel(),y.ravel()));left=points[:,0]<.5
        model=representatives["A"].problem
        exact=np.where(left,model.data(points,0)[0],model.data(points,1)[0]);grid=[]
        values={}
        for method,solution in representatives.items():
            prediction=np.empty(len(points))
            for side,mask in [(0,left),(1,~left)]:prediction[mask]=solution.evaluate(points[mask],side)[0]
            values[method]=prediction
        for i,p in enumerate(points):grid.append({"x":p[0],"y":p[1],"exact":exact[i],**{m+"_abs_error":abs(v[i]-exact[i]) for m,v in values.items()}})
        save_csv(run/"raw/representative_grid.csv",grid)
    plot_only(run)
    print(run);print("runs",len(rows),"failed",sum(r["status"]!="ok" for r in rows),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--run-id");parser.add_argument("--plot-run")
    args=parser.parse_args();plot_only(Path(args.plot_run)) if args.plot_run else run_experiment(args.run_id)
