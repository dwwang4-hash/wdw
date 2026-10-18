"""A/B/C/D及两项指标消融，独立点/行预算、全种子和完整成本。"""
from .common import SEEDS, create_run, save_config, save_csv, summarize, save_plot, plt
from pathlib import Path
import argparse
import csv
import json
import traceback
import numpy as np
from src.pde_models import StraightInterfaceProblem
from src.adaptive_sampling import compare_sampling
from src.local_rann import validation_metrics

METHODS=["A","B","C","D","D_minus_pde","D_minus_interface"]
BETAS=[(1,1),(1000,1),(1,1000)]


def plot_only(run):
    rows=list(csv.DictReader((run/"raw/sampling.csv").open(encoding="utf-8-sig")))
    for budget_mode in ["points","equations"]:
        fig,axes=plt.subplots(1,3,figsize=(14,4))
        for ax,(b1,b2) in zip(axes,BETAS):
            for index,method in enumerate(METHODS):
                block=[r for r in rows if r["budget_mode"]==budget_mode and r["method"]==method and int(r["beta_left"])==b1 and int(r["beta_right"])==b2 and r["status"]=="ok"]
                values=np.array([float(r["relative_l2"]) for r in block])
                ax.scatter(index+np.linspace(-.1,.1,len(values)),values,s=20,alpha=.7)
                if len(values):ax.plot(index,values.mean(),"k_",markersize=16)
            ax.set_xticks(range(len(METHODS)));ax.set_xticklabels(["A","B","C","D","D−PDE","D−Γ"],rotation=30)
            ax.set(yscale="log",ylabel="Independent relative L2",title=f"beta=({b1},{b2})");ax.grid(alpha=.3)
        fig.suptitle(f"Budget={budget_mode}; N=64/side; 3 adaptive rounds; all 5 seeds; black=mean")
        fig.text(.1,-.02,"Source: raw/sampling.csv; fixed test points excluded from selection",fontsize=8)
        save_plot(run,fig,f"sampling_errors_{budget_mode}")
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    for mode,marker in [("points","o"),("equations","s")]:
        for method in METHODS[:4]:
            block=[r for r in rows if r["budget_mode"]==mode and r["method"]==method and r["status"]=="ok"]
            axes[0].scatter([float(r["total_seconds"]) for r in block],[float(r["relative_l2"]) for r in block],marker=marker,s=20,label=f"{method}, {mode}",alpha=.7)
            axes[1].scatter([float(r["interface_value_rms"]) for r in block],[float(r["interface_flux_rms"]) for r in block],marker=marker,s=20,alpha=.7)
    axes[0].set(xscale="log",yscale="log",xlabel="Total solve+sampling time (s)",ylabel="Independent relative L2")
    axes[1].set(xscale="log",yscale="log",xlabel="Interface value RMS",ylabel="Physical flux RMS")
    for ax in axes:ax.grid(alpha=.3,which="both")
    axes[0].legend(fontsize=6,ncol=2)
    fig.suptitle("A/B/C/D: all seeds and 3 beta cases; N=64/side, scale=2")
    fig.text(.1,-.02,"Source: raw/sampling.csv; total time includes candidate evaluations and all refits",fontsize=8)
    save_plot(run,fig,"sampling_cost_and_interface")


def run_experiment(run_id=None):
    run=create_run("exp03",run_id)
    config={"experiment":"exp03_sampling","seeds":SEEDS,"betas":BETAS,"methods":METHODS,"budget_modes":["points","equations"],
            "variant":"jumps","neurons_per_side":64,"scale":2,"rounds":3,"exploration":.2,"scaling":"balanced",
            "initial_counts":[128,128,32],"fixed_add_counts":[80,80,32],"point_budget_per_round":192,"equation_budget_per_round":224,
            "minimum_add_counts":[16,16,8],"candidate_counts":[2048,2048,1024],"boundary_points":240,
            "validation":"83x83 midpoint per side;257 interface;83 per boundary segment",
            "random_streams":"features=[seed,side,200]; point groups=[seed,100,group]; candidate=[seed,300]; selection=[seed,400]",
            "objective":"block empirical RMS with fixed physical scales; no inverse-density weights",
            "timing":"all point generation,candidate residuals,allocations,assembly,SVD solves and diagnostics; excludes final validation/plot"}
    save_config(run,config)
    rows=[];traces=[];coefficients={}
    log=(run/"run.log").open("w",encoding="utf8")
    for mode in ["points","equations"]:
        for b1,b2 in BETAS:
            problem=StraightInterfaceProblem(b1,b2,"jumps")
            for method in METHODS:
                for seed in SEEDS:
                    row={"case_index":len(rows),"budget_mode":mode,"beta_left":b1,"beta_right":b2,"method":method,"seed":seed,"status":"ok"}
                    try:
                        solution,trace,elapsed=compare_sampling(problem,method,seed,mode)
                        row.update(validation_metrics(solution));row.update(solution.diagnostics);row["total_seconds"]=elapsed
                        if not all(np.isfinite(v) for k,v in row.items() if isinstance(v,(int,float))):raise FloatingPointError("指标非有限")
                        expected=1104 if mode=="points" else 1232
                        actual=solution.diagnostics["n_points" if mode=="points" else "n_equations"]
                        if actual!=expected:raise AssertionError(f"预算不守恒：{actual}!={expected}")
                        coefficients[f"case_{len(rows)}"]=np.concatenate(solution.coefficients)
                        for entry in trace:traces.append({**{k:row[k] for k in ["case_index","budget_mode","beta_left","beta_right","method","seed"]},**entry})
                    except Exception:
                        row["status"]="failed";row["error"]=traceback.format_exc();log.write(row["error"]+"\n")
                    rows.append(row);log.write(json.dumps(row,ensure_ascii=False)+"\n");log.flush()
                    save_csv(run/"raw/sampling.csv",rows)
                    if traces:save_csv(run/"raw/allocation_trace.csv",traces)
    log.close()
    np.savez_compressed(run/"raw/solution_coefficients.npz",**coefficients)
    metrics=["relative_l2","max_abs","interface_value_rms","interface_flux_rms","total_seconds","condition_raw","condition_retained","data_rank","n_points","n_equations","n_interface"]
    save_csv(run/"tables/sampling_summary.csv",summarize(rows,["budget_mode","beta_left","beta_right","method"],metrics))
    pairs=[]
    for mode in ["points","equations"]:
        for b1,b2 in BETAS:
            for seed in SEEDS:
                match={r["method"]:r for r in rows if r["budget_mode"]==mode and r["beta_left"]==b1 and r["beta_right"]==b2 and r["seed"]==seed and r["status"]=="ok"}
                if "D" not in match:continue
                for baseline in ["A","B","C","D_minus_pde","D_minus_interface"]:
                    if baseline not in match:continue
                    for metric in ["relative_l2","interface_value_rms","interface_flux_rms","total_seconds"]:
                        numerator=match["D"][metric];denominator=match[baseline][metric]
                        pairs.append({"budget_mode":mode,"beta_left":b1,"beta_right":b2,"seed":seed,"baseline":baseline,"metric":metric,
                                      "D_value":numerator,"baseline_value":denominator,"D_minus_baseline":numerator-denominator,"D_over_baseline":numerator/denominator})
    save_csv(run/"tables/paired_differences.csv",pairs)
    plot_only(run)
    print(run);print("runs",len(rows),"failed",sum(r["status"]!="ok" for r in rows),flush=True)
    return run


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--run-id");parser.add_argument("--plot-run")
    args=parser.parse_args()
    plot_only(Path(args.plot_run)) if args.plot_run else run_experiment(args.run_id)
