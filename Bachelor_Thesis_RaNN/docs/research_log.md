# 科研日志

## 2026-10-13：环境与工程

完成：检查`/workspace`、搜索已有py/pdf/tex/README及AGENTS；未发现已有科研成果和适用AGENTS文件。Python3.12.14，系统NumPy/SciPy/Matplotlib可用，但建立独立`.venv`后使用锁定版本。实际Linux云环境，Windows未测。

执行：`pwd`、`rg --files ...`、`find /workspace -name AGENTS.md -print`、`python --version`、`python -m venv /workspace/Bachelor_Thesis_RaNN/.venv`、`.venv/bin/python -m pip install numpy==2.2.6 scipy==1.15.3 matplotlib==3.10.3`、`pip freeze`、`pip check`。检查cloud-environment运行技能及网络策略，不查看秘密/凭据值。未做系统安装或删除既有文件。

错误：初次网络请求sandbox报Operation not permitted；使用工具支持的本命令网络权限后成功。pip缓存目录不可写警告，自动禁用缓存，安装成功；未修改系统目录。

产物：requirements、requirements-lock、模块化目录、环境JSON。下一步：模型和基线。

## 2026-10-13：文献核实与选题

完成：urllib实际访问arXiv页面/PDF、Crossref检索与DOI端点；下载四篇核心PDF并以`pdftotext -layout`提取。另保存近期文献与RAD/RAR-D先行工作；11条文献矩阵及BibTeX。核心年份更正：DG2022预印本/2024期刊；界面2023预印本/2025期刊；Schwarz2024预印本/2025期刊。AG当前v3为2025-11-23。

执行：工具输出中的Python urllib下载脚本（URL与状态保存在`references/source/download_log*.json`）、Crossref主题搜索与arXiv API组合查询、`pdftotext`、`.venv/bin/python references/build_catalog.py`。来源全文校验值在manifest。

错误/限制：通用网页工具两次空错误；Crossref部分429；ScienceDirect、Elsevier API、SSRN全文403。未绕过访问限制。arXiv2308.03088候选经首页核查为另一篇线弹性论文，标记误候选并保留排错资料；PG2023只核实书目，全文未得。不推测作者观点。

关键发现：界面预印本Summary明确将自适应配置点列为未来方向；2026 Residual-Christoffel及局部PoU自适应已存在，不能宣称D原创。预印本通量矩阵β因子及边界块疑似印刷漏项需正式版核对。

产物：research_plan、literature_review、literature_matrix、source快照、catalog、references.bib。下一步：取得PG全文并继续查新，当前不阻塞独立基线。

## 2026-10-13：数学与首个真实实验

完成：Poisson f=2π²sinπx sinπy；零边界五点差分；固定tanh、解析一/二阶导数、SVD最小二乘；直线界面制造解（非零法向通量、零跳跃）数学及程序一致性。

执行：`.venv/bin/python -m unittest discover -s tests -v > results/raw/test_basics.log 2>&1`（5测试通过）；`.venv/bin/python -m experiments.exp01_poisson > results/raw/exp01_run.log 2>&1`（退出0）；读取全部CSV；检查FDM解图。后续增加了拒绝覆盖/--rerun归档保护、执行--plot-only并用数据哈希验证重绘不改CSV。

关键结果：n=15/31/63/127相对误差3.21896444e−3、8.03577679e−4、2.00821810e−4、5.02009159e−5；阶2.002087、2.000522、2.000130。RaNN N=64的五种子平均相对误差8.63894250e−3（样本标准差4.76455459e−3）；N=128均值5.98657458e−5（标准差3.07592004e−5）；128平均条件数2.47729060e9，最大8.41929101e9。

错误：无数值异常/验收失败；首次绘图时Matplotlib因用户目录只读转到临时缓存，伴随Fontconfig缓存警告，绘图成功。随后将MPLCONFIGDIR与XDG_CACHE_HOME设置为项目内.cache并重新验证重绘。病态性是需研究的真实观察。不得把精度改善理解为全参数稳定或公平效率胜出。FDM与RaNN验证点和残差定义不同，已说明。

文件：src、experiments/exp01_poisson、tests/test_basics；results/raw CSV/JSON/log；results/tables；results/figures三组PNG/PDF；docs/initial_results、mathematical_derivations、experiment_protocol、quality_check_initial。第一批数据独立归档至results/archive/initial_20261013。

