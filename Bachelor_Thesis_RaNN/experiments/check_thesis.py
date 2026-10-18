"""检查最后编译、引用顺序、图源和原始数据，再生成审阅PDF副本。"""
from pathlib import Path
import csv,hashlib,json,re,shutil,subprocess
from .audit_thesis_v3 import expand

ROOT=Path(__file__).resolve().parents[1]


def main():
    thesis=ROOT/'thesis';log=(thesis/'build/compile_final.log').read_text()
    for bad in ['undefined','Missing character','Overfull','LaTeX Warning','LaTeX Font Warning']:
        if bad in log:raise AssertionError(f'最后编译存在问题：{bad}')
    pdf=thesis/'build/main.pdf'
    if pdf.stat().st_size<100000:raise AssertionError('PDF异常小')
    info=subprocess.run(['pdfinfo',str(pdf)],capture_output=True,text=True,check=True).stdout
    pages=int(re.search(r'Pages:\s*(\d+)',info).group(1))
    text=(thesis/'build/main_text.txt').read_text()
    for term in ['绪论','预备知识','局部随机神经网络离散方法','配置点策略','数值实验','总结与展望','参考文献']:
        if term not in text:raise AssertionError(f'正文缺少章节：{term}')
    for source in csv.DictReader((thesis/'asset_sources.csv').open(encoding='utf-8-sig')):
        left=hashlib.sha256((thesis/'figures'/source['thesis_figure']).read_bytes()).hexdigest()
        right=hashlib.sha256((ROOT/source['source']).read_bytes()).hexdigest()
        if left!=right:raise AssertionError('图副本与最新源不同：'+source['thesis_figure']+'；先重建assets并重新编译')
    first_cites=[]
    for name in ['01_introduction.tex','02_preliminaries.tex','03_method.tex','04_sampling.tex','05_results.tex','06_conclusion.tex','appendix.tex']:
        for group in re.findall(r'\\cite\{([^}]+)\}',expand(thesis/'chapters'/name)):
            for key in group.split(','):
                if key not in first_cites:first_cites.append(key)
    bibkeys=re.findall(r'\\bibitem\{([^}]+)\}',(thesis/'bibliography.tex').read_text())
    if first_cites!=bibkeys:raise AssertionError(f'引用集合/首次顺序不一致：{first_cites} versus {bibkeys}')
    raw_checked=0
    for stage in [2,3,4]:
        for report in json.loads((ROOT/f'docs/stage{stage}_verification.json').read_text()):
            for name,digest in report['raw_sha256'].items():
                if hashlib.sha256((ROOT/'results/runs'/report['run']/'raw'/name).read_bytes()).hexdigest()!=digest:raise AssertionError('封存原始CSV变化：'+name)
                raw_checked+=1
    audit=json.loads((ROOT/'docs/v3_content_audit.json').read_text())
    for name,digest in audit['raw_csv_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise AssertionError('本轮审查后原始CSV变化：'+name)
    shutil.copy2(pdf,thesis/'draft.pdf')
    active_tex=[p for p in thesis.rglob('*.tex') if 'versions' not in p.relative_to(thesis).parts]
    record={'pages':pages,'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),
            'tex_chinese_characters':sum(len(re.findall(r'[\u4e00-\u9fff]',p.read_text())) for p in active_tex),
            'chapters':6,'appendices':1,'csv_generated_tables':len(list((thesis/'tables').glob('*.tex'))),'source_verified_figures':len(list((thesis/'figures').glob('*.pdf'))),'bibliography_entries':len(bibkeys),
            'citation_order_checked':True,'final_compile_no_undefined_missing_glyph_or_overfull':True,'reproduction_csv_unchanged':True,
            'historical_raw_files_hash_checked':raw_checked,'body_chinese_project_count':audit['body_chinese_total'],
            'school_current_template_obtained':False,'school_math_current_rules_confirmed':False,
            'execution':'XeLaTeX actually executed; Linux; school template pending'}
    (thesis/'build/final_verification.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(record,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
