"""运行/重绘首个制造解实验，原始数据和图表均保存到固定目录。"""
import os
for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_name] = "1"
import argparse
import csv
import json
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
# 将图形缓存放在项目内，避免云环境只读用户目录及跨平台字体缓存警告。
_cache_root = Path(__file__).resolve().parents[1] / ".cache"
(_cache_root / "matplotlib").mkdir(parents=True, exist_ok=True)
os.environ["MPLCONFIGDIR"] = str(_cache_root / "matplotlib")
os.environ["XDG_CACHE_HOME"] = str(_cache_root)
import numpy as np
import scipy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from src.baseline_fdm import solve_poisson
from src.pde_models import poisson_exact, poisson_forcing
from src.poisson_rann import solve_poisson_rann, boundary_points
from src.metrics import errors, rms

ROOT = Path(__file__).resolve().parents[1]
SEEDS = [11, 23, 37, 51, 71]


def save_csv(name, rows):
    path = ROOT / "results/raw" / name
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def save_figure(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(ROOT / f"results/figures/{name}.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)


def redraw():
    data = np.genfromtxt(ROOT / "results/raw/poisson_fdm.csv", delimiter=",", names=True)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.loglog(data["h"], data["relative_l2"], "o-", label="FDM relative discrete L2")
    ax.loglog(data["h"], data["h"]**2 * data["relative_l2"][0]/data["h"][0]**2, "--", label="O(h^2)")
    ax.set(xlabel="h = 1/(n+1)", ylabel="Relative discrete L2 error", title="Poisson sine solution; n=15,31,63,127")
    ax.legend(); ax.grid(True, which="both", alpha=.3)
    fig.text(.1, -.02, "Source: results/raw/poisson_fdm.csv", fontsize=8)
    save_figure(fig, "poisson_fdm_convergence")
    grid = np.genfromtxt(ROOT / "results/raw/poisson_fdm_grid.csv", delimiter=",", names=True)
    n = int(round(np.sqrt(len(grid))))
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))
    for ax, field, title in zip(axes, ["exact", "numerical", "abs_error"], ["Exact", "Five-point FDM", "Absolute error"]):
        mesh = ax.pcolormesh(grid["x"].reshape(n,n), grid["y"].reshape(n,n), grid[field].reshape(n,n), shading="auto")
        fig.colorbar(mesh, ax=ax); ax.set(title=title, xlabel="x", ylabel="y", aspect="equal")
    fig.suptitle("-Laplacian u = 2*pi^2*sin(pi*x)*sin(pi*y); zero boundary; n=63")
    fig.text(.1, -.02, "Source: results/raw/poisson_fdm_grid.csv", fontsize=8)
    save_figure(fig, "poisson_fdm_solution")
    rpath = ROOT / "results/raw/poisson_rann.csv"
    if rpath.exists():
        rdata = np.genfromtxt(rpath, delimiter=",", names=True)
        fig, ax = plt.subplots(figsize=(6,4))
        for count in [64,128]:
            block = rdata[rdata["neurons"]==count]
            ax.scatter(np.full(len(block),count), block["relative_l2"], label=f"N={count}, all 5 seeds")
        ax.set(yscale="log", xlabel="Random features N", ylabel="Independent-grid relative L2", title="tanh; scale=4; 1024 interior; boundary weight=10")
        ax.legend(); ax.grid(alpha=.3)
        fig.text(.1,-.02,"Source: results/raw/poisson_rann.csv; seeds=11,23,37,51,71",fontsize=8)
        save_figure(fig,"poisson_rann_errors")


def run(rerun=False):
    if (ROOT/"results/raw/poisson_fdm.csv").exists():
        if not rerun:
            raise FileExistsError("已有exp01结果。仅重绘用 --plot-only；重跑并自动归档旧结果用 --rerun。")
        archive = ROOT/"results/archive"/datetime.now(timezone.utc).strftime("exp01_%Y%m%dT%H%M%S_%fZ")
        for directory in ["raw", "tables", "figures"]:
            shutil.copytree(ROOT/"results"/directory, archive/directory)
        print(f"已归档旧结果：{archive}", flush=True)
    for directory in ["results/raw", "results/tables", "results/figures"]:
        (ROOT/directory).mkdir(parents=True, exist_ok=True)
    config = {"python":sys.version,"platform":platform.platform(),"numpy":np.__version__,"scipy":scipy.__version__,
              "matplotlib":matplotlib.__version__,"seeds":SEEDS,"fdm_n":[15,31,63,127],
              "rann_neurons":[64,128],"interior_points":1024,"boundary_points":320,"boundary_weight":10,
              "scale":4,"rcond":1e-12,"validation":"81x81 interior midpoint grid; separate 324 boundary midpoints",
              "timing":"assembly and solve incl SVD diagnostics; excludes validation and plotting; BLAS threads=1"}
    (ROOT/"results/raw/exp01_config.json").write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding="utf8")
    rows=[]
    for n in config["fdm_n"]:
        points, numerical, h, elapsed, residual = solve_poisson(n)
        exact=poisson_exact(points)
        row={"n":n,"unknowns":n*n,"h":h,**errors(numerical,exact),"solve_seconds":elapsed,"discrete_relative_residual":residual}
        row["observed_order"] = np.log(rows[-1]["relative_l2"]/row["relative_l2"])/np.log(rows[-1]["h"]/h) if rows else float("nan")
        rows.append(row); print("FDM", row, flush=True)
        if n==63:
            save_csv("poisson_fdm_grid.csv",[{"x":p[0],"y":p[1],"exact":e,"numerical":u,"abs_error":abs(u-e)} for p,e,u in zip(points,exact,numerical)])
    save_csv("poisson_fdm.csv",rows)
    if not all(1.9 < row["observed_order"] < 2.1 for row in rows[1:]):
        raise RuntimeError("差分法二阶收敛验收失败，停止后续实验")
    axis=(np.arange(81)+.5)/81
    xx,yy=np.meshgrid(axis,axis)
    validation=np.column_stack((xx.ravel(),yy.ravel()))
    exact=poisson_exact(validation)
    boundary=boundary_points(81)
    rrows=[]
    for count in config["rann_neurons"]:
        for seed in SEEDS:
            features,coeff,info=solve_poisson_rann(count,seed)
            phi,_,lap=features.evaluate(validation)
            bphi,_,_=features.evaluate(boundary)
            row={"neurons":count,"seed":seed,**errors(phi@coeff,exact),"validation_pde_rms":rms(-lap@coeff-poisson_forcing(validation)),
                 "validation_boundary_rms":rms(bphi@coeff),"coeff_norm":float(np.linalg.norm(coeff)),**info}
            rrows.append(row); print("RaNN", row,flush=True)
    save_csv("poisson_rann.csv",rrows)
    summary=[]
    for count in config["rann_neurons"]:
        block=[r for r in rrows if r["neurons"]==count]
        for metric in ["relative_l2","max_abs","validation_pde_rms","validation_boundary_rms","solve_seconds","condition_raw","data_rank"]:
            vals=np.array([r[metric] for r in block])
            summary.append({"neurons":count,"metric":metric,"mean":vals.mean(),"sample_std":vals.std(ddof=1),"min":vals.min(),"max":vals.max(),"seeds":len(vals)})
    with (ROOT/"results/tables/poisson_rann_summary.csv").open("w",encoding="utf8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    redraw()


if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--plot-only",action="store_true")
    parser.add_argument("--rerun",action="store_true",help="重跑前自动归档已有实验数据和图表")
    args=parser.parse_args()
    redraw() if args.plot_only else run(args.rerun)
