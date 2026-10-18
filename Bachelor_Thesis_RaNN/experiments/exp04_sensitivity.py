"""固定界面比例与单因素敏感性，保留全部参数而非只挑最好。"""
from .common import SEEDS, create_run, save_config, save_csv, summarize, save_plot, plt
from pathlib import Path
from time import perf_counter
import argparse
import csv
import json
import traceback
import numpy as np
from src.pde_models import StraightInterfaceProblem
from src.local_rann import solve_local,validation_metrics,interior_points,interface_points

BETAS=[(1,1),(1000,1),(1,1000)]
PROPORTIONS={"points":[(368,368,128),(304,304,256),(240,240,384),(176,176,512)],
             "equations":[(464,464,32),(432,432,64),(368,368,128),(240,240,256),(176,176,320)]}


def cases():
    base={"count":64,"scale":2.,"interface_weight":50.,"ridge":0.,"n_left":368,"n_right":368,"n_interface":128}
    result=[]
    for mode,allocations in PROPORTIONS.items():
        for b1,b2 in BETAS:
            for nl,nr,ng in allocations:
                result.append({**base,"study":"proportion","budget_mode":mode,"parameter":"n_interface","parameter_value":ng,
                               "beta_left":b1,"beta_right":b2,"n_left":nl,"n_right":nr,"n_interface":ng})
    for b1,b2 in BETAS:
        for count in [32,64,128,256]:
            result.append({**base,"study":"sensitivity","budget_mode":"points","parameter":"count","parameter_value":count,
                           "count":count,"beta_left":b1,"beta_right":b2})
    for parameter,values in [("scale",[.5,1.,2.,4.,8.]),("interface_weight",[1.,10.,50.,100.,500.]),("ridge",[0.,1e-12,1e-9,1e-6])]:
        for value in values:result.append({**base,"study":"sensitivity","budget_mode":"points","parameter":parameter,"parameter_value":value,parameter:value,"beta_left":1,"beta_right":1000})
    for nl,nr,ng in [(92,92,32),(184,184,64),(368,368,128),(736,736,256)]:
        result.append({**base,"study":"sensitivity","budget_mode":"points","parameter":"collocation_budget","parameter_value":nl+nr+ng,
                       "n_left":nl,"n_right":nr,"n_interface":ng,"beta_left":1,"beta_right":1000})
    return result


def plot_only(run):
    rows=list(csv.DictReader((run/"raw/sensitivity.csv").open(encoding="utf-8-sig")))
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for mode,ax in zip(["points","equations"],axes):
        for b1,b2 in BETAS:
            xs=[];means=[];stds=[]
            for nl,nr,ng in PROPORTIONS[mode]:
                b=[r for r in rows if r["study"]=="proportion" and r["budget_mode"]==mode and int(r["beta_left"])==b1 and int(r["beta_right"])==b2 and int(r["n_interface"])==ng and r["status"]=="ok"]
                vals=np.array([float(r["relative_l2"]) for r in b]);xs.append(ng);means.append(vals.mean());stds.append(vals.std(ddof=1))
            ax.errorbar(xs,means,yerr=stds,marker="o",capsize=3,label=f"beta=({b1},{b2})")
        ax.set(yscale="log",xlabel="Fixed interface points",ylabel="Relative L2 mean +/- sample std",title=f"Equal {mode} budget")
        ax.grid(alpha=.3);ax.legend(fontsize=8)
    fig.suptitle("Static random allocation follow-up; N=64/side; all 5 seeds")
    fig.text(.1,-.02,"Source: raw/sensitivity.csv (study=proportion); not a preselected optimal baseline",fontsize=8)
    save_plot(run,fig,"fixed_interface_proportions")
    fig,axes=plt.subplots(1,3,figsize=(13,4))
    for b1,b2 in BETAS:
        for ax,metric in zip(axes,["relative_l2","interface_flux_rms","condition_raw"]):
            xs=[];ys=[]
            for count in [32,64,128,256]:
                b=[r for r in rows if r["study"]=="sensitivity" and r["parameter"]=="count" and int(r["beta_left"])==b1 and int(r["beta_right"])==b2 and int(r["count"])==count and r["status"]=="ok"]
                xs.append(count);ys.append(np.mean([float(r[metric]) for r in b]))
            ax.loglog(xs,ys,"o-",label=f"beta=({b1},{b2})");ax.set(xlabel="Features per side",ylabel=metric);ax.grid(alpha=.3,which="both")
            from matplotlib.ticker import NullFormatter
            ax.set_xticks([32,64,128,256]);ax.set_xticklabels(["32","64","128","256"])
            ax.xaxis.set_minor_formatter(NullFormatter())
    axes[0].legend(fontsize=8)
    fig.suptitle("Width sensitivity; scale=2; 864 interior/interface points; 5-seed means")
    fig.text(.1,-.02,"Source: raw/sensitivity.csv (parameter=count); physical flux is unnormalized",fontsize=8)
    save_plot(run,fig,"width_sensitivity")


def run_experiment(run_id=None):
    run=create_run("exp04",run_id)
    setting=cases()
    save_config(run,{"experiment":"exp04_sensitivity","seeds":SEEDS,"cases":setting,"scaling":"balanced","boundary_weight":50,
                     "rcond":1e-12,"variant":"jumps","timing":"generation+assembly+solve+SVD diagnostic; validation excluded",
                     "design_status":"exploratory follow-up after exp03; all scans reported; no best-test-set baseline claim"})
    rows=[];coefficients={};log=(run/"run.log").open("w",encoding="utf8")
    for config in setting:
        for seed in SEEDS:
            row={"case_index":len(rows),**config,"seed":seed,"status":"ok"}
            try:
                start=perf_counter()
                interior=[interior_points(config["n_left"] if side==0 else config["n_right"],side,
                          np.random.default_rng(np.random.SeedSequence([seed,100,side]))) for side in [0,1]]
                interface=interface_points(config["n_interface"],np.random.default_rng(np.random.SeedSequence([seed,100,2])))
                problem=StraightInterfaceProblem(config["beta_left"],config["beta_right"],"jumps")
                solution=solve_local(problem,config["count"],seed,interior,interface,scale=config["scale"],interface_weight=config["interface_weight"],ridge=config["ridge"])
                row["total_seconds"]=perf_counter()-start
                row.update(solution.diagnostics);row.update(validation_metrics(solution))
                if not all(np.isfinite(v) for k,v in row.items() if isinstance(v,(int,float))):raise FloatingPointError("指标非有限")
                coefficients[f"case_{len(rows)}"]=np.concatenate(solution.coefficients)
            except Exception:
                row["status"]="failed";row["error"]=traceback.format_exc();log.write(row["error"]+"\n")
            rows.append(row);log.write(json.dumps(row,ensure_ascii=False)+"\n");log.flush()
            save_csv(run/"raw/sensitivity.csv",rows)
    log.close();np.savez_compressed(run/"raw/solution_coefficients.npz",**coefficients)
    save_csv(run/"tables/sensitivity_summary.csv",summarize(rows,["study","budget_mode","parameter","parameter_value","beta_left","beta_right"],
             ["relative_l2","interface_value_rms","interface_flux_rms","boundary_rms","condition_raw","condition_retained","data_rank","rank","total_seconds"]))
    plot_only(run)
    print(run);print("runs",len(rows),"failed",sum(r["status"]!="ok" for r in rows),flush=True)
    return run


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--run-id");parser.add_argument("--plot-run")
    args=parser.parse_args()
    plot_only(Path(args.plot_run)) if args.plot_run else run_experiment(args.run_id)
