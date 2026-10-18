"""从已保存的官方元数据重建书目与文献矩阵，不重新联网。"""
import csv
import hashlib
import json
import re
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "references/source"

NOTES = {
    "pg": ("未获全文", "待原文", "待原文", "待原文", "待原文", "待原文", "待原文", "PG与强形式配置的差异待核查", "小规模线性Poisson弱形式（有全文后）"),
    "dg": ("预印本初读", "Poisson及热方程；网格和近似/连续性假设", "三种LRNN-DG格式及条件性分析", "局部随机空间+DG积分+面配置+增广最小二乘", "例5.1 Helmholtz；5.2 Poisson；5.3 heat", "表4 h=2^-3、DoF_K=160时L2=1.49E-07，原文数据未复现", "Assumption3.5/3.7需额外控制，不能删去", "增宽饱和是否与配置点和秩有关（本项目猜想）", "单个二维算例、奇异值和面误差"),
    "interface": ("2023预印本初读；正式版全文未读", "分片正常数β；椭圆/抛物界面；值与通量跳跃", "子域网络+FD导数+界面最小二乘+混合/时空格式", "式3.3-3.7；一阶h=1e-6、二阶h=5e-4；组行权重50", "二维花形/三维/多界面/高维/固定与动态抛物", "例4.1表1 m=320,N=5000相对L2=3.17E-08；原文未复现", "Summary明确提出采样自适应、参数范围与数值分析待研究", "联合界面指标可能有用也可能因尺度失衡无效（猜想）", "直线界面独立实现；解析与FD模式区分"),
    "schwarz": ("预印本初读", "局部随机网络；重叠域；最小二乘", "PCA删冗余+AS/RAS预条件", "单位分解+边界约束+PCA+CG/GMRES", "多尺度、时间相关、三维；对比QR", "§5/§6报告条件数/时间改善；未转录量化收益", "§6提出多层、并行、稠密块和数值分析需求", "采样能否降低冗余和有效条件数（猜想）", "SVD诊断与简单正则化；不必实现Schwarz"),
    "ag": ("v3初读", "一般PDE；图范数等价、激活/正则性及iid采样等假设", "频率初始化+宽/深增长+域分裂+误差分解", "残差引导新特征；§5.1实验用均匀配置点", "振荡/尖峰Poisson、不连续对流反应等", "§5报告基准改善；未重建原始表格", "§4末/§6完整多层自适应的阶与复杂度待研究", "固定特征隔离配置点效应（本项目问题）", "不增长网络，只对比空间采样"),
    "rar": ("书目/全文初读", "PINN前向/反问题", "RAD/RAR-D及10类采样系统比较", "残差概率密度及增量/替换采样", "四个前向及两个反向问题；摘要称6000余次仿真", "作者报告RAD/RAR-D提升；本项目未复现", "全面作者局限待逐段精读", "如何迁移至固定随机特征及界面（本项目问题）", "残差采样基线与候选概率"),
    "high_precision": ("仅书目核实", "待原文", "待原文", "待原文", "待原文", "待原文", "待原文", "高精度病态性的关系待研究", "后续重点阅读"),
    "elm": ("v3摘要和§5初读", "域分解随机特征、多层", "ELM-FBPINN及多层比较", "固定隐藏特征+局部窗口+线性求解", "1D振子、2D多尺度Laplacian/Helmholtz", "§5大K条件数常超1e18；2D FBPINN最终精度可更好", "§5激活饱和、冗余及有效秩饱和", "采样和局部宽度是否交互（猜想）", "宽度/局部分域消融"),
    "christoffel": ("v1初读摘要/算法定位/§6", "固定特征线性PDE；条件于试探空间", "算子残差空间采样+逆密度权重+白化", "残差Gram、Christoffel密度、贪心logdet", "1-3维、标量/向量、多种几何", "§6报告条件数/迭代改善；O(r log(r/δ)/ε²)采样在假设下", "§6局部/多尺度、流式Gram、块leverage为后续方向", "解残差联合指标与空间几何采样有何不同（本项目问题）", "必须重点对比，不能声称采样稳定性新颖"),
    "pirann": ("官方页/PDF初读；题名不一致", "广义Barron谱空间；局部PoU", "局部缩放随机参数+残差Dörfler细化", "PoU、后验指标、标记/细化", "1D Burgers、2D/3D峰与L形角点", "作者报告定位高梯度/奇点；本项目未复现", "作者明确局限待补精读", "已有局部残差自适应与D区别待查", "读残差定义与细化预算"),
    "ad": ("仅官方摘要", "隐藏特征分布低维参数化", "PDAD/DDAD分布适应", "两阶段岭约化优化与无岭重拟合（摘要）", "官方摘要列空间时间及算子学习；全文未读", "仅作者摘要报告，无核实量化数值", "待全文", "隐藏参数采样与配置点采样不能混淆", "暂作参数敏感性背景"),
}


