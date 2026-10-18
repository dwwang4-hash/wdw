# Bachelor_Thesis_RaNN

数学本科论文起步工程：已有局部随机网络方法的独立实现、配置点比较与稳定性研究。暂定题目《基于自适应采样的局部随机神经网络求解椭圆型界面问题的数值研究》。**现阶段不是完整论文，也没有自适应方法优越性结论。**

## 已实际完成

- 检查空工作区和Python3.12.14；项目独立`.venv`，未修改系统Python。
- 核实五篇核心文献书目（AG正式出版待核实），获取其中四篇作者预印本全文；11条文献矩阵、近期先行工作初查、可追溯来源。
- 研究计划、阶段验收、实验协议；Poisson与直线界面制造解推导。
- 五点差分、tanh随机特征/解析导数、SVD最小二乘、Poisson基础RaNN、五项单元测试。
- 四级差分网格、两个特征数×五种子真实运行；CSV、JSON、日志、统计及三组PNG/PDF图。

后续已完成双子域LRNN、零/非零跳跃、150次界面基线、180次A/B/C/D及指标消融、285次固定比例/参数扫描，13项测试通过。D当前未优于A/B，保留负面结果。

峰值阶段又完成400次多预算比较、90组右端扰动（15组谱）、25次串行效率复测；现有15项测试通过。[峰值结果](docs/peak_results.md)、[扰动结果](docs/stability_results.md)、[串行成本](docs/peak_efficiency_results.md)、[论断证据表](docs/claim_evidence_matrix.csv)、[当前质量报告](docs/quality_check_stage3.md)。窄峰存在精度不足，未声称所有算例通过高精度验收。

详情：[起步结果](docs/initial_results.md)、[界面结果](docs/interface_results.md)、[采样结果](docs/sampling_results.md)、[敏感性结果](docs/sensitivity_results.md)、[持续执行提示词](docs/autonomous_work_prompt.md)、[研究计划](docs/research_plan.md)、[文献阅读](docs/literature_review.md)、[矩阵](docs/literature_matrix.csv)、[数学推导](docs/mathematical_derivations.md)、[协议](docs/experiment_protocol.md)、[日志](docs/research_log.md)、[当前质量报告](docs/quality_check_stage2.md)。

## Windows / VS Code / Python3.12复现

在项目根目录的PowerShell执行，无需激活虚拟环境：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m experiments.exp01_poisson --rerun
.\.venv\Scripts\python.exe -m experiments.exp01_poisson --plot-only
```

首次无结果运行可省略`--rerun`。工程附带真实CSV，默认再次求解会拒绝覆盖；`--rerun`先将现有raw/tables/figures复制到唯一UTC时间戳的`results/archive/`后更新最新结果。不要先用shell重定向覆盖旧日志；重要实验另外使用独立run_id。`--plot-only`仅更新可再生图表，不改原始CSV。VS Code选择`.venv\Scripts\python.exe`为解释器。

Linux实测命令：

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m experiments.exp01_poisson --rerun
.venv/bin/python -m experiments.exp01_poisson --plot-only
.venv/bin/python references/build_catalog.py
```

三个直接依赖锁定在`requirements.txt`，本次全部依赖在`requirements-lock.txt`。CPU即可，不需PyTorch/GPU。当前实际执行环境为Linux，未在用户Windows实机运行；数值舍入和时间随BLAS/硬件可能变化。图用英文标注以避免Windows/Linux中文字体差异；文档与代码说明为中文。阅读PDF文本提取工具`pdftotext`只用于本轮文献阅读，运行数值实验不依赖它。

## 当前模块

`pde_models`：制造解；`baseline_fdm`：零边界Poisson五点差分；`random_features`：固定tanh及导数；`least_squares`：gelsd、岭增广与奇异值；`poisson_rann`：强形式Poisson组装；`metrics`：离散点误差；`exp01_poisson`：运行、统计及CSV重绘。统一公开种子11,23,37,51,71。

`src/local_rann.py`已实现双子域强形式LRNN及独立验证；`src/adaptive_sampling.py`已实现A/B/C/D与两个指标消融。exp02为界面，exp03含策略/消融/完整效率，exp04为比例/敏感性；未另建重复的exp05入口。`thesis/`目前仅有核实来源的`references.bib`，没有整篇草稿，未运行LaTeX编译。

新实验结果在`results/runs/exp02_interface_20261013`、`exp03_sampling_20261013`、`exp04_sensitivity_20261013`，各有config、raw、tables、figures、run.log。每次运行只创建新run_id，不覆盖这些结果。Linux执行例（Windows替换解释器路径）：

```bash
.venv/bin/python -m experiments.exp02_interface --run-id my_exp02
.venv/bin/python -m experiments.exp03_sampling --run-id my_exp03
.venv/bin/python -m experiments.exp04_sensitivity --run-id my_exp04
.venv/bin/python -m experiments.exp02_interface --plot-run results/runs/exp02_interface_20261013
.venv/bin/python -m experiments.exp03_sampling --plot-run results/runs/exp03_sampling_20261013
.venv/bin/python -m experiments.exp04_sensitivity --plot-run results/runs/exp04_sensitivity_20261013
.venv/bin/python -m experiments.build_stage_report
```

