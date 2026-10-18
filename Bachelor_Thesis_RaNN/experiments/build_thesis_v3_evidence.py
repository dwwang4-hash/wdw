"""从封存CSV整理v3证据，不求解、不覆盖原始实验。"""
from .common import ROOT,save_csv
from .build_thesis_assets import read,avg,scientific,mean_std,table
import json,hashlib


def main():
    rows=read('exp03_sampling_20261013','sampling.csv')
    if len(rows)!=180 or any(r['status']!='ok' for r in rows):
        raise AssertionError('主实验运行数量或状态变化')
    detail=[];sources=[]
    for b1,b2 in [(1,1),(1000,1),(1,1000)]:
        for method in ['A','B','C','D']:
            block=[r for r in rows if r['budget_mode']=='equations' and int(r['beta_left'])==b1 and int(r['beta_right'])==b2 and r['method']==method]
            if sorted(int(r['seed']) for r in block)!=[11,23,37,51,71]:raise AssertionError('配对种子不完整')
            if any(int(r['n_equations'])!=1232 for r in block):raise AssertionError('行预算不等')
            detail.append([f'({b1},{b2})',method,scientific(avg(block,'max_abs')),scientific(avg(block,'validation_pde_normalized_side1')),scientific(avg(block,'validation_pde_normalized_side2')),scientific(avg(block,'interface_value_rms')),scientific(avg(block,'interface_flux_rms'))])
            sources.extend(block)
    table('sampling_multimetric.tex',[r'$(\beta_1,\beta_2)$','方法',r'$E_\infty$',r'$R_1/\beta_1$',r'$R_2/\beta_2$',r'$J_u$',r'$J_q$'],detail)
    ranks=[];allocation=[]
    for b1,b2 in [(1,1),(1000,1),(1,1000)]:
        for method in ['A','B','C','D']:
            block=[r for r in sources if int(r['beta_left'])==b1 and int(r['beta_right'])==b2 and r['method']==method]
            ranks.append([f'({b1},{b2})',method,scientific(avg(block,'condition_raw')),f"{min(int(r['data_rank']) for r in block)}--{max(int(r['data_rank']) for r in block)}",f"{avg(block,'n_points'):.1f}",f"{avg(block,'n_interface'):.1f}",f"{avg(block,'total_seconds'):.4f}"])
    table('sampling_rank_cost.tex',[r'$(\beta_1,\beta_2)$','方法',r'$\kappa$均值','有效秩','物理点均值','界面点均值','时间/秒'],ranks)
    traces=read('exp03_sampling_20261013','allocation_trace.csv')
    for mode in ['points','equations']:
        for iteration in range(4):
            block=[r for r in traces if r['budget_mode']==mode and r['method']=='D' and int(r['beta_left'])==1000 and int(r['beta_right'])==1 and int(r['iteration'])==iteration]
            if len(block)!=5:raise AssertionError('轨迹种子不完整')
            allocation.append(['点' if mode=='points' else '行',str(iteration)]+[f'{avg(block,k):.1f}' for k in ['n_left','n_right','n_interface']])
    table('allocation_history.tex',['预算','轮次','左内部均值','右内部均值','界面均值'],allocation)
    save_csv(ROOT/'thesis/tables/v3_multimetric_source.csv',sources)
    raw=ROOT/'results/runs/exp03_sampling_20261013/raw/sampling.csv'
    result={'source':str(raw.relative_to(ROOT)),'sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'source_runs':len(rows),'multimetric_runs':len(sources),'groups':12,'seeds_checked':[11,23,37,51,71],'equations_checked':1232,'new_numerical_solves':0}
    (ROOT/'docs/v3_evidence_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
