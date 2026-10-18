# 文献核实与初步阅读笔记

核查日：2026-10-13。依据arXiv作者预印本PDF、arXiv页面和Crossref出版方登记信息；快照在`references/source/`，矩阵在`literature_matrix.csv`。以下为**起步阶段初读**，并非每篇证明的逐行审稿。原文实验结果不等于本项目复现结果。原文表格数值只在注明表号时摘录；未读全文者不填写观点和结果。

## 核心书目信息及版本差异

1. Shang, Yong; Wang, Fei; Sun, Jingbo. *Randomized neural network with Petrov–Galerkin methods for solving linear and nonlinear partial differential equations*. Communications in Nonlinear Science and Numerical Simulation, **127 (2023), 107518**. DOI：[10.1016/j.cnsns.2023.107518](https://doi.org/10.1016/j.cnsns.2023.107518)。正式书目信息已由Crossref核实。全文未获取：ScienceDirect、Elsevier API、SSRN均403，题名精确arXiv检索未找到对应版本。SSRN 4420653题名是*Deep Petrov-Galerkin Method…*，不能未经比对认定其等同正式全文。arXiv:2308.03088是**另一个线弹性问题论文**，不是此文；不得替代引用。
2. Sun, Jingbo; Dong, Suchuan; Wang, Fei. *Local randomized neural networks with discontinuous Galerkin methods for partial differential equations*. Journal of Computational and Applied Mathematics, **445 (2024), 115830**. DOI：[10.1016/j.cam.2024.115830](https://doi.org/10.1016/j.cam.2024.115830)。[预印本2206.05577v1](https://arxiv.org/abs/2206.05577v1)，2022-06-11，已下载29页PDF。预印本年份2022，正式出版年份2024，不能混写。
3. Li, Yunlong; Wang, Fei. 正式版题名*Local randomized neural networks with finite difference methods for interface problems*. Journal of Computational Physics, **529 (2025), 113847**. DOI：[10.1016/j.jcp.2025.113847](https://doi.org/10.1016/j.jcp.2025.113847)。[2308.03087v1](https://arxiv.org/abs/2308.03087v1)，2023-08-06，22页PDF题名*Local Randomized Neural Networks Methods for Interface Problems*。当前读的是2023预印本，正式版方法/勘误尚需进一步比对。
4. Dang, Haoning; Wang, Fei; Jiang, Song. *Adaptive-Growth Randomized Neural Networks for PDEs: Algorithms and Numerical Analysis*. [2408.17225](https://arxiv.org/abs/2408.17225)，首次2024-08-30；当前下载**v3，2025-11-23，42页**。DOI：10.48550/arXiv.2408.17225（预印本DOI）。本轮未核实期刊正式出版信息，不能写成确定未发表或推测期刊。旧版本题名与2024文献列表中的“Adaptive growing…”存在差异，理论分析须按v3标注。
5. Shang, Yong; Heinlein, Alexander; Mishra, Siddhartha; Wang, Fei. *Overlapping Schwarz preconditioners for randomized neural networks with domain decomposition*. Computer Methods in Applied Mechanics and Engineering, **442 (2025), 118011**. DOI：[10.1016/j.cma.2025.118011](https://doi.org/10.1016/j.cma.2025.118011)。[2412.19207v1](https://arxiv.org/abs/2412.19207v1)，2024-12-26，已下载24页。

## L1：RNN-PG 2023（仅书目核实，全文待补）

背景/模型/假设/创新/推导/实验/作者局限：均待全文，不能根据题名填成作者观点。本项目预定关注试探空间、分片多项式测试函数、积分组装和最小二乘与强形式配置的区别，但这只是阅读问题清单。切入点暂是一个线性Poisson弱形式算例，最终是否实施依赖完整算法说明。出版信息核实不能算完成方法复现。

## L2：LRNN-DG（原文§2—§5）

背景与模型：用分片随机网络替代局部多项式，在DG框架下耦合；以Poisson为模型，扩展到热方程的时空离散。模型有边界数据，不能将文中所有实验误认为零Dirichlet。

核心方法：每个单元固定随机隐藏参数构造局部有限维函数空间。标准DG双线性形式含单元梯度积分、面平均/跳跃及惩罚；文中还有LRNN-C⁰DG与LRNN-C¹DG，用面配置约束连续性/导数连续性，组装增广线性系统并求最小二乘。原文(2.21)—(2.24)及§3是重点。**本项目的强形式点配置RaNN不等于该DG方法。**

数学假设：§3误差分析包含网格、近似和面约束控制假设，原文Assumption 3.5、3.7并在表7给数值支持。有限面点满足条件不自动意味着整条面上跳跃为零，不可删除这些假设后引用结论。

原文实验：Example 5.1一维Helmholtz；5.2二维Poisson，u=e^(x+y)sin(3πx+0.5π)cos(πy+0.2π)，单位方形；5.3热方程，比较FEM/DG。Example 5.2表4在h=2⁻³、每单元160自由度时L²误差1.49E−07，而640自由度时1.31E−07；这是原文表格，显示增宽并非无限持续降低误差。§5.2说明隐藏参数U[−1,1]，C⁰/C¹每边70配置点。

作者明确的限制/分析条件：理论中的近似和连续性控制依赖假设；不能据原文“高精度”推断所有初始化和参数都有保证。本轮未确认更全面的作者局限陈述，后续逐段精读。

我们的研究猜想：配置点不足或近线性相关可导致增宽后误差饱和；应同时监测秩与独立面误差。本科切入点：先解释DG与强形式配置的区别；若选此文复现，仅选5.2的小网格，不同时复现全部时空格式。

## L3：界面LRNN-FD（预印本§2—§5，最直接的基线来源）

模型：−∇·(β∇u)=f，两侧正常数β，指定[u]、[β∇u·n]及Dirichlet；原文跳跃定义u₁−u₂。抛物型版本含初值及已知移动界面。

贡献：不同子域用不同随机网络；内部、边界、界面点形成线性约束；导数用有限差分；还给混合形式p=β∇u和时空方法。是原文贡献，不能称本论文原创。

算法推导：式(3.3)—(3.5)将u_i=Σα_kiψ_ki代入各类条件，叠置内部A、值跳跃B、通量C、边界D；Remark 3.2按组γ_i加权。式(3.6)、(3.7)为一、二阶中心差分。§4设一阶步长10⁻⁶、二阶步长5×10⁻⁴（原文两个步长都写hx，应按导数阶区别），γ_i=50，tanh单隐层，十次随机试验平均，PyTorch实现。使用解析导数的本项目基础方案只能标为独立实现。

重要公式核查：预印本(3.5)写出的C行未显式含β，与(2.1)物理通量条件不一致；D块表达也需检查。正式版可能有修正，本轮无法核对。实施必须按模型带β，并把差异列入复现报告；不得照抄漏项或“调数据”匹配表格。

实验：4.1二维花形界面；4.2三维；4.3多界面；4.4高维；4.5固定界面抛物；4.6动态界面。4.1表1：β₁=1、β₂=10、m=320、N=5000时相对L²=3.17E−08；同表更大m并非总更准确。表2在(β₁,β₂)=(10⁴,10⁻⁴)时误差6.26E−05，而(10⁻⁴,10⁴)为1.17E−09；参数范围也随组别调整。因此不能引用为“与系数对比度无关的统一稳定性”。这些数值是**原文报告、未经本项目复现**。

作者明确后续方向：§5 Summary列出随机权重/偏置范围选择、自适应配置点、数值分析和复杂物理应用。该文确实为采样研究提供动机，但不是对2026新颖性的保证。

我们的猜想：联合残差分配可能改善部分界面欠采样情形，也可能因尺度失衡/矩阵病态无效。本科切入点：二维直线、解析导数与FD双模式；固定特征比较点预算和界面比例，先做独立实现，再选花形或简化代表算例复现。

## L4：AG-RaNN（v3 §3—§6）

背景：随机隐藏参数分布难选，浅层光滑特征对尖峰/不连续难逼近。方法：频率信息初始化；基于残差构造新增神经元与层，不训练全部隐藏参数；域分裂处理不连续。增长的是**特征/架构**，不能等同“增加配置点”。

推导脉络：§3利用源项/残差频谱构造随机参数范围和候选特征；§4把误差分解为近似、统计与优化；Theorem 4.15条件包含图范数等价Assumption 4.1、激活条件Assumption 4.3、真解Sobolev正则性、有界隐藏参数盒、独立同分布采样以及经验损失精确极小化。自适应点不是iid时不能原封不动引用此理论。

原文实验：§5用MATLAB rng(1)、QR linsolve，DFT选初始化，Gauss–Legendre误差积分；§5.1明确实验配置点为均匀采样。Example 1振荡/尖峰Poisson的一至三维、多峰；Example 2不连续对流反应，另有后续模型，精读待完善。Example 1 Case 2表3—4显示增长策略与FEM比较；这里只记录原文在给定基准中改善精度的报告，不替本项目给出收益百分比。

作者明确局限：Remark 3.4零源项无法提供有意义频谱初始化信息；§4末/§6将完整多层随机网络严格分析留作未来方向。正文理论和实验采样设定有区别，应逐项注明。

我们的猜想及本科切入点：保持特征不增长，只调整配置点以隔离采样效应；比较“精度不足来自空间表达力”还是“来自配置点覆盖”，不重建其高阶Sobolev证明。

## L5：重叠Schwarz（§2—§6）

背景：局部随机特征系统病态且大规模直接求解成本高。局部随机网络以单位分解窗口连接；约束算子处理边界；PCA删减冗余基函数；加性/限制加性Schwarz预条件，分别配CG/GMRES。此处采用正规系统/迭代与预条件的组合，不可因为我们避免直接正规方程就评价原法“错误”。

模型和推导：固定特征构造强形式最小二乘；局部残差矩阵经PCA压缩，子域限制/延拓及局部逆产生预条件器；详见原文§3—§4。窗口导数也属于PDE矩阵，不可只对子网络求导而忽略窗口。

实验及结果：§5多尺度、时间相关及三维问题，报告PCA/预条件降低条件数、迭代求解减少时间，与QR对比；这些是原文特定实验结论。本轮未逐表转录量化收益，避免混用不同系统规模和时间。

作者明确局限：§6要求两层/多层Schwarz、并行方法、稠密块预条件设计与进一步数值分析；数据/代码声明为可向通信作者合理请求，不能声称已获得作者代码。

我们的猜想及本科切入点：首先SVD奇异值诊断与尺度/岭的简单控制，研究点选取是否改善有效秩；完整Schwarz并非本科最低任务。

## 2024—2026补充文献与新颖性风险

| 来源 | 已核实及阅读程度 | 与本课题的关系 |
|---|---|---|
| Chen, Jingrun; E, Weinan; Sun, Yifei. Optimization of Random Feature Method in the High-Precision Regime. CAMC 6(2),1490–1517,2024. DOI 10.1007/s42967-024-00389-8 | Crossref书目已核实，全文本轮未取得 | 高精度随机特征稳定性重点待读；不能仅根据题名归纳结论。 |
| Anderson, Samuel; Dolean, Victorita; Moseley, Ben; Pestana, Jennifer. ELM-FBPINNs: An Efficient Multilevel Random Feature Method. arXiv:2409.01949 | 下载v3（2026-05-18）42页；初读摘要、讨论§5 | 局部/多层随机特征的误差、条件数、成本消融；§5指出大宽度可使SVD条件数超过10¹⁸，二维FBPINN最终精度可能更好，随机方法并非全指标胜出。正式出版DOI本轮未核实。 |
| Yang, You; Wang, Fei. Adaptive-Distribution Randomized Neural Networks for PDEs: A Low-Dimensional Distribution-Learning Framework. arXiv:2604.23999,2026 | 官方页及摘要核实，PDF未下载/全文未读 | 调的是隐藏参数分布，区别于空间配置点；仅据作者摘要记录这一定位。 |
| Bi, Ran; Deng, Weibing. arXiv:2604.08869,2026 | 官方页题名Adaptive Randomized Neural Networks with Locally Activation Function…；当前PDF题名Adaptive Physics-Informed Randomized Neural Networks with a Partition of Unity for Solving PDEs；31页，初读 | 残差后验指标+Dörfler标记+局部单位分解细化，已是残差驱动局部随机网络自适应。不得将局部残差细化当作首次提出。题名版本差异保留，未核实正式出版。 |
| Linghu, Jiale; Wang, Yangshuai. Residual-Christoffel Sampling for Random Feature Collocation of Linear PDEs. arXiv:2607.13382,2026 | 官方页和v1 PDF（35页）核实；初读摘要/§6及算法定位 | 算子作用后特征Gram决定采样密度、逆密度权重和白化，另有log-det贪心选行；条件于已实现特征空间的谱近似采样复杂度。这里“residual”是算子残差空间几何，不能混为当前解残差幅值。与配置点稳定性非常接近，需列为后续重点比较。 |
| Wu, Chenxi; Zhu, Min; Tan, Qinyang; Kartha, Yadhu; Lu, Lu. A comprehensive study of non-adaptive and residual-based adaptive sampling for physics-informed neural networks. CMAME 403,115671,2023. DOI 10.1016/j.cma.2022.115671，arXiv:2207.10289 | 书目和PDF核实，初读摘要及采样定位 | 六种固定均匀策略、重采样、RAD/RAR-D等十类比较；残差自适应是明确先行工作。虽然早于2024，仍是必要基线。未在本轮重建全部PINN实验。 |

Musekamp等arXiv:2408.01536 *Active Learning for Neural PDE Solvers*只读官方摘要，偏外部求解器生成训练集与参数/初值选择，非本课题直接配置点方法，不据其结果支持D。

## 检索范围及限制

真实执行：Crossref题名/主题检索（2024-01-01至2026-10-13过滤）、arXiv网页题名搜索、arXiv API组合搜索“interface/adaptive/sampling”“random feature sampling PDE”“randomized neural adaptive”。返回快照保留。广泛`all:`搜索有大量无关条目，仅按题名筛选，不能当作全面查新。Crossref部分请求429；通用网页工具返回空错误；出版商全文403。未绕过拒绝或使用付费资源。

结论：**已确认残差采样、局部随机网络自适应和算子感知配置点稳定性都存在先行工作；尚不能确认D的具体联合预算公式是否与先行研究相同，也不能证明其新颖性。** 后续必须进一步检索界面多项残差、界面重要性采样、multi-objective采样、leverage/Christoffel及分域预算分配，精读最近候选全文，形成逐项差异表，再决定是否称方法改进。

## 初稿阶段新增核查

再次请求OpenAlex两篇正式期刊记录，响应没有开放PDF URL；不据此推断网上绝无全文。访问作者科研/论文列表页，页面题头为“汪飞”，本稿使用英文Fei Wang避免原请求“王飞”中文对应的未经核实混用；本轮页面未显示目标文章全文链接，快照在source。PG与界面正式版本全文缺口仍保留。

PDF第3页图1明确Ω₁在闭合界面内，Ω₂在外。原文§4.1/§4.2权重和偏置“分别”范围的文字更自然指weight/bias，近似复现主比较因此采用weight_bias；已执行的per_domain假设作为对照保留，追加登记不改写旧结果。数学通量仍按β加权，预印本印刷C行疑似漏β的正式勘误未获核实。

新增SciPy 1.0文章正式Crossref元数据：Virtanen、Gommers、Oliphant等，Nature Methods 17:261—272（2020），DOI10.1038/s41592-019-0686-2。另核实Matrix Computations书名/ISBN/出版社的Crossref记录与OpenLibrary第4版（2013）目录；Crossref登记日期2012不同于版次目录2013，初稿采用4版目录年份。教材全文未得，只作标准线代背景，自含推导不声称作者具体新定理或已精读教材。

## 2026-10-16 补充

新增ELM 2006出版页摘要核查，仅引用固定隐藏节点与线性输出参数的基础定位；本地全文下载HTTP465，不归纳未读定理。ELM-FBPINNs已保存v3（2026-05-18）PDF，v3论文新增引用该实际版本，首次提交年份2024与阅读版本2026区分。核心PG全文与完整新颖性核查仍未补齐，未将摘要等同完整阅读。
