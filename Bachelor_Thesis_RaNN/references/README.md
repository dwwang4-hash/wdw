# 可核验参考资料

`source/`保存本轮实际下载的arXiv HTML、PDF、pdftotext文本及Crossref原始JSON。`download_log*.json`和`publisher_access_log.json`保留URL与访问成败；`manifest_sha256.csv`记录文件校验值。下载时间为2026-10-13，版本见HTML提交历史及PDF首页。

核心PDF已取得2206.05577v1、2308.03087v1、2408.17225v3、2412.19207v1。RNN-PG 2023正式全文未取得。2308.03088是误候选核查后确认的另一篇线弹性论文，保留作为排错证据，**不归入核心第一篇PDF**。

出版信息用出版方登记的Crossref元数据核实；无法访问ScienceDirect正式全文，因此不能称已核对所有正式版公式。AG-RaNN、2026补充预印本正式出版信息尚未确认。arXiv DOI与期刊DOI分别标记。

文献矩阵位于`../docs/literature_matrix.csv`，阅读笔记位于`../docs/literature_review.md`，核实书目条目的BibTeX位于`../thesis/references.bib`。BibTeX尚未套用学校格式；每条来源有标记。

这些资料仅用于阅读与核验，版权归原作者/出版方；分发工程时可只提供下载URL与校验清单，不需公开再发布PDF。
