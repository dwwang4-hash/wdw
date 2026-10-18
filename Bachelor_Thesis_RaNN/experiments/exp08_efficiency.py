"""主峰值运行结束后串行计时，隔离本项目其他计算任务。"""
from .common import SEEDS, create_run, save_config, save_csv, summarize, save_plot, plt
from pathlib import Path
import argparse
import csv
import json
import numpy as np
from src.pde_models import PeakInterfaceProblem
from src.adaptive_sampling import compare_sampling


def plot_only(run):
    rows=list(csv.DictReader((run/"raw/efficiency.csv").open(encoding="utf-8-sig")))
    fig,ax=plt.subplots(figsize=(7,4))
    for index,method in enumerate(["A","B","C","D","D_unused"]):
        values=np.array([float(r["total_seconds"]) for r in rows if r["method"]==method])
        ax.scatter(index+np.linspace(-.1,.1,len(values)),values,s=25)
        ax.plot(index,values.mean(),"k_",markersize=16)
    ax.set_xticks(range(5));ax.set_xticklabels(["A","B","C","D","D_unused"])
    ax.set(ylabel="Complete sampling and solve time (s)",title="Sequential cost: narrow peak, beta=(1000,1), N=128/side, scale4")
    ax.grid(alpha=.3);fig.text(.1,-.02,"Source: raw/efficiency.csv; rounds=6,1904 equations; all 5 seeds",fontsize=8)
    save_plot(run,fig,"sequential_efficiency")


def run_experiment(run_id=None):
    source=Path(__file__).resolve().parents[1]/"results/runs/exp06_peaks_20261013"
    source_rows=list(csv.DictReader((source/"raw/peaks.csv").open(encoding="utf-8-sig")))
    if len(source_rows)!=400:raise RuntimeError("先完成400次主比较，不能与本计时任务并发")
    saved=np.load(source/"raw/solution_coefficients.npz")
    run=create_run("exp08",run_id)
    save_config(run,{"experiment":"exp08_sequential_efficiency","methods":["A","B","C","D","D_unused"],"seeds":SEEDS,
                     "width":.06,"beta":[1000,1],"scale":4,"neurons_per_side":128,"rounds":6,"equation_budget":1904,
                     "scope":"single predetermined case; execute after exp06/exp07; exact same method/seed, coefficients compared"})
    rows=[];log=(run/"run.log").open("w",encoding="utf8")
    model=PeakInterfaceProblem(1000,1,"jumps",width=.06)
    # seed外层防止时间波动总集中于同一策略的一整段。
    for seed in SEEDS:
        for method in ["A","B","C","D","D_unused"]:
            solution,_,elapsed=compare_sampling(model,"D" if method=="D_unused" else method,seed,"equations",128,4.,6,
                                               indicator_scope="unused" if method=="D_unused" else "all")
            original=next(r for r in source_rows if float(r["width"])==.06 and int(r["beta_left"])==1000 and float(r["scale"])==4 and int(r["rounds"])==6 and int(r["seed"])==seed and r["method"]==method)
            c=np.concatenate(solution.coefficients);baseline=saved["case_"+original["case_index"]]
            difference=np.linalg.norm(c-baseline)/max(np.linalg.norm(baseline),1)
            if difference>1e-10:raise AssertionError("重复算法输出系数不一致")
            row={"method":method,"seed":seed,"status":"ok","total_seconds":elapsed,"main_case_index":original["case_index"],
                 "relative_l2":float(original["relative_l2"]),"relative_coefficient_reconstruction_difference":difference,
                 "n_points":solution.diagnostics["n_points"],"n_equations":solution.diagnostics["n_equations"]}
            rows.append(row);log.write(json.dumps(row)+"\n");log.flush();save_csv(run/"raw/efficiency.csv",rows)
    log.close();save_csv(run/"tables/efficiency_summary.csv",summarize(rows,["method"],["total_seconds","relative_l2"]))
    plot_only(run);print(run);print("sequential timing runs",len(rows),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--run-id");parser.add_argument("--plot-run")
    args=parser.parse_args();plot_only(Path(args.plot_run)) if args.plot_run else run_experiment(args.run_id)
