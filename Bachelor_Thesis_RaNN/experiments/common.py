"""独立run目录、CSV统计和绘图环境；不覆盖其他实验结果。"""
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT/".cache"
(CACHE/"matplotlib").mkdir(parents=True, exist_ok=True)
os.environ["MPLCONFIGDIR"] = str(CACHE/"matplotlib")
os.environ["XDG_CACHE_HOME"] = str(CACHE)
for key in ["OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"]:
    os.environ[key] = "1"
import csv
import json
import re
import platform
from datetime import datetime, timezone
import numpy as np
import scipy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEEDS = [11, 23, 37, 51, 71]


def create_run(prefix, run_id=None):
    run_id = run_id or prefix+"_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("run_id仅允许字母数字下划线和连字符")
    run = ROOT/"results/runs"/run_id
    run.mkdir(parents=True, exist_ok=False)
    for name in ["raw", "tables", "figures"]:
        (run/name).mkdir()
    return run


def save_config(run, config):
    config = {**config,"python":platform.python_version(),"platform":platform.platform(),"numpy":np.__version__,
              "scipy":scipy.__version__,"matplotlib":matplotlib.__version__,"blas_threads":1}
    (run/"config.json").write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding="utf8")


def save_csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)


def summarize(rows, groups, metrics):
    result=[]
    keys=sorted(set(tuple(r[k] for k in groups) for r in rows),key=str)
    for key in keys:
        all_block=[r for r in rows if tuple(r[k] for k in groups)==key]
        block=[r for r in all_block if r.get("status")=="ok"]
        for metric in metrics:
            values=np.asarray([float(r[metric]) for r in block])
            result.append({**dict(zip(groups,key)),"metric":metric,"successful":len(block),"failed":len(all_block)-len(block),
                           "mean":float(values.mean()) if len(values) else float("nan"),
                           "sample_std":float(values.std(ddof=1)) if len(values)>1 else float("nan"),
                           "min":float(values.min()) if len(values) else float("nan"),"max":float(values.max()) if len(values) else float("nan")})
    return result


def save_plot(run, fig, name):
    for ext in ["png", "pdf"]:
        fig.savefig(run/"figures"/f"{name}.{ext}",dpi=300,bbox_inches="tight")
    plt.close(fig)
