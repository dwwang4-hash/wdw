# 科研初稿v2修订说明

日期：2026-10-13。学校尚未发布模板通知，继续使用项目内中文科研草稿。

## 实际修改

1. 第二章增加符号表、有限维误差分解及增行性质证明，区分固定矩阵理论和真实自适应系统。
2. 第三章写出逐侧边界及两类界面的加权目标，澄清行乘数与平方权重。
3. 第四章修正抽样期望公式适用条件；实际增量无放回过程没有直接套用独立同分布结论。
4. 第五章补均值/样本标准差、18组配对结果、同最终配额固定随机对照、积分敏感度；新增表均来自已有CSV，不新增或改写实验。
5. 第六章逐项对应最低、标准和拓展目标。拓展目标尚未获得稳定优于合理基线的证据，不声称原创算法或普遍失败定理。

## 检查与限制

实际生成10份CSV表并编译35页PDF；7图哈希、引用顺序与复现CSV校验通过。正文源汉字11231（包括表及参考文献，不等同学校正文统计）。原版源文件/PDF归档。学校格式、个人信息、PG全文、全面查新、严格作者复现及Windows实机仍待处理。

严格全局Python警告检查曾因第三方pyparsing弃用警告中止，正常表生成已成功；该警告不属于数值失败。首轮排版有一处长行溢出，改为独立公式后解决；标签更新警告通过再次编译解决。全部最终状态以final_verification.json为准。

## 复现命令

```bash
.venv/bin/python -m experiments.build_thesis_assets
# 在thesis目录执行XeLaTeX；build/chapters须存在，按需多遍消除标签警告
xelatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
pdftotext -layout build/main.pdf build/main_text.txt
# 返回项目根目录
.venv/bin/python -m experiments.check_thesis
```

完整编译命令须将最终日志保存为build/compile_final.log，运行说明见thesis/README.md。