尚未完成：LRNN求解、原文方法复现、自适应、界面求解数值实验、论文初稿/编译。下一优先任务：双子域LRNN组装，明确β与跳跃符号，非零跳跃额外制造解及不同β验收。

## 2026-10-13：自主继续，LRNN与采样阶段

用户授权自主继续并根据结果补充提示词。创建`docs/autonomous_work_prompt.md`，依据已验收状态设置下一任务；不要求普通步骤确认，不宣称完整论文已完成。

完成：`StraightInterfaceProblem`补充非零gu/gq；`LocalTanhFeatures`加入局部尺度链式法则；`local_rann.py`组装含β的双子域内部/边界/值/通量矩阵。新增解析基可精确表示制造解的核查，隔离公式错误与表达力不足。`adaptive_sampling.py`实现A/B/C/D、两个指标消融、最小配额、探索和无放回抽样；两种预算分别按物理点/标量行守恒。每组独立流保证B包含C/D初始随机点前缀。

执行：`.venv/bin/python -m unittest discover -s tests -v`（13测试通过）；`python -m experiments.exp02_interface --run-id exp02_interface_20261013`（150次、失败0）；`python -m experiments.exp03_sampling --run-id exp03_sampling_20261013`（180次完整算法、失败0）；后续预登记`python -m experiments.exp04_sensitivity --run-id exp04_sensitivity_20261013`（285次、失败0）；`python -m experiments.build_stage_report`；三个`--plot-run`入口重绘并校验CSV哈希、case0系数解重建、重复run_id拒绝覆盖。

关键结果：界面128/侧时非零跳跃β=(1000,1)的raw/平衡平均解误差4.5787e−5/1.3906e−7，但物理通量RMS均值1.7633e−4/2.7557e−4，存在精度指标取舍。raw最大条件数1.69e15、最低数据秩240/256；balanced仍最高2.11e12、最低255/256。

采样负面结果：每种预算3β×5seed的15描述性配对中D对A/B解误差胜出0次；D/B误差比例中位数points约1.2635，equations约1.2561。完整耗时较静态更高。去PDE指标的消融给界面更多点，表现较好；后续相同最终组配额的固定随机均值在六组均更低且更快，未支持残差选点额外收益。所有负面数据保留，不修改主比较参数。

敏感性：β=(1,1000)每侧特征32/64/128/256平均相对L2约1.1375e−2/1.0851e−4/1.2361e−7/2.5805e−10，条件数随之从约1.82e5到1.08e17，256时数据秩404—417/512。scale和界面权重显著影响物理误差；强ridge有偏差；总点216→1728的解误差非单调。不能根据扫描最优值作普适参数推荐。

文件：新增三个run目录含CSV/配置/统计/系数NPZ/日志/图；exp02_protocol、exp03_protocol、exp04_protocol；interface_results、sampling_results、sensitivity_results、quality_check_stage2、stage2_verification；更新README、研究计划、数学推导与持续提示词。原始起步CSV和旧zip不覆盖。

错误与限制：无算法异常。实现时已在运行前修正exp02重绘入口的Path导入；均匀点改为完整矩形网格，避免截断最后一行偏置。D没有精度优势是科研结果，不是要删除的失败。候选池下一轮RMS包含已选训练点，可能乐观；独立测试从未参与。全文/正式版本缺口、Windows未测、无一般PDE理论仍保留。

下一步：独立局部峰/快变化制造解与预登记多预算；候选监测池变体；FD代表算例复现/文献缺口；右端扰动和rcond稳定性。当前定位独立实现、系统比较与稳定性分析，不强行原创或正面结论；尚未写整篇论文或编译。

## 2026-10-13：提示词丰富与独立峰值/扰动阶段

用户要求稍丰富提示词并继续。补充问题—假设—实验—证据衔接、负面结果处理、测试/候选/监测角色、行/点预算、扰动假设、来源追溯和论文论断证据表规则；根据已完成阶段消除过时待办。

完成：`PeakInterfaceProblem`在两侧增加共同零边界Gaussian峰，独立推导h梯度/Laplacian、f_i−β_iΔh和新增通量跳跃(β₂−β₁)h_x；两个测试检查公式、完整PDE、边界与界面。新增D_unused组指标范围（不计已选训练候选点），默认all保持旧实验机制。诊断增加最小保留奇异值。

