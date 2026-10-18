# Windows + VS Code 本地迁移与复现

日期：2026-10-18。以下是下载后的待执行步骤，本次云端迁移没有运行科研实验、测试、绘图或论文编译，也没有在Windows实机执行这些命令。

## 1. 选择归档并检查下载

- `RaNN_Windows_Project_20261018.zip`：日常继续研究所需的完整可移植项目，根目录为`Bachelor_Thesis_RaNN`。
- `RaNN_All_Research_Backup_20261018.zip`：全部当前可访问科研版本备份，含同一项目及6份旧ZIP。项目位于`RaNN_All_Research_Backup_20261018/project/Bachelor_Thesis_RaNN`。历史包不是必须逐一解压的运行依赖。
- 归档旁另提供`RaNN_Migration_SHA256_20261018.txt`和发行JSON。下载后先用PowerShell计算ZIP哈希，与该文件对应条目比较：

```powershell
Get-FileHash .\RaNN_Windows_Project_20261018.zip -Algorithm SHA256
```

解压到一个不存在或干净的新目录，避免Windows询问覆盖已有科研文件。建议短路径如`C:\Research`；不要把新包直接解压覆盖旧研究目录。

```powershell
Expand-Archive -LiteralPath .\RaNN_Windows_Project_20261018.zip -DestinationPath C:\Research\RaNN_20261018
Set-Location C:\Research\RaNN_20261018\Bachelor_Thesis_RaNN
```

如果用全备份包，请进入其`project\Bachelor_Thesis_RaNN`，不是外层备份目录。目录内应同时看到README、src、experiments、results、thesis、scripts和migration。

本项目尚无Git远程，所以现在应下载ZIP。以后用户确认仓库并完成推送后才有真实克隆地址；此处不编造GitHub URL。

## 2. 在VS Code打开项目根目录

安装/使用本机VS Code和64位Python 3.12。终端运行：

```powershell
py -3.12 --version
code .
```

如没有`code`命令，从VS Code菜单“打开文件夹”选择上述项目根目录即可。`.vscode/settings.json`提供Windows虚拟环境解释器和unittest发现设置；不会自动安装依赖或执行任务。

## 3. 先作字节完整性检查

标准库校验不需要NumPy，也不导入求解器：

```powershell
py -3.12 -B scripts\verify_migration.py
```

应显示`passed: true`及清单文件数量。清单不含自身，清单SHA在外部发行JSON；它校验已封存文件，不把随后新增的本地run或虚拟环境当成错误。若失败，先检查解压目录、下载是否完整，保留错误，不修改云端参考CSV去迎合校验。

## 4. 创建独立Python环境并安装核心依赖

