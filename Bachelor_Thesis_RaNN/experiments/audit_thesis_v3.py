"""审查v3正文规模、摘要、数据来源及归档材料；不等同学校审定。"""
from pathlib import Path
import re,json,hashlib
ROOT=Path(__file__).resolve().parents[1]


def expand(path,seen=None):
    seen=set() if seen is None else seen
    if path in seen:raise AssertionError('重复/循环输入：'+str(path))
    seen.add(path)
    text=path.read_text()
    def replace(match):
        p=ROOT/'thesis'/match.group(1)
        return expand(p.with_suffix('.tex'),seen)
    return re.sub(r'\\input\{([^}]+)\}',replace,text)


def main():
    sources=[]; counts={}
    for filename in ['01_introduction','02_preliminaries','03_method','04_sampling','05_results','06_conclusion']:
        text=expand(ROOT/'thesis/chapters'/f'{filename}.tex')
        text=re.sub(r'(?m)(?<!\\)%.*$','',text)
        # 只统计六章叙述中的汉字，剔除表/图、数学环境和引用，不计摘要、参考文献或附录。
        text=re.sub(r'\\begin\{(table|figure)\}.*?\\end\{\1\}','',text,flags=re.S)
        text=re.sub(r'\\begin\{(equation|align|tabular|verbatim)\}\*?.*?\\end\{\1\}','',text,flags=re.S)
        text=re.sub(r'\\\[.*?\\\]','',text,flags=re.S)
        text=re.sub(r'\$.*?\$','',text,flags=re.S)
        text=re.sub(r'\\(?:cite|ref|eqref|label|path)\{[^}]*\}','',text)
        counts[filename]=len(re.findall(r'[\u4e00-\u9fff]',text))
    main=(ROOT/'thesis/main.tex').read_text()
    chinese=main.split('\\chapter*{摘要}')[1].split('\\chapter*{Abstract}')[0].split('\\noindent')[0]
    english=main.split('\\chapter*{Abstract}')[1].split('\\noindent')[0]
    bib=(ROOT/'thesis/bibliography.tex').read_text()
    manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'results').rglob('*.csv')) if 'raw' in p.parts}
    result={'date':'2026-10-16','body_chinese_by_chapter':counts,'body_chinese_total':sum(counts.values()),'counting':'本项目保守汉字统计：六章展开输入后排除数学、表、图、摘要、引用、参考文献、附录；非学校Word计数认证','abstract_chinese':len(re.findall(r'[\u4e00-\u9fff]',chinese)),'abstract_english_words':len(re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*",english)),'bibliography_entries':len(re.findall(r'\\bibitem\{',bib)),'school_current_template_obtained':False,'school_math_current_rules_confirmed':False,'raw_csv_sha256':manifest}
    (ROOT/'docs/v3_content_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='raw_csv_sha256'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
