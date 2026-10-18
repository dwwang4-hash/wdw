"""从真实CSV重建阶段报告，不重新求解、不挑选最好运行。"""
from .common import ROOT
import csv
import numpy as np


def load(run,filename):
    return list(csv.DictReader((ROOT/"results/runs"/run/"raw"/filename).open(encoding="utf-8-sig")))


def mean(rows,metric):return np.mean([float(r[metric]) for r in rows])


def main():
    rows=load("exp03_sampling_20261013","sampling.csv")
    lines=["# 首轮采样比较：真实负面结果","","来源：`results/runs/exp03_sampling_20261013/`。180次算法运行，五固定种子、三个β组合、两种预算、A/B/C/D及两项消融。所有运行状态正常；状态ok表示运行完成且指标有限，不表示精度优越或达到特定通量目标。","",
           "## 等物理点预算","","每次总内部/界面点864，加外边界240=1104；D方程数可变。下表均值覆盖全部五种子，样本标准差在summary.csv。","",
           "| β左,β右 | 策略 | 相对L2均值 | 物理通量RMS均值 | 完整时间均值/秒 | 界面点均值 |","|---|---|---|---|---|---|"]
    for beta in [(1,1),(1000,1),(1,1000)]:
        for method in ["A","B","C","D","D_minus_pde","D_minus_interface"]:
            b=[r for r in rows if r["budget_mode"]=="points" and (int(r["beta_left"]),int(r["beta_right"]))==beta and r["method"]==method]
            lines.append(f"| {beta} | {method} | {mean(b,'relative_l2'):.6e} | {mean(b,'interface_flux_rms'):.6e} | {mean(b,'total_seconds'):.6f} | {mean(b,'n_interface'):.1f} |")
    lines += ["","## 配对比较（描述性，非独立大样本推断）","","同seed内比较，15个配对是3模型×5种子，模型间相关，不能当作15个独立随机种子做显著性结论。误差比例D/基线<1才表示D较小。","",
              "| 预算 | 基线 | D误差更小的配对数 | 误差比例中位数 | 时间比例中位数 |","|---|---|---|---|---|"]
    for mode in ["points","equations"]:
        for baseline in ["A","B","C"]:
            ratios=[];times=[]
            for beta in [(1,1),(1000,1),(1,1000)]:
                for seed in [11,23,37,51,71]:
                    b={r["method"]:r for r in rows if r["budget_mode"]==mode and (int(r["beta_left"]),int(r["beta_right"]))==beta and int(r["seed"])==seed}
                    ratios.append(float(b["D"]["relative_l2"])/float(b[baseline]["relative_l2"]))
                    times.append(float(b["D"]["total_seconds"])/float(b[baseline]["total_seconds"]))
            lines.append(f"| {mode} | {baseline} | {sum(x<1 for x in ratios)}/15 | {np.median(ratios):.4f} | {np.median(times):.3f} |")
    lines += ["","equations模式固定最终1232标量行（含240边界行），D物理点数可变；结论同样未支持D对A/B的解误差优势。精度收益不能抵偿不存在的收益；D需要候选评估和4次求解，较静态方法明显更贵。","",
              "## 已观察事实与猜想分开","",
              "事实：D给界面约63—69点（均值），少于A/B/C的128；去PDE指标消融给界面512点（点预算）或320点（行预算），其平均解误差较好。D在部分配对可比C更好、但并无稳定胜出。高β下64特征的物理通量RMS约0.1，可能大于指定跳跃幅值0.05；小相对解误差不能替代物理通量满足度。","",
              "猜想：简单RMS联合指标偏向内部PDE，导致界面资源不足；当前平滑问题表达力不足或目标偏重高残差，使增量内部采样提高PDE局部拟合而损害解误差。上述是待验证解释，不是已证明因果。候选池中被选入训练的点仍用于下一轮池RMS，可能产生候选指标乐观偏差，独立测试集从未参与。","",
              "跟进：exp04固定比例扫描隔离界面点数效果，单因素特征宽度/scale/界面权重/ridge/点数分辨表达力与稳定性。保留exp03原数据，不把后续选择的最好参数改写为主比较预设。","",
              "局限：只做一个平滑直线界面族和一个主预算，五种子；尚无圆界面/尖峰/多预算独立验证；没有逆密度权重，采样改变经验目标；没有证明新颖性与统一收敛。论文可定位数值比较及适用条件分析，无需强行将D包装为新算法。"]
    (ROOT/"docs/sampling_results.md").write_text("\n".join(lines)+"\n",encoding="utf8")
    rows=load("exp04_sensitivity_20261013","sensitivity.csv")
    lines=["# 固定界面比例与参数敏感性：后续真实结果","","来源：`results/runs/exp04_sensitivity_20261013/`。285次，五固定种子；属于看到exp03后登记的探索性试验，不能与主比较混作验证性推断。","",
           "## 固定比例扫描","","以下全部为固定随机点、每侧64特征，其他参数一致。全扫描均保留，不能据测试集选好比例后宣称事先最佳。","",
           "| 预算 | β左,β右 | 界面点 | 每侧内部点 | 相对L2均值 | 物理通量RMS均值 |","|---|---|---|---|---|---|"]
    for mode in ["points","equations"]:
        for beta in [(1,1),(1000,1),(1,1000)]:
            b=[r for r in rows if r["study"]=="proportion" and r["budget_mode"]==mode and (int(r["beta_left"]),int(r["beta_right"]))==beta]
            for ng in sorted(set(int(r["n_interface"]) for r in b)):
                c=[r for r in b if int(r["n_interface"])==ng]
                lines.append(f"| {mode} | {beta} | {ng} | {c[0]['n_left']} | {mean(c,'relative_l2'):.6e} | {mean(c,'interface_flux_rms'):.6e} |")
    lines += ["","## 单因素扫描","","β=(1,1000)完整参数均值；全部三种β的宽度结果及标准差见summary.csv。条件数针对原始加权数据矩阵，岭求解的增广秩另报，不混称稳定数据满秩。","",
              "| 参数 | 值 | 相对L2均值 | 物理通量RMS均值 | 数据秩范围 | 条件数均值 |","|---|---|---|---|---|---|"]
    for parameter in ["count","scale","interface_weight","ridge","collocation_budget"]:
        b=[r for r in rows if r["study"]=="sensitivity" and r["parameter"]==parameter and int(r["beta_left"])==1 and int(r["beta_right"])==1000]
        for value in sorted(set(float(r["parameter_value"]) for r in b)):
            c=[r for r in b if float(r["parameter_value"])==value]
            rank=[int(r["data_rank"]) for r in c]
            lines.append(f"| {parameter} | {value:g} | {mean(c,'relative_l2'):.6e} | {mean(c,'interface_flux_rms'):.6e} | {min(rank)}—{max(rank)} | {mean(c,'condition_raw'):.6e} |")
    sampling=load("exp03_sampling_20261013","sampling.csv")
    lines += ["","## 固定比例与去PDE消融的直接对照","","相同最终组点数，下表固定随机与自适应去PDE指标的五种子均值。属于探索性比较，未据此作因果或显著性声明。","",
              "| 预算 | β左,β右 | 固定随机相对L2 | 去PDE消融相对L2 | 固定随机完整秒 | 消融完整秒 |","|---|---|---|---|---|---|"]
    for mode,ng in [("points",512),("equations",320)]:
        for beta in [(1,1),(1000,1),(1,1000)]:
            b=[r for r in rows if r["study"]=="proportion" and r["budget_mode"]==mode and int(r["n_interface"])==ng and (int(r["beta_left"]),int(r["beta_right"]))==beta]
            d=[r for r in sampling if r["method"]=="D_minus_pde" and r["budget_mode"]==mode and (int(r["beta_left"]),int(r["beta_right"]))==beta]
            lines.append(f"| {mode} | {beta} | {mean(b,'relative_l2'):.6e} | {mean(d,'relative_l2'):.6e} | {mean(b,'total_seconds'):.6f} | {mean(d,'total_seconds'):.6f} |")
    lines += ["","六组均值中固定随机的解误差均较小且耗时较少。这未支持自适应选点的额外收益；消融较好不能简单归功于界面残差指标，更大界面预算是必须考虑的混杂因素。注意通量指标可能有不同排序，应回查全表。","",
              "增加特征32→256时本平滑模型解误差显著降低，但条件数升至约1e17且有效秩小于512；更低scale可能提高平滑解近似同时加重病态。强ridge会带来明显偏差。点数216→1728时解误差不单调，通量指标却可改善。这些只是已测试参数与模型上的数值观察，不是一般单调性定理。","",
              "以上数值来自程序，没有删除极端参数或秩下降结果。后续判断需要结合独立困难算例；不得把探索性扫描中的最优值当作普适推荐。没有完成参数交互、扰动稳定性实测和原文FD复现。"]
    (ROOT/"docs/sensitivity_results.md").write_text("\n".join(lines)+"\n",encoding="utf8")
    print("Rebuilt docs/sampling_results.md and docs/sensitivity_results.md")


if __name__=="__main__":main()
