# 大连理工数学本科论文科研修订稿v3

当前PDF：`draft_v3.pdf`，最新副本`draft.pdf`。实际编译52页，正文六章保守项目统计20388汉字（排除公式、图表、摘要、文献、附录），中文摘要536汉字、英文摘要462词，引用11项。13份CSV生成表，另有符号与设置概览表，共8幅图。统计不是学校Word计数认证。

采用真实数据的中文审阅稿，不是已经学校核准的格式终稿。当前封面个人信息、致谢、声明及签名不能代填。现行学校模板附件要求验证码，规范核查见`../docs/dlut_requirements_review.md`，不能将2010年数学学院通知当成本届现行细则。

## 从封存数据重建证据

在项目根目录运行（Linux可用`.venv/bin/python`，Windows可用`.venv/Scripts/python.exe`）：

```bash
python -m experiments.build_thesis_assets
python -m experiments.build_thesis_v3_evidence
python -m experiments.build_model_illustration
python -m experiments.audit_thesis_v3
```

必须按此顺序执行：第一个入口重建通用图源清单，第三个入口补入模型示意图来源。模型图从解析剖面CSV绘制，不是拟合结果；两个表生成入口不重新求解PDE。程序拒绝实验run覆盖，重绘派生图表则允许更新副本。原始CSV不得改写。

## 编译与检查

需已有XeLaTeX、中文字体及Poppler命令`pdftotext`、`pdfinfo`。Windows实机尚未验证；不声称系统已自动安装这些依赖。环境有ctexbook时优先使用；本云环境使用book/fontspec/Noto字体的科研稿分支，中文标题由项目设置。

在thesis目录执行，先创建`build/chapters`。Linux示例：

```bash
mkdir -p build/chapters
xelatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex > build/compile_pass1.log 2>&1
xelatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex > build/compile_final.log 2>&1
pdftotext -layout build/main.pdf build/main_text.txt
```

若标签变化，重复最后一遍编译与文本导出。Windows先创建对应目录，再使用本机终端支持的重定向语法。返回项目根目录运行：

```bash
python -m experiments.check_thesis
```

校验包括最终编译警告、展开子文件后的首次引用顺序、8图来源哈希、阶段2—4的18份封存原始CSV哈希及本轮原始数据清单。通过后复制`build/main.pdf`到`draft.pdf`并写入`build/final_verification.json`。生成归档版本的`draft_v3.pdf`需在最终校验通过后复制，不把失败构建当作正式输出。

## 归档与限制

v1、v2和修改前v2的源文件/PDF保留于`versions/`；当前v3另行归档。源汉字统计排除了该目录，防止版本副本重复累计。学校材料清单和辅助范围说明在`../docs/submission_materials_checklist.md`。18项程序测试本轮通过；未进行新的PDE数值实验，未声称严格原作者复现或一般原创算法优势。全部局限见`../docs/thesis_quality_report.md`。