执行：`.venv/bin/python -m unittest discover -s tests -v`（15通过）；`python -m experiments.exp06_peaks --run-id exp06_peaks_20261013`（400完整算法、异常0）；`python -m experiments.exp07_stability --run-id exp07_stability_20261013`（15谱、90扰动观察）；两任务初期并发，披露主峰时间的限制。两任务完成后`python -m experiments.exp08_efficiency --run-id exp08_efficiency_20261013`（25串行重复，系数与主case一致）；`python -m experiments.build_peak_report`；三个重绘入口、原始CSV哈希、系数重建及重复run_id保护核查。

峰参数：width=.12/.06，中心(.46,.55)、振幅.75；β=(1,1)/(1000,1)、N128/侧、scale2/4、3/6轮、1232/1904标量行、五固定种子、五方法。最终161×161/侧与81×81测试误差相对变化最大约0.49%，未用于选点。导出四模型解析数据及界面CSV。

关键结果：D对A/B/C的误差更低配对数为6/80、36/80、49/80，逐配对误差比例中位数1.2926、1.0948、.9627；设置之间相关，不作80独立样本推断。D_unused未稳定逆转。最大相对L2约1.493，程序正常不代表峰值高精度验收通过。固定窄峰代表β=(1000,1),scale4,六轮，A/D平均相对误差约.1948/.2845，串行完整时间约.0481/.4097秒。其他对照全部保留。

扰动：相对右端变化1e−8，固定TSVD保留空间；最小保留方向放大/上界约1。最大系数相对变化275.6，而预测函数相对变化最大约1.71e−8，可能接近浮点抵消地板。该结果不证明一般函数稳定性或病态无害，尚未做高精度/矩阵扰动核查。无截断时被丢弃方向不适用，以NaN记录。

错误/处理：无运行异常。峰值精度不足保留，未改参数追求D胜出。图检查发现2×2图行间标题/轴标签拥挤，加入tight_layout后重绘；数值CSV不变。并发任务计时限制通过独立串行复测处理，没有覆盖主时间。代码更新以本阶段哈希记录，历史哈希和旧包保留。

产物：exp06/07/08三个run，peak_results、stability_results、peak_efficiency_results、claim_evidence_matrix、quality_check_stage3、stage3_verification；数学推导§6/7、README、持续提示词更新。下一步：FD原文代表算例复现分级与全文缺口，统一证据和论文提纲。当前不声称已完成原文复现、查新或论文编译。

## 2026-10-13：FD花形近似复现与六章科研初稿

用户授权继续。核查2308.03087v1的Example4.1参数、表1、PDF图1内外区域。实现物理坐标tanh、中心FD导数、花形曲线法向、分片真解和β通量。初始范围per_domain解释作为假设运行110次；再核对§4.2同类措辞后，weight/bias分别范围更自然，独立追加weight_bias下三m/N×两导数×十种子60次，不改旧数据。最贴原文的60次作为近似复现主比较，旧步长/阈值等为额外对照。

执行：`python -m unittest discover -s tests -v`（18通过）；`python -m experiments.exp09_reproduction --run-id exp09_reproduction_20261013`（110、异常0）；`python -m experiments.exp09_reproduction --literal-only --run-id exp09_literal_20261013`（60、异常0）；重绘入口、CSV哈希、case0系数/独立误差重建；`python -m experiments.build_thesis_assets`生成7表7图及报告。

关键结果：weight_bias主解释FD GL20十种子均值m80/N1000=3.169e−5、m160/N1000=1.059e−7、m320/N5000=3.057e−10；原表分别1.18e−3、9.20e−6、3.17e−8，差异保留，不声称改进。per_domain步长变体h₂=.01/5e−4/1e−5/1e−6 GL100五次均值约2.635e−8/5.976e−10/1.262e−7/8.669e−6，显示小步长舍入恶化。正式作者实现、dtype/rcond/界面测度仍未知，不能称严格复现。

文献查询：OpenAlex两篇正式文章没有开放PDF链接；作者科研/发表论文主页未列目标全文链接，题头中文姓名“汪飞”，本稿使用Fei Wang避免原请求中文对应混用。新增SciPy文章Crossref DOI元数据；Matrix Computations的Crossref/ISBN和OpenLibrary第4版目录，日期2012/2013分别保留，全文未得。出版商403、Google Books429、作者搜索403没有绕过。快照保存。PG与期刊正式版缺口不伪造。