云端Linux的`.venv`没有打进包，不能复制到Windows使用。保持在项目根目录：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --disable-pip-version-check -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe --version
```

直接使用虚拟环境解释器，不必激活PowerShell脚本，也不必修改系统ExecutionPolicy。VS Code按`Ctrl+Shift+P`→`Python: Select Interpreter`，选`.venv\Scripts\python.exe`。

核心版本已固定：NumPy 2.2.6、SciPy 1.15.3、Matplotlib 3.10.3。`requirements-lock.txt`保留云端全部已安装传递依赖版本，供追溯；未证明其每个包都能在Windows安装。先用核心requirements，安装后保存本机版本用于比较。包中没有离线wheel仓库，首次安装需要可访问的Python包源；未安装系统级Python或改其他项目环境。

若`py`不存在，可使用本机Python 3.12的完整路径。不要用全局`pip`意外把依赖装到其他项目。Python小版本、BLAS和硬件可能不同，迁移不保证数值结果逐位相同或时间相同。

## 5. 运行基础测试（本地后续操作）

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

当前源码包含18项测试，最近的既有通过日志在`docs/v3_tests.log`。本轮迁移没有重新执行它们；这一步由Windows本机实际验证。测试覆盖模型/导数/组装、跳跃、预算与花形FD等，但并不证明所有参数均准确。

## 6. 运行不覆盖历史数据的最小CPU验证

```powershell
.\.venv\Scripts\python.exe -B scripts\local_smoke.py --run-id win_smoke_001
```

新脚本调用已有FDM实现，仅求n=15、31，结果写入`results\runs\win_smoke_001`；目录已存在会拒绝覆盖。比较参考误差约3.21896444e-3和8.03577679e-4，具体原始值来自云端`results/raw/poisson_fdm.csv`。不比较硬件时间。再次执行时改成新run_id。

可选增加一次原模型界面B策略验证（仍是新目录，不是完整研究验收）：

```powershell
.\.venv\Scripts\python.exe -B scripts\local_smoke.py --run-id win_smoke_interface_001 --interface
```

它调用原A/B/C/D入口中的B，β=(1000,1)、64特征/侧、seed11、1232行，使用原验证函数。这个迁移辅助入口本轮只作语法和调用签名检查，没有执行求解，也没有声称Windows已通过。

不要为起步验证直接运行`python -m experiments.exp01_poisson --rerun`：旧入口会归档后重写固定results/raw。使用上述新目录入口，或在完整复制的工作副本中另行研究。

## 7. 不重新求解，重画关键图

```powershell
.\.venv\Scripts\python.exe -B scripts\plot_saved_results.py
```

读取云端封存的FDM和采样CSV，输出新目录`results/local_plots/<时间戳>`的300dpi PNG、PDF及源CSV哈希。保留全部指定种子的散点和均值，不覆盖原图。也可指定不存在的新目录：

```powershell
.\.venv\Scripts\python.exe -B scripts\plot_saved_results.py --output results\local_plots\win_figures_001
```

原实验`--plot-run`通常在旧run内更新图，本次保真迁移优先不用它。字体、绘图库和PDF创建时间元数据不同，重绘文件哈希不必与旧图相同；应比较输入CSV和图中数据。所有云端原图已直接保存在项目中，可先打开观看，无需重绘。

## 8. 需要时再重跑完整实验，并与云端比较

完整批次不是最小验证。完成前述步骤后自行决定运行，例如：

```powershell
.\.venv\Scripts\python.exe -B -m experiments.exp03_sampling --run-id win_exp03_001
.\.venv\Scripts\python.exe -B scripts\compare_runs.py --cloud results\runs\exp03_sampling_20261013\raw\sampling.csv --local results\runs\win_exp03_001\raw\sampling.csv --output results\runs\win_exp03_001\comparison.json
```

比较工具按预算、两侧系数、方法和种子配对，报告相对L2差异及数值秩。默认5%相对差为可调整诊断阈值，不是误差定理或普适验收要求；不自动修改数据。图像字节不一致不是数值迁移失败；高度病态系统的末位或阈值附近秩变化也不必说明丢文件。优先检查依赖、随机种子、SVD阈值和聚合结果。

新run目录拒绝覆盖，已有`win_exp03_001`时请换名字。各完整实验入口/配置/结果见实验复现指南。CPU dense SVD批次在本机可能明显更慢；大宽度、5000点花形和多种子扫描不要一上来全跑。

## 9. Linux/Windows差异与CPU设置

- 原文件内记录的`/workspace/...`是历史出处，不需要在Windows创建同名目录；代码使用Path定位项目根。
- Python入口建议`python -m experiments...`，并在项目根目录执行；避免双击文件导致模块路径不同。
- 源码和文档UTF-8，CSV多用UTF-8-SIG以兼容Excel。不要用Excel另存覆盖原CSV；换行/编码改变也会使SHA不同。
- 代码本身设置BLAS单线程。若希望在启动进程前也明确约束，可在当前PowerShell会话设置：

```powershell
$env:OPENBLAS_NUM_THREADS="1"
$env:OMP_NUM_THREADS="1"
$env:MKL_NUM_THREADS="1"
```

这些只是当前会话变量，不写系统环境。没有GPU或PyTorch必需依赖，最小验证就是CPU方案。不同CPU/BLAS/线程调度导致速度不同；不要把旧时间直接当作本机性能验收线。

## 10. 论文与Git后续

`thesis/draft_v3.pdf`可直接阅读。无需为迁移重新编译。要编辑LaTeX，需要另备XeLaTeX、中文字体及Poppler；依赖不在Python requirements内。Noto字体在Windows可能缺失，ctexbook分支通常使用本机字体，需本地核对，不擅自系统安装。构建命令见thesis/README.md，先复制工作副本再更新派生论文文件。

此项目没有Git历史，所有文件不是“已提交”；也不能声称它们是git status里的未跟踪文件。确认仓库前不要推送。拟版本管理的源码、配置和原始科研数据可保留，Linux环境与缓存不入库；原始科研单文件最大约14.23MiB，无超过100MiB的项目文件。旧ZIP最大约51.34MiB，宜作备份/发行附件而不反复放进Git提交。本轮没有创建或公开仓库。
