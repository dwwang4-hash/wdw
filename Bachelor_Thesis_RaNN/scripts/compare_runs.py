"""只读CSV比较云端与本地的同参数结果；不比较硬件时间，不运行求解。"""
import argparse,csv,json,math
from pathlib import Path


def load(path,keys,metric):
    result={}
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if not set(keys+[metric]).issubset(reader.fieldnames or []):raise ValueError('CSV缺少比较键/指标：'+str(path))
        for row in reader:
            key=tuple(row[k] for k in keys)
            if key in result:raise ValueError('比较键不唯一，请加入额外参数列：'+str(key))
            result[key]=row
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--cloud',type=Path,required=True);p.add_argument('--local',type=Path,required=True);p.add_argument('--keys',default='budget_mode,beta_left,beta_right,method,seed');p.add_argument('--metric',default='relative_l2');p.add_argument('--rtol',type=float,default=.05);p.add_argument('--atol',type=float,default=1e-12);p.add_argument('--output',type=Path);args=p.parse_args()
    keys=args.keys.split(',');cloud=load(args.cloud,keys,args.metric);local=load(args.local,keys,args.metric);matched=sorted(cloud.keys()&local.keys());details=[]
    for key in matched:
        c,l=cloud[key],local[key]
        if c.get('status','ok')!='ok' or l.get('status','ok')!='ok':details.append({'key':key,'status':'failed_run_retained'});continue
        x,y=float(c[args.metric]),float(l[args.metric]);finite=math.isfinite(x) and math.isfinite(y)
        details.append({'key':key,'cloud':x,'local':y,'local_over_cloud':y/x if finite and x else None,'within_diagnostic_tolerance':finite and math.isclose(x,y,rel_tol=args.rtol,abs_tol=args.atol),'cloud_data_rank':c.get('data_rank'),'local_data_rank':l.get('data_rank')})
    report={'metric':args.metric,'keys':keys,'matched':len(matched),'missing_local':len(cloud.keys()-local.keys()),'extra_local':len(local.keys()-cloud.keys()),'outside_diagnostic_tolerance':sum(not r.get('within_diagnostic_tolerance',False) for r in details),'rtol':args.rtol,'atol':args.atol,'note':'tolerance is a user-adjustable diagnostic, not a PDE accuracy theorem; inspect singular cutoff/rank and aggregate seed results; hardware time is not compared','comparisons':details}
    if args.output:
        with args.output.open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k!='comparisons'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
