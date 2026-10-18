"""直线界面基线，固定公开参数；所有种子和尺度对照均保留。"""
from .common import ROOT, SEEDS, create_run, save_config, save_csv, summarize, save_plot, plt
import argparse
import json
import traceback
from pathlib import Path
import numpy as np
from src.pde_models import StraightInterfaceProblem
from src.local_rann import solve_local, validation_metrics, random_collocation, interior_points, interface_points

BETAS = [(1,1),(10,1),(100,1),(1000,1),(1,10),(1,100),(1,1000)]


def plot_only(run):
    import csv
    rows=list(csv.DictReader((run/"raw/interface.csv").open(encoding="utf-8-sig")))
    fig,axes=plt.subplots(1,3,figsize=(14,4))
    for scaling in ["raw","balanced"]:
        for metric,ax in zip(["relative_l2","interface_flux_rms","condition_raw"],axes):
            for direction,style in [("left","o-"),("right","s--")]:
                xs=[];ys=[]
                for contrast in [1,10,100,1000]:
                    b1,b2=(contrast,1) if direction=="left" else (1,contrast)
                    block=[r for r in rows if r["variant"]=="jumps" and r["scaling"]==scaling and float(r["beta_left"])==b1 and float(r["beta_right"])==b2 and r["status"]=="ok"]
                    xs.append(contrast);ys.append(np.mean([float(r[metric]) for r in block]))
                ax.loglog(xs,ys,style,label=f"{scaling}, high beta on {direction}")
            ax.set(xlabel="Coefficient contrast",ylabel=metric);ax.grid(alpha=.3,which="both")
    axes[0].legend(fontsize=7)
    fig.suptitle("Straight interface; nonzero jumps; N=128/side, scale=2; means over 5 seeds")
    fig.text(.1,-.02,"Source: raw/interface.csv; physical flux error is NOT divided by beta",fontsize=8)
    save_plot(run,fig,"interface_contrast")
    path=run/"raw/representative_grid.csv"
    if path.exists():
        data=np.genfromtxt(path,delimiter=",",names=True,encoding="utf-8-sig")
        fig,axes=plt.subplots(1,3,figsize=(12,3.7))
        for ax,key,title in zip(axes,["exact","raw_abs_error","balanced_abs_error"],["Manufactured exact solution","Raw scaling absolute error","Balanced scaling absolute error"]):
            n=81
            mesh=ax.pcolormesh(data["x"].reshape(n,n),data["y"].reshape(n,n),data[key].reshape(n,n),shading="auto")
            fig.colorbar(mesh,ax=ax);ax.set(title=title,xlabel="x",ylabel="y",aspect="equal")
        fig.suptitle("beta=(1000,1); jumps model; N=128/side; seed=11")
        fig.text(.1,-.02,"Source: raw/representative_grid.csv; interface traces evaluated separately",fontsize=8)
        save_plot(run,fig,"interface_solution")


def run_experiment(run_id=None):
    run=create_run("exp02",run_id)
    config={"experiment":"exp02_interface","seeds":SEEDS,"betas":BETAS,"variants":["continuous","jumps"],
            "neurons_per_side":128,"scale":2,"interior_per_side":512,"interface_points":80,"boundary_per_segment":40,
            "scaling":["raw","balanced"],"boundary_weight":50,"interface_weight":50,"ridge":0,"rcond":1e-12,
            "poisson_limit_neurons":[64,128],"validation_grid_per_side":"83x83 midpoint", "interface_validation":257,
            "acceptance":"analytic-basis assembly/derivative tests first; balanced cases relative L2,value RMS,boundary RMS each <1e-2; physical flux reported without assuming high-contrast uniform accuracy",
            "timing":"solve_seconds=assembly, SVD solve and SVD diagnostic; validation excluded"}
    save_config(run,config)
    cases=[(v,b1,b2,s,128) for v in ["continuous","jumps"] for b1,b2 in BETAS for s in ["raw","balanced"]]
    cases += [("poisson",1,1,"balanced",n) for n in [64,128]]
    rows=[];coefficients={};representatives={}
    log=(run/"run.log").open("w",encoding="utf8")
    for variant,b1,b2,scaling,count in cases:
        for seed in SEEDS:
            row={"case_index":len(rows),"variant":variant,"beta_left":b1,"beta_right":b2,"scaling":scaling,"neurons_per_side":count,"seed":seed,"status":"ok"}
            try:
                problem=StraightInterfaceProblem(b1,b2,variant)
                solution=solve_local(problem,count,seed,scaling=scaling)
                row.update(validation_metrics(solution));row.update(solution.diagnostics)
                if not all(np.isfinite(v) for k,v in row.items() if isinstance(v,(float,int))):
                    raise FloatingPointError("指标出现非有限值")
                coefficients[f"case_{len(rows)}"]=np.concatenate(solution.coefficients)
                if variant=="jumps" and b1==1000 and b2==1 and seed==11:
                    representatives[scaling]=solution
            except Exception:
                row["status"]="failed";row["error"]=traceback.format_exc();log.write(row["error"]+"\n")
            rows.append(row)
            log.write(json.dumps(row,ensure_ascii=False)+"\n");log.flush()
            save_csv(run/"raw/interface.csv",rows)
    log.close()
    np.savez_compressed(run/"raw/solution_coefficients.npz",**coefficients)
    metrics=["relative_l2","max_abs","boundary_rms","interface_value_rms","interface_flux_rms","interface_flux_normalized","condition_raw","data_rank","solve_seconds"]
    save_csv(run/"tables/interface_summary.csv",summarize(rows,["variant","beta_left","beta_right","scaling","neurons_per_side"],metrics))
    if len(representatives)==2:
        axis=(np.arange(81)+.5)/81;xx,yy=np.meshgrid(axis,axis)
        points=np.column_stack((xx.ravel(),yy.ravel()));left=points[:,0]<.5
        grid=[]
        exact=np.where(left,representatives["raw"].problem.data(points,0)[0],representatives["raw"].problem.data(points,1)[0])
        values={}
        for scaling,solution in representatives.items():
            value=np.empty(len(points))
            for side,mask in [(0,left),(1,~left)]:value[mask]=solution.evaluate(points[mask],side)[0]
            values[scaling]=value
        for p,e,a,b in zip(points,exact,values["raw"],values["balanced"]):
            grid.append({"x":p[0],"y":p[1],"exact":e,"raw_numerical":a,"balanced_numerical":b,"raw_abs_error":abs(a-e),"balanced_abs_error":abs(b-e)})
        save_csv(run/"raw/representative_grid.csv",grid)
    plot_only(run)
    balanced=[r for r in rows if r["scaling"]=="balanced" and r["status"]=="ok"]
    acceptance={"runs":len(rows),"failed":sum(r["status"]!="ok" for r in rows),
                "balanced_worst_relative_l2":max(r["relative_l2"] for r in balanced),
                "balanced_worst_value_rms":max(r["interface_value_rms"] for r in balanced),
                "balanced_worst_boundary_rms":max(r["boundary_rms"] for r in balanced)}
    acceptance["baseline_passed"]=acceptance["failed"]==0 and all(acceptance[k]<1e-2 for k in ["balanced_worst_relative_l2","balanced_worst_value_rms","balanced_worst_boundary_rms"])
    (run/"acceptance.json").write_text(json.dumps(acceptance,indent=2),encoding="utf8")
    print(run);print(json.dumps(acceptance,indent=2),flush=True)
    return run


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--run-id");parser.add_argument("--plot-run")
    args=parser.parse_args()
    plot_only(Path(args.plot_run)) if args.plot_run else run_experiment(args.run_id)
