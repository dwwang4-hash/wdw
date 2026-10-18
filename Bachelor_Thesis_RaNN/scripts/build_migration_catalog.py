"""只读历史科研文件构建实验/数据目录；不导入任何科研模块或运行实验。"""
from pathlib import Path
import ast,csv,json,struct,zipfile,collections
ROOT=Path(__file__).resolve().parents[1]


def save(name,rows,fields=None):
    path=ROOT/'migration'/name
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields or list(rows[0]));writer.writeheader();writer.writerows(rows)


def main():
    before=list(csv.DictReader((ROOT/'migration/source_before.csv').open(encoding='utf-8-sig')))
    research=[r for r in before if r['category']=='research_original']
    save('research_files_before.csv',research);save('runtime_exclusions.csv',[r for r in before if r['category']=='runtime_rebuildable'])
    data=[];arrays=[]
    for row in research:
        path=ROOT/row['path']
        if path.suffix=='.csv':
            with path.open(encoding='utf-8-sig',newline='') as f:r=csv.DictReader(f);items=list(r);fields=r.fieldnames or []
            data.append({'path':row['path'],'rows':len(items),'columns':json.dumps(fields,ensure_ascii=False),'status_counts':json.dumps(dict(collections.Counter(r['status'] for r in items)),ensure_ascii=False) if 'status' in fields else 'no_status_column','sha256':row['sha256']})
        if path.suffix=='.npz':
            with zipfile.ZipFile(path) as z:
                for entry in z.namelist():
                    with z.open(entry) as f:
                        magic=f.read(8)
                        if magic[:6]!=b'\x93NUMPY':raise ValueError('Non-NPY inside NPZ')
                        size=struct.unpack('<H' if magic[6]==1 else '<I',f.read(2 if magic[6]==1 else 4))[0]
                        if size>1048576:raise ValueError('NPY header too large')
                        header=ast.literal_eval(f.read(size).decode('latin1'))
                    arrays.append({'archive':row['path'],'array':entry,'shape':str(header['shape']),'dtype':str(header['descr']),'fortran_order':header['fortran_order']})
    save('csv_catalog.csv',data);save('npz_array_catalog.csv',arrays)
    catalog=[];log=(ROOT/'docs/research_log.md').read_text();mapping={'exp02_interface':'interface.csv','exp03_sampling':'sampling.csv','exp04_sensitivity':'sensitivity.csv','exp06_peaks':'peaks.csv','exp07_stability':'stability.csv','exp08_efficiency':'efficiency.csv','exp09_reproduction':'reproduction.csv'}
    for folder in sorted((ROOT/'results/runs').iterdir()):
        if not (folder/'config.json').exists():continue
        cfg=json.loads((folder/'config.json').read_text());experiment=cfg['experiment'];module='exp09_reproduction' if folder.name.startswith('exp09') else next(k for k in mapping if folder.name.startswith(k+'_'))
        primary=folder/'raw'/mapping[module]
        if not primary.exists():
            candidates=[p for p in (folder/'raw').glob('*.csv') if 'perturb' in p.name]
            if module=='exp07_stability' and len(candidates)==1:primary=candidates[0]
            else:raise FileNotFoundError(primary)
        with primary.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
        flags=' --literal-only' if 'literal' in folder.name else ''
        cmd=f'python -m experiments.{module}{flags} --run-id {folder.name}'
        seeds=cfg.get('seeds') or sorted({int(r['seed']) for r in rows if r.get('seed')})
        catalog.append({'run_id':folder.name,'module':'experiments.'+module,'code_path':'experiments/'+module+'.py','config_path':str((folder/'config.json').relative_to(ROOT)),'raw_primary':str(primary.relative_to(ROOT)),'rows':len(rows),'status_counts':dict(collections.Counter(r.get('status','not_recorded') for r in rows)),'seeds':seeds,'original_command':cmd,'command_evidence':'docs/research_log.md records this module/run-id; executable prefix normalized, no complete shell transcript','run_id_mentioned_in_log':folder.name in log,'all_result_files':[r['path'] for r in research if r['path'].startswith(str(folder.relative_to(ROOT))+'/')],'config':cfg})
    (ROOT/'migration/experiment_catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2))
    save('experiment_index.csv',[{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items() if k not in ['config','all_result_files']} for row in catalog])
    commands=[{'research_log_line':i,'text':line} for i,line in enumerate(log.splitlines(),1) if '执行' in line or '运行：' in line]
    (ROOT/'migration/command_evidence.json').write_text(json.dumps(commands,ensure_ascii=False,indent=2))
    summary={'research_files_before':len(research),'research_bytes':sum(int(r['bytes']) for r in research),'runtime_files_excluded':len(before)-len(research),'file_extensions':dict(collections.Counter(Path(r['path']).suffix.lower() or '[no_extension]' for r in research)),'csv_files':len(data),'npz_files':len({r['archive'] for r in arrays}),'npz_arrays':len(arrays),'run_directories':len(catalog),'largest_research_files':[{'path':r['path'],'bytes':int(r['bytes'])} for r in sorted(research,key=lambda r:int(r['bytes']),reverse=True)[:10]],'windows_invalid_paths':[r['path'] for r in research if any(any(c in part for c in '<>:"|?*') or part.endswith((' ','.')) or part.upper().split('.')[0] in {'CON','PRN','AUX','NUL','COM1','LPT1'} for part in Path(r['path']).parts)],'longest_research_relative_path':max(len(r['path']) for r in research)}
    (ROOT/'migration/catalog_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
