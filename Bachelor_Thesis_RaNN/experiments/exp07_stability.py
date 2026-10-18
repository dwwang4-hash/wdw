"""固定矩阵与固定SVD保留子空间的右端扰动实验。"""
from .common import SEEDS, create_run, save_config, save_csv, summarize, save_plot, plt
from pathlib import Path
from time import perf_counter
import argparse
import csv
import json
import numpy as np
from scipy.linalg import svd
from src.pde_models import StraightInterfaceProblem
from src.random_features import LocalTanhFeatures
from src.adaptive_sampling import sampling_collocation
from src.local_rann import assemble,outer_boundary,interior_points


def plot_only(run):
    data=list(csv.DictReader((run/"raw/stability.csv").open(encoding="utf-8-sig")))
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for direction,marker in [("worst_retained","o"),("random","s")]:
        block=[r for r in data if r["direction"]==direction]
        axes[0].scatter([float(r["theoretical_bound"]) for r in block],[float(r["observed_amplification"]) for r in block],marker=marker,s=20,label=direction)
        axes[1].scatter([float(r["coefficient_relative_change"]) for r in block],[float(r["solution_relative_change"]) for r in block],marker=marker,s=20,label=direction)
    limits=[min(float(r["theoretical_bound"]) for r in data),max(float(r["theoretical_bound"]) for r in data)]
    axes[0].loglog(limits,limits,"k--",label="1/sigma retained")
    axes[0].set(xscale="log",yscale="log",xlabel="Bound 1/min retained singular value",ylabel="Observed ||delta c||/||delta rhs||")
    axes[1].set(xscale="log",yscale="log",xlabel="Relative coefficient change",ylabel="Relative predicted-function change")
    for ax in axes:ax.grid(alpha=.3,which="both");ax.legend(fontsize=8)
    fig.suptitle("Fixed matrix TSVD; rhs perturbation=1e-8; N=64,128,256/side; 5 seeds")
    fig.text(.1,-.02,"Source: raw/stability.csv; rcond=1e-14,1e-12,1e-10; no matrix perturbation",fontsize=8)
    save_plot(run,fig,"rhs_perturbation")


def run_experiment(run_id=None):
    run=create_run("exp07",run_id)
    save_config(run,{"experiment":"exp07_stability","seeds":SEEDS,"neurons_per_side":[64,128,256],"rcond":[1e-14,1e-12,1e-10],
                     "relative_rhs_perturbation":1e-8,"directions":["worst_retained","random"],"model":"jumps;beta=(1,1000)",
                     "scale":2,"counts":[368,368,128],"scaling":"balanced","solver":"explicit economy SVD gesdd; fixed retained subspace per threshold",
                     "validation":"83x83 midpoint/side; coefficient-induced function changes","scope":"rhs perturbations only; matrix fixed"})
    model=StraightInterfaceProblem(1,1000,"jumps");rows=[];spectra=[];solutions={}
    log=(run/"run.log").open("w",encoding="utf8")
    for count in [64,128,256]:
        for seed in SEEDS:
            start=perf_counter();features=[LocalTanhFeatures(count,seed,i,2) for i in [0,1]]
            interior,interface=sampling_collocation(seed,368,128)
            matrix,rhs=assemble(model,features,interior,interface,outer_boundary(),"balanced")
            u,s,vt=svd(matrix,full_matrices=False,lapack_driver="gesdd")
            elapsed=perf_counter()-start
            for index,value in enumerate(s):spectra.append({"count":count,"seed":seed,"index":index,"singular_value":value})
            points=[interior_points(83**2,i,uniform=True) for i in [0,1]]
            phi=[features[i].evaluate(points[i])[0] for i in [0,1]]
            exact=np.concatenate([model.data(points[i],i)[0] for i in [0,1]])
            def predict(c):return np.concatenate((phi[0]@c[:count],phi[1]@c[count:]))
            for cutoff in [1e-14,1e-12,1e-10]:
                keep=s>cutoff*s[0];ur=u[:,keep];sr=s[keep];vr=vt[keep]
                def solve(d):return vr.T@((ur.T@d)/sr)
                c=solve(rhs);prediction=predict(c);rhs_norm=np.linalg.norm(rhs)
                rng=np.random.default_rng(np.random.SeedSequence([seed,700]));random=rng.normal(size=len(rhs));random/=np.linalg.norm(random)
                for direction,vector in [("worst_retained",ur[:,-1]),("random",random)]:
                    delta=1e-8*rhs_norm*vector;perturbed=solve(rhs+delta);dc=perturbed-c
                    gain=np.linalg.norm(dc)/np.linalg.norm(delta);bound=1/sr[-1]
                    # 被截断方向与保留空间正交；仅在存在截断时另报告，不计入90主观察。
                    rejected_gain=float("nan")
                    if np.any(~keep):
                        rejected=1e-8*rhs_norm*u[:,np.flatnonzero(~keep)[0]]
                        rejected_gain=np.linalg.norm(solve(rejected))/np.linalg.norm(rejected)
                    row={"case_index":len(rows),"count":count,"seed":seed,"rcond":cutoff,"direction":direction,"status":"ok",
                         "rank":int(np.sum(keep)),"min_retained_singular":sr[-1],"condition_raw":s[0]/s[-1],"condition_retained":s[0]/sr[-1],
                         "rhs_relative_perturbation":np.linalg.norm(delta)/rhs_norm,"observed_amplification":gain,"theoretical_bound":bound,
                         "gain_over_bound":gain/bound,"coefficient_relative_change":np.linalg.norm(dc)/np.linalg.norm(c),
                         "solution_relative_change":np.linalg.norm(predict(dc))/np.linalg.norm(prediction),
                         "base_relative_l2":np.linalg.norm(prediction-exact)/np.linalg.norm(exact),
                         "perturbed_relative_l2":np.linalg.norm(predict(perturbed)-exact)/np.linalg.norm(exact),
                         "rejected_direction_gain":rejected_gain,"assembly_svd_seconds":elapsed}
                    rows.append(row);solutions[f"base_{len(rows)-1}"]=c;solutions[f"perturbed_{len(rows)-1}"]=perturbed
                    log.write(json.dumps(row)+"\n");log.flush();save_csv(run/"raw/stability.csv",rows)
    log.close();save_csv(run/"raw/spectra.csv",spectra);np.savez_compressed(run/"raw/coefficients.npz",**solutions)
    save_csv(run/"tables/stability_summary.csv",summarize(rows,["count","rcond","direction"],["observed_amplification","gain_over_bound","coefficient_relative_change","solution_relative_change","base_relative_l2","perturbed_relative_l2","rank"]))
    plot_only(run);print(run);print("perturbation observations",len(rows),"spectra",15,flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--run-id");parser.add_argument("--plot-run")
    args=parser.parse_args();plot_only(Path(args.plot_run)) if args.plot_run else run_experiment(args.run_id)