def crossref_record(key, filename, arxiv=""):
    data = json.loads((SOURCE / filename).read_text(encoding="utf8"))["message"]
    item = data["items"][0] if "items" in data else data
    return {"key": key, "title":item["title"][0], "authors":"; ".join(a.get("given", "")+" "+a["family"] for a in item["author"]),
            "year":item["published"]["date-parts"][0][0], "journal":item.get("container-title",[""])[0],
            "volume":item.get("volume",""), "issue":item.get("issue",""), "pages":item.get("page",""),
            "doi":item["DOI"], "doi_type":"正式出版", "arxiv":arxiv,
            "source":filename, "pdf":f"https://arxiv.org/pdf/{arxiv}" if arxiv else "未核实公开PDF"}


def arxiv_record(key, ident):
    html=(SOURCE/f"{ident}.html").read_text(encoding="utf8")
    def meta(name):return [unescape(x) for x in re.findall(r'<meta name="'+name+r'" content="([^"]*)"',html)]
    return {"key":key,"title":meta("citation_title")[0],"authors":"; ".join(meta("citation_author")),
            "year":int(meta("citation_date")[0][:4]),"journal":"arXiv预印本；正式出版未核实","volume":"","issue":"","pages":"",
            "doi":"10.48550/arXiv."+ident,"doi_type":"预印本", "arxiv":ident,"source":ident+".html","pdf":"https://arxiv.org/pdf/"+ident}


def main():
    records=[crossref_record("pg","doi_pg.json"),crossref_record("dg","doi_dg.json","2206.05577"),
             crossref_record("interface","doi_interface.json","2308.03087"),arxiv_record("ag","2408.17225"),
             crossref_record("schwarz","doi_schwarz.json","2412.19207"),crossref_record("rar","doi_rar.json","2207.10289"),
             crossref_record("high_precision","crossref_high_precision.json"),arxiv_record("elm","2409.01949"),
             arxiv_record("christoffel","2607.13382"),arxiv_record("pirann","2604.08869"),arxiv_record("ad","2604.23999")]
    columns=["reading_status","model_assumptions","authors_contribution","algorithm_derivation","original_experiments","original_results_not_reproduced","authors_limitations","our_questions_not_authors_claims","undergraduate_entry"]
    rows=[]
    for record in records:
        record["verified_date"]="2026-10-13"
        row={**record,**dict(zip(columns,NOTES[record["key"]]))}
        row["local_pdf_exists"]=(SOURCE/f"{record['arxiv']}.pdf").exists() if record["arxiv"] else False
        rows.append(row)
    with (ROOT/"docs/literature_matrix.csv").open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (ROOT/"references/catalog.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf8")
    entries=[]
    for r in records:
        # 未精读的条目可留在书目库；正文不得据此填充未经核实观点。
        author=r["authors"].replace("; "," and ")
        fields={"author":author,"title":r["title"],"year":str(r["year"]),"doi":r["doi"],"url":"https://doi.org/"+r["doi"],
                "note":"Metadata verified 2026-10-13; source: "+r["source"]}
        if r["doi_type"]=="正式出版":fields.update({"journal":r["journal"],"volume":r["volume"],"pages":r["pages"]})
        else:fields.update({"eprint":r["arxiv"],"archivePrefix":"arXiv"})
        entries.append("@"+("article" if r["doi_type"]=="正式出版" else "misc")+"{"+r["key"]+",\n"+",\n".join("  "+k+" = {"+v+"}" for k,v in fields.items() if v)+"\n}")
    (ROOT/"thesis/references.bib").write_text("\n\n".join(entries)+"\n",encoding="utf8")
    with (ROOT/"references/manifest_sha256.csv").open("w",encoding="utf8",newline="") as f:
        writer=csv.writer(f);writer.writerow(["path","bytes","sha256"])
        for p in sorted(SOURCE.iterdir()):
            if p.is_file():writer.writerow([p.relative_to(ROOT).as_posix(),p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest()])
    print(f"Generated {len(rows)} verified/qualified literature records")


if __name__=="__main__":main()
