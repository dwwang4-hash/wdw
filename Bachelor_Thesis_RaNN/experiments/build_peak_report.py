"""从本阶段已完成CSV构建结果与证据表，不重新求解。"""
from .common import ROOT
import csv
import numpy as np


def load(run,name):return list(csv.DictReader((ROOT/"results/runs"/run/"raw"/name).open(encoding="utf-8-sig")))


def mean(rows,key):return np.mean([float(r[key]) for r in rows])


def main():
    all_rows=load("exp06_peaks_20261013","peaks.csv")
    if len(all_rows)!=400:raise RuntimeError("主比较尚未完成")
    rows=[r for r in all_rows if r["status"]=="ok"]
    lines=["# 独立峰值阶段结果","","来源：`results/runs/exp06_peaks_20261013/`。400次完整算法运行，五固定种子，参数/模型/预算在运行前登记。失败数："+str(len(all_rows)-len(rows))+"。所有预登记设置都保留，不按胜负删算例。","",
           "## 全参数比较","","N=128/侧，均值与样本标准差来自五次运行；以下保留两峰宽、两系数、两scale、两标量行预算的所有组。","",
           "| 峰宽 | β左 | scale | 标量行数 | 方法 | 相对L2均值 | 样本标准差 | 物理通量RMS均值 |","|---|---|---|---|---|---|---|---|"]
    for width in [.12,.06]:
        for beta in [1,1000]:
            for scale in [2.,4.]:
                for rounds in [3,6]:
                    for method in ["A","B","C","D","D_unused"]:
                        b=[r for r in rows if float(r["width"])==width and int(r["beta_left"])==beta and float(r["scale"])==scale and int(r["rounds"])==rounds and r["method"]==method]
                        values=np.array([float(r["relative_l2"]) for r in b])
                        lines.append(f"| {width:g} | {beta} | {scale:g} | {560+224*rounds} | {method} | {values.mean():.6e} | {values.std(ddof=1):.6e} | {mean(b,'interface_flux_rms'):.6e} |")
    lines += ["","## 描述性配对统计","","80个配对来自16设置×5种子，设置之间相关，不能当作80个独立随机种子作显著性推断。以下比例为相对L2的逐seed比值；小于1表示目标策略误差较低。","",
              "| 策略 | 基线 | 较低误差配对数 | 总配对 | 比例中位数 |","|---|---|---|---|---|"]
    for target in ["D","D_unused"]:
        for baseline in ["A","B","C"]:
            ratios=[]
            for width in [.12,.06]:
                for beta in [1,1000]:
                    for scale in [2.,4.]:
                        for rounds in [3,6]:
                            for seed in [11,23,37,51,71]:
                                b={r["method"]:r for r in rows if float(r["width"])==width and int(r["beta_left"])==beta and float(r["scale"])==scale and int(r["rounds"])==rounds and int(r["seed"])==seed}
                                if target in b and baseline in b:ratios.append(float(b[target]["relative_l2"])/float(b[baseline]["relative_l2"]))
            lines.append(f"| {target} | {baseline} | {sum(r<1 for r in ratios)} | {len(ratios)} | {np.median(ratios):.4f} |")
    grid_changes=[float(r["grid_error_relative_change"]) for r in rows]
    lines += ["","## 测试网格与成本范围","",
              f"独立81/161中点网格相对L2变化：最大{max(grid_changes):.6e}，中位数{np.median(grid_changes):.6e}。两网格接近是数值积分敏感性检查，不是连续L2精确积分证明。界面用独立521点；两侧相同峰引起β差异通量跳跃，已单独推导和测试。","",
              "主运行初期与谱任务并发，因此该表total_seconds保留但不作严格效率比较。单独串行exp08用于固定代表场景，无本项目其他计算任务并发。","",
              "D_unused只改变预算指标池范围，不能排除所有选择偏差，也不等于独立监测集。结果只覆盖这四个直线界面模型和两个scale/预算，不能推断一般界面PDE的优越性；固定特征可能不足以表达窄峰。所有物理通量误差必须与gu/gq及解误差一并评价。"]
    (ROOT/"docs/peak_results.md").write_text("\n".join(lines)+"\n",encoding="utf8")
    rows=load("exp07_stability_20261013","stability.csv")
    lines=["# 固定矩阵右端扰动：真实结果","","来源：`results/runs/exp07_stability_20261013/`。15组矩阵谱、90组扰动观察；显式经济SVD、固定阈值下保留子空间，不是矩阵扰动或一般PDE收敛实验。","",
           "| 每侧特征 | rcond | 方向 | 放大/理论上界均值 | 系数相对变化均值 | 函数相对变化均值 | 数据秩范围 |","|---|---|---|---|---|---|---|"]
    for count in [64,128,256]:
        for cutoff in [1e-14,1e-12,1e-10]:
            for direction in ["worst_retained","random"]:
                b=[r for r in rows if int(r["count"])==count and float(r["rcond"])==cutoff and r["direction"]==direction];ranks=[int(r["rank"]) for r in b]
                lines.append(f"| {count} | {cutoff:g} | {direction} | {mean(b,'gain_over_bound'):.6e} | {mean(b,'coefficient_relative_change'):.6e} | {mean(b,'solution_relative_change'):.6e} | {min(ranks)}—{max(ranks)} |")
    worst=[r for r in rows if r["direction"]=="worst_retained"]
    lines += ["",f"最小保留左奇异方向的放大/上界范围为{min(float(r['gain_over_bound']) for r in worst):.10f}—{max(float(r['gain_over_bound']) for r in worst):.10f}，在浮点误差内与1/σ_min_retained一致。相对右端扰动固定1e−8；最大系数相对变化{max(float(r['coefficient_relative_change']) for r in rows):.6e}，而本组最大函数相对变化{max(float(r['solution_relative_change']) for r in rows):.6e}。","",
              "这体现随机特征冗余可使系数敏感而预测函数变化较小。函数变化约1e−8处可能接近大系数抵消的浮点求值误差地板，未进行高精度算术复核，不能精确解释其末位或宣称严格函数稳定常数。不能据此说病态无害：本实验方向/矩阵/预测点固定，未覆盖边界数据错误、矩阵舍入、阈值跨秩或分布变化。条件数和解误差不应相互替代。被截断方向理论响应为零，浮点残余投影可能非零，原数据保留；无截断时rejected_direction_gain为NaN（不适用）。"]
    (ROOT/"docs/stability_results.md").write_text("\n".join(lines)+"\n",encoding="utf8")
    rows=load("exp08_efficiency_20261013","efficiency.csv")
    lines=["# 独立串行成本检查","","固定代表：w=.06,β=(1000,1),N=128/侧,scale4,六轮,1904标量方程；五公开种子；25次算法串行运行。全部系数与主峰值实验对应case检查一致。精度列来自主run对应case，非重新选择最好结果。","",
           "| 方法 | 完整时间均值/秒 | 样本标准差 | 相对L2均值 |","|---|---|---|---|"]
    for method in ["A","B","C","D","D_unused"]:
        b=[r for r in rows if r["method"]==method];times=np.array([float(r["total_seconds"]) for r in b])
        lines.append(f"| {method} | {times.mean():.6f} | {times.std(ddof=1):.6f} | {mean(b,'relative_l2'):.6e} |")
    lines += ["","完整时间含点生成、候选评估和所有求解/诊断，排除测试/绘图。只是一种固定场景的CPU测量，不外推到其他硬件/模型，也不能把性能比值归因于采样公式单一因素。"]
    (ROOT/"docs/peak_efficiency_results.md").write_text("\n".join(lines)+"\n",encoding="utf8")
    evidence=[{"claim":"平滑模型D未胜A/B","source":"exp03_sampling_20261013/tables/paired_differences.csv","scope":"平滑直线模型和预设参数"},
              {"claim":"固定更多界面点可解释消融较好","source":"exp04_sensitivity_20261013/raw/sensitivity.csv + exp03_sampling_20261013/raw/sampling.csv","scope":"后验探索性对照，非因果证明"},
              {"claim":"峰值方法比较","source":"exp06_peaks_20261013/raw/peaks.csv","scope":"两峰宽/两β/两scale/两标量行预算；逐组判断"},
              {"claim":"固定TSVD右端放大界","source":"docs/mathematical_derivations.md §7 + exp07_stability_20261013/raw/stability.csv","scope":"固定矩阵和保留子空间；现成线性代数结论"},
              {"claim":"固定峰值场景完整成本","source":"exp08_efficiency_20261013/raw/efficiency.csv","scope":"25次串行CPU测量；未证明跨模型优越性"}]
    from .common import save_csv
    save_csv(ROOT/"docs/claim_evidence_matrix.csv",evidence)
    print("Generated peak/stability/efficiency reports and claim-evidence matrix")


if __name__=="__main__":main()
