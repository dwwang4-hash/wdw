"""供Windows下载后运行的CPU最小验证；新建run，不覆盖云端实验。迁移时不执行。"""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id');p.add_argument('--interface',action='store_true',help='额外执行原模型的单次B策略界面验证');args=p.parse_args()
    # 必须先设置线程/绘图环境，再加载NumPy；common使用项目内缓存。
    from experiments.common import create_run,save_config,save_csv
    from src.baseline_fdm import solve_poisson
    from src.pde_models import poisson_exact,StraightInterfaceProblem
    from src.metrics import errors
    import csv,json,math
    root=Path(__file__).resolve().parents[1]
    run=create_run('local_smoke',args.run_id)
    save_config(run,{'kind':'local migration smoke, same mathematical models','fdm_n':[15,31],'interface_requested':args.interface,'seed':11,'cloud_sources':['results/raw/poisson_fdm.csv','results/runs/exp03_sampling_20261013/raw/sampling.csv']})
    cloud={int(r['n']):r for r in csv.DictReader((root/'results/raw/poisson_fdm.csv').open(encoding='utf-8-sig'))}
    rows=[]
    for n in [15,31]:
        points,values,h,elapsed,residual=solve_poisson(n)
        metrics=errors(values,poisson_exact(points));reference=float(cloud[n]['relative_l2'])
        rows.append({'model':'poisson_fdm','n':n,'seed':'','h':h,**metrics,'solve_seconds':elapsed,'discrete_relative_residual':residual,'cloud_relative_l2':reference,'matches_cloud_error':math.isclose(metrics['relative_l2'],reference,rel_tol=1e-8,abs_tol=1e-12)})
    if args.interface:
        from src.adaptive_sampling import compare_sampling
        from src.local_rann import validation_metrics
        solution,trace,elapsed=compare_sampling(StraightInterfaceProblem(1000,1,'jumps'),'B',11,'equations')
        metrics=validation_metrics(solution)
        cloud_rows=list(csv.DictReader((root/'results/runs/exp03_sampling_20261013/raw/sampling.csv').open(encoding='utf-8-sig')))
        reference=next(r for r in cloud_rows if r['budget_mode']=='equations' and r['method']=='B' and int(r['seed'])==11 and int(r['beta_left'])==1000 and int(r['beta_right'])==1)
        rows.append({'model':'straight_interface_B','n':'','seed':11,**metrics,**solution.diagnostics,'total_seconds':elapsed,'cloud_relative_l2':float(reference['relative_l2']),'relative_error_ratio':metrics['relative_l2']/float(reference['relative_l2'])})
        save_csv(run/'raw/allocation_trace.csv',trace)
    save_csv(run/'raw/smoke.csv',rows)
    # 最小差分验证只检查可解释的同模型误差，不比较硬件时间，不把RaNN近奇异差异硬判失败。
    report={'run':str(run.relative_to(root)),'fdm_passed':all(r['matches_cloud_error'] for r in rows if r['model']=='poisson_fdm'),'interface_note':'optional one-case diagnostic, not five-seed full acceptance','rows':len(rows)}
    (run/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
    if not report['fdm_passed']:raise SystemExit(1)


if __name__=='__main__':main()