新参数预登记见docs/exp02_protocol、exp03_protocol、exp04_protocol；最后一个报告脚本按本轮命名run读取CSV，用于重建当前阶段报告。

峰值/扰动协议见docs/exp06_protocol。run目录为exp06_peaks_20261013、exp07_stability_20261013、exp08_efficiency_20261013。实验和重绘：

```bash
.venv/bin/python -m experiments.exp06_peaks --run-id my_exp06
.venv/bin/python -m experiments.exp07_stability --run-id my_exp07
.venv/bin/python -m experiments.exp06_peaks --plot-run results/runs/exp06_peaks_20261013
.venv/bin/python -m experiments.exp07_stability --plot-run results/runs/exp07_stability_20261013
.venv/bin/python -m experiments.exp08_efficiency --plot-run results/runs/exp08_efficiency_20261013
.venv/bin/python -m experiments.build_peak_report
```

exp08执行入口按固定的exp06主run取系数做重复一致性检查，须等exp06/07完成再启动；报告脚本也读取本轮固定命名目录。新run_id重跑后如需重建其报告，应显式调整数据路径，不覆盖旧run。主峰值前段与谱实验并发，严格成本讨论使用另行串行exp08。

## 结果位置与含义

`results/raw/poisson_fdm.csv`记录四级网格误差/阶/时间/离散残差；`poisson_fdm_grid.csv`保留n=63节点解用于重绘。`poisson_rann.csv`保留十次运行，`results/tables/poisson_rann_summary.csv`统计均值和样本标准差。`exp01_config.json`和`environment.json`记录参数/环境，`exp01_run.log`、`test_basics.log`保留真实输出。`results/figures/`含解与误差图、差分收敛图及RaNN五种子误差图，300dpi PNG和PDF。

FDM观测阶约2；128特征RaNN独立网格相对误差均值5.9866e−5，但加权系统条件数均值2.4773e9。不能将不同预算/评估点的FDM与RaNN时间作为公平效率对比，也不能从Poisson结果推断界面或自适应效果。

## 学术真实性与待确认

文献结果与本项目结果分别记录。无全文时不编写作者观点；预印本/正式版题名、年份、DOI区别保留。联合采样只是候选实验方案；既有残差自适应、局部细化和2026算子空间采样必须引用与比对。

实际毕业届次、期限、导师选题意见和官方模板未提供；后续暂用ctex中文LaTeX和GB/T7714，取得学校规范后再调整。FD近似复现与中文科研初稿已完成，下一优先任务是逐章审阅及文献缺口核查；不继续仅在旧模型上调参以追求D胜出。

## FD近似复现与论文初稿（最新）

已完成`src/fd_features.py`、花形界面`src/flower_interface.py`；170次复现/步长/初始化等运行，18项测试通过。预登记及初始化解释更正见`docs/exp09_protocol.md`，真实差异见[复现报告](docs/reproduction_results.md)。没有称严格复现或按原表调数据。

中文六章科研初稿已写入`thesis/`并实际编译，[PDF](thesis/draft.pdf)、[源文件](thesis/main.tex)、[论文运行说明](thesis/README.md)、[质量与待办](docs/thesis_quality_report.md)。最新修订版v2含10份CSV生成表、7幅图，另有符号表；新增配对统计、同配额对照和积分敏感度。学校字数/模板尚未确认。

```bash
.venv/bin/python -m experiments.exp09_reproduction --run-id my_exp09
.venv/bin/python -m experiments.exp09_reproduction --literal-only --run-id my_exp09_literal
.venv/bin/python -m experiments.exp09_reproduction --plot-run results/runs/exp09_literal_20261013
.venv/bin/python -m experiments.build_thesis_assets
```

当前优先任务转为初稿逐章审阅、文献缺口和学校格式；前文各阶段说明保留为历史进展，最新状态以此节及科研日志为准。

## 初稿修订版v2

[修订说明](docs/thesis_revision_v2.md)。v1源文件和PDF保存在`thesis/versions/v1_20261013/`。本轮未新增或改写数值实验结果，修正自适应抽样理论的适用条件，补充有限维误差分解、增行条件数反例及统计证据。

## 当前版本：面向大连理工数学本科论文的v3（2026-10-16）

[最新PDF](thesis/draft_v3.pdf)、[规范落实表](docs/dlut_requirements_review.md)、[修订说明](docs/thesis_revision_v3.md)、[质量报告](docs/thesis_quality_report.md)。实际52页；六章叙述保守统计20388汉字，中文摘要536汉字、英文摘要462词；13份CSV生成表、2份正文说明表、8图、11引用。本轮18项测试通过，18份封存原始CSV哈希通过。没有新PDE求解或更改旧实验。

现行官方模板附件有验证码，尚未取得；2010年数学学院通知仅为历史准备参考，不当成本届规则。学校格式、本人信息、导师审核和流程材料待落实。AI辅助范围见[材料清单](docs/submission_materials_checklist.md)，不能据此虚构全部工作由学生独立完成的声明。

完整证据重建顺序与编译说明以[thesis/README.md](thesis/README.md)为准。新增入口：`python -m experiments.build_thesis_v3_evidence`、`python -m experiments.build_model_illustration`、`python -m experiments.audit_thesis_v3`。旧段落保留为阶段历史，最新状态以此节为准。