论文：建立详细提纲后，写入`thesis/main.tex`、六章、中英文摘要、附录及9条实际使用参考文献，CSV生成表和来源图。实际使用XeLaTeX编译30页，源汉字约八千（含表/参考文献，不等学校正文口径），学校信息待填写。没有ctexbook/xeCJK时使用book/fontspec/Noto的项目内草稿分支，无系统安装。

执行编译：`mkdir -p thesis/build/chapters`；在thesis中多遍`xelatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex`；`pdftotext -layout`；`python -m experiments.check_thesis`。首次缺少build/chapters写辅助文件失败，日志保留，创建后成功；随后修正表头转义、英文标识/长命令溢出、字体形状与引用顺序。最终编译无未定义引用/缺字/溢出警告。抽查数学正文与复现图。

检查中发现重绘源PDF的时间元数据使论文副本哈希不同，重新同步assets并编译，最终7图来源一致、引用集合及首次顺序一致，复现CSV未变。初稿审核报告单列尚未解决问题。`git status`发现工作目录不是有效Git仓库，未作提交，使用run_id、文件哈希和阶段zip保存版本。

产物：reproduction_results、thesis_outline、thesis_quality_report、stage4_verification；FD/flower模块、18测试；thesis完整源/PDF/7表7图/来源表/编译日志/final_verification；README与持续提示词更新。下一优先任务转为指导教师审阅、文献缺口、学校模板/字数、逐章修订；不再默认扩张旧模型实验。不声称稿件已满足学校提交或完成严格复现/全面查新。

## 2026-10-13 初稿修订v2

完成数学假设/误差分解/增行反例、统计与配额对照、积分敏感度、目标定位及质量报告。文件：thesis/chapters/02—06、main.tex、experiments/build_thesis_assets.py、check_thesis.py、docs/thesis_revision_v2.md。命令：python -m experiments.build_thesis_assets；XeLaTeX多遍；pdftotext；python -m experiments.check_thesis。真实结果：35页、11231源汉字、10份CSV生成表、7图、9引用；原始复现CSV未变。

错误：长行溢出改独立公式；标签变化再次编译解决；全局-W error触发第三方pyparsing弃用警告，正常生成成功，未修改第三方库。未新增数值实验，不声称再次执行18项算法测试。v1/v2归档保留。待办：导师审阅、文献全文与查新缺口、学校模板、Windows实机与高精度稳定性核查。

## 2026-10-16 大连理工数学本科论文v3

已核查学校官方页面，下载2024年3月文件汇编并保存版本/哈希；现行附件有验证码，未冒充取得。补五份正文分析文件及标准数学推导；纠正局部坐标必须用边长而非半宽的表述，连续抽样密度单列rho并明确二次可积。新增从180次主采样中整理60次等行预算记录的三份表及解析模型图，原始数值结果不变，无新PDE拟合。

运行：python -m experiments.build_thesis_v3_evidence；python -m experiments.build_model_illustration；python -m experiments.audit_thesis_v3；python -m unittest discover -s tests -v；XeLaTeX多遍；pdftotext；python -m experiments.check_thesis。真实结果：52页，正文叙述20388汉字（非学校认证），摘要536汉字/462词，11引用，13生成表另2说明表，8图。18测试、18封存原始CSV哈希通过。

错误：最初requests缺失改用urllib；默认命令网络受限，明确网络能力后下载公开汇编成功；现行模板验证码和ELM PDF HTTP465未解决，记录范围。附录长模块名溢出0.8172pt改命令块后解决。编译中一次检查命令使用了多余thesis路径而未读到文件，未影响其后构建；最终引用/缺字/溢出检查通过。未进行系统安装或删除数据。

文件：thesis/chapters/01_scope_expanded、02_model_analysis、03_implementation_analysis、04_protocol_analysis、05_discussion_expanded；v3三个证据/审查脚本；docs/dlut_requirements_review、submission_materials_checklist、thesis_revision_v3、thesis_quality_report；references/dlut；thesis/draft_v3.pdf。待办：导师与学生实质审阅、实际届次与本届学院细则、官方模板及真实流程、PG全文与查新、Windows和高精度核查。
