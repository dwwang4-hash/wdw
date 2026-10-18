"""从已保存CSV生成论文表格、复现报告和图表副本；不重新求解。"""
from .common import ROOT
from pathlib import Path
import csv,shutil,numpy as np


def read(run,name):return list(csv.DictReader((ROOT/'results/runs'/run/'raw'/name).open(encoding='utf-8-sig')))
def avg(rows,key):return float(np.mean([float(r[key]) for r in rows]))
def scientific(value):
    mantissa,exponent=f'{value:.3e}'.split('e')
    return '$'+mantissa+r'\times10^{'+str(int(exponent))+'}$'
def mean_std(rows,key):
    values=np.asarray([float(r[key]) for r in rows])
    if len(values)<2 or not np.all(np.isfinite(values)):raise ValueError('均值/标准差需要至少两条有限记录')
    exponent=int(np.floor(np.log10(abs(values.mean())))) if values.mean()!=0 else 0
    scale=10.**exponent
    return '$('+f'{values.mean()/scale:.3f}'+r'\pm'+f'{values.std(ddof=1)/scale:.3f}'+r')\times10^{'+str(exponent)+'}$'
def table(name,headers,rows):
    text=r'\begin{tabular}{'+'l'*len(headers)+r'}\toprule'+'\n'+' & '.join(headers)+r' \\ \midrule'+'\n'
    text+='\n'.join(' & '.join(row)+r' \\' for row in rows)
    text+='\n'+r'\bottomrule\end{tabular}'+'\n'
    (ROOT/'thesis/tables'/name).write_text(text,encoding='utf8')


def main():
    (ROOT/'thesis/tables').mkdir(exist_ok=True);(ROOT/'thesis/figures').mkdir(exist_ok=True)
    fdm=list(csv.DictReader((ROOT/'results/raw/poisson_fdm.csv').open()))
    table('fdm.tex',['每向内部点','相对离散误差','观测阶'],[[r['n'],scientific(float(r['relative_l2'])), '--' if r['observed_order']=='nan' else f"{float(r['observed_order']):.4f}"] for r in fdm])
    interface=read('exp02_interface_20261013','interface.csv');rows=[]
    for b1,b2 in [(1000,1),(1,1000)]:
        for scaling in ['raw','balanced']:
            b=[r for r in interface if r['variant']=='jumps' and int(r['beta_left'])==b1 and int(r['beta_right'])==b2 and r['scaling']==scaling]
            rows.append([f'({b1},{b2})',scaling,mean_std(b,'relative_l2'),mean_std(b,'interface_flux_rms')])
    table('interface.tex',[r'$(\beta_1,\beta_2)$','尺度',r'相对$L^2$：均值$\pm s$',r'通量RMS：均值$\pm s$'],rows)
    sampling=read('exp03_sampling_20261013','sampling.csv');rows=[]
    names={'A':'A','B':'B','C':'C','D':'D','D_minus_pde':'去PDE指标','D_minus_interface':'去界面指标'}
    for method in names:
        b=[r for r in sampling if r['budget_mode']=='points' and int(r['beta_left'])==1000 and int(r['beta_right'])==1 and r['method']==method]
        rows.append([names[method],mean_std(b,'relative_l2'),f"{avg(b,'total_seconds'):.4f}",f"{avg(b,'n_interface'):.1f}"])
    table('sampling.tex',['方法',r'相对$L^2$：均值$\pm s$','完整时间/秒','界面点均值'],rows)
    pairs=[];paired_records=[]
    for mode in ['points','equations']:
        for b1,b2 in [(1,1),(1000,1),(1,1000)]:
            for baseline in ['A','B','C']:
                ratios=[]
                for seed in [11,23,37,51,71]:
                    matched={r['method']:r for r in sampling if r['budget_mode']==mode and int(r['beta_left'])==b1 and int(r['beta_right'])==b2 and int(r['seed'])==seed}
                    ratio=float(matched['D']['relative_l2'])/float(matched[baseline]['relative_l2']);ratios.append(ratio)
                    paired_records.append({'budget':mode,'beta_left':b1,'beta_right':b2,'baseline':baseline,'seed':seed,'D_over_baseline':ratio})
                pairs.append(['点' if mode=='points' else '行',f'({b1},{b2})','D/'+baseline,f'{sum(x<1 for x in ratios)}/5',f'{np.median(ratios):.4f}'])
    table('paired_sampling.tex',['预算',r'$(\beta_1,\beta_2)$','配对','误差较小次数','比值中位数'],pairs)
    sensitivity=read('exp04_sensitivity_20261013','sensitivity.csv');rows=[]
    for count in [32,64,128,256]:
        b=[r for r in sensitivity if r['study']=='sensitivity' and r['parameter']=='count' and int(r['count'])==count and int(r['beta_left'])==1 and int(r['beta_right'])==1000]
        ranks=[int(r['data_rank']) for r in b]
        rows.append([str(count),scientific(avg(b,'relative_l2')),scientific(avg(b,'condition_raw')),f'{min(ranks)}--{max(ranks)}'])
    table('width.tex',['每侧特征','相对$L^2$均值','原始条件数均值','数据秩范围'],rows)
    controls=[];control_records=[]
    for b1,b2 in [(1,1),(1000,1),(1,1000)]:
        fixed=[r for r in sensitivity if r['study']=='proportion' and r['budget_mode']=='points' and int(r['beta_left'])==b1 and int(r['beta_right'])==b2 and int(r['n_interface'])==512]
        adaptive=[r for r in sampling if r['budget_mode']=='points' and int(r['beta_left'])==b1 and int(r['beta_right'])==b2 and r['method']=='D_minus_pde']
        for label,block in [('固定随机',fixed),('去PDE指标',adaptive)]:
            controls.append([f'({b1},{b2})',label,mean_std(block,'relative_l2'),f"{avg(block,'total_seconds'):.4f}"])
            for r in block:control_records.append({'beta_left':b1,'beta_right':b2,'method':label,'seed':r['seed'],'relative_l2':r['relative_l2'],'total_seconds':r['total_seconds'],'source_case_index':r['case_index']})
    table('allocation_control.tex',[r'$(\beta_1,\beta_2)$','同配额方法',r'相对$L^2$：均值$\pm s$','完整时间/秒'],controls)
    efficiency=read('exp08_efficiency_20261013','efficiency.csv');rows=[]
    for method in ['A','B','C','D','D_unused']:
        b=[r for r in efficiency if r['method']==method]
        rows.append([method.replace('_',r'\_'),mean_std(b,'relative_l2'),f"{avg(b,'total_seconds'):.4f}"])
    table('peaks.tex',['方法',r'相对$L^2$：均值$\pm s$','串行完整时间/秒'],rows)
    literal=read('exp09_literal_20261013','reproduction.csv');original=read('exp09_reproduction_20261013','reproduction.csv');rows=[]
    refs={(80,1000):1.18e-3,(160,1000):9.20e-6,(320,5000):3.17e-8}
    for count,total in refs:
        for derivative in ['fd','analytic']:
            b=[r for r in literal if int(r['count'])==count and int(r['total'])==total and r['derivative']==derivative]
            rows.append([f'{count}/{total}',derivative,scientific(refs[count,total]),mean_std(b,'relative_l2_gl20'),mean_std(b,'relative_l2_gl100')])
    table('reproduction.tex',['$m/N$','导数','原文表1',r'GL20：均值$\pm s$',r'GL100：均值$\pm s$'],rows)
    quadrature_rows=[];quadrature_records=[]
    for count,total in refs:
        block=[r for r in literal if int(r['count'])==count and int(r['total'])==total and r['derivative']=='fd']
        changes=[float(r['quadrature_relative_change']) for r in block]
        quadrature_rows.append([f'{count}/{total}',f'{100*np.median(changes):.2f}'+r'\%',f'{100*max(changes):.2f}'+r'\%',scientific(avg(block,'relative_l2_gl100'))])
        for r in block:quadrature_records.append({'count':count,'total':total,'seed':r['seed'],'case_index':r['case_index'],'quadrature_relative_change':r['quadrature_relative_change'],'relative_l2_gl20':r['relative_l2_gl20'],'relative_l2_gl100':r['relative_l2_gl100']})
    table('quadrature.tex',['$m/N$','积分差别中位数','积分差别最大值','GL100误差均值'],quadrature_rows)
    steps=[]
    for h in [.01,5e-4,1e-5,1e-6]:
        b=[r for r in original if r['study']=='fd_step' and float(r['h_second'])==h]
        steps.append([scientific(h),scientific(avg(b,'relative_l2_gl100')),scientific(avg(b,'validation_pde_rms'))])
    table('fd_steps.tex',['二阶差分步长','相对$L^2$均值','解析PDE残差RMS'],steps)
    links={'fdm_convergence':ROOT/'results/figures/poisson_fdm_convergence.pdf',
           'interface_contrast':ROOT/'results/runs/exp02_interface_20261013/figures/interface_contrast.pdf',
           'sampling':ROOT/'results/runs/exp03_sampling_20261013/figures/sampling_errors_points.pdf',
           'width':ROOT/'results/runs/exp04_sensitivity_20261013/figures/width_sensitivity.pdf',
           'peaks':ROOT/'results/runs/exp06_peaks_20261013/figures/peaks_budget_scale4.pdf',
           'perturbation':ROOT/'results/runs/exp07_stability_20261013/figures/rhs_perturbation.pdf',
           'reproduction':ROOT/'results/runs/exp09_literal_20261013/figures/flower_reproduction.pdf'}
    sources=[]
    for name,path in links.items():
        shutil.copy2(path,ROOT/'thesis/figures'/f'{name}.pdf');sources.append({'thesis_figure':name+'.pdf','source':str(path.relative_to(ROOT))})
    from .common import save_csv
    save_csv(ROOT/'thesis/asset_sources.csv',sources)
    save_csv(ROOT/'thesis/tables/paired_sampling_source.csv',paired_records)
    save_csv(ROOT/'thesis/tables/allocation_control_source.csv',control_records)
    save_csv(ROOT/'thesis/tables/quadrature_source.csv',quadrature_records)
    lines=['# 花形界面FD近似复现报告','','本轮110次预设复现/诊断，加按原文字面权重/偏置解释的60次追加。全部无运行异常，18项测试通过。与原文表1的数值存在明显差异，不能称严格复现，也不能据更低误差声称方法改进。','','## 最贴合文字的初始化','','权重U[−1.6,1.6]、偏置U[−.7,.7]，两网络相同。三组m/N、FD/解析导数、十公开种子，原表与两积分结果如下。','','|m/N|导数|原文表1|本项目GL20均值|本项目GL100均值|','|---|---|---|---|---|']
    for count,total in refs:
        for derivative in ['fd','analytic']:
            b=[r for r in literal if int(r['count'])==count and r['derivative']==derivative]
            lines.append(f"|{count}/{total}|{derivative}|{refs[count,total]:.6e}|{avg(b,'relative_l2_gl20'):.6e}|{avg(b,'relative_l2_gl100'):.6e}|")
    lines+=['','原先per_domain解释保留为额外假设对照；主复现采用更贴合文字的weight_bias，追加登记原因来自§4.2同类表述核对。原始110次配置和结果没有改写。PDF图1确认Ω₁在内、Ω₂在外。','','## FD步长与误差尺度','','在per_domain变体m160/N1000的五种子对照中，h₂=.01/5e−4/1e−5/1e−6的均值按表记录；小步长不一定更准确，h₂=1e−6时出现明显舍入放大。此为独立诊断变体，不能当作作者参数结论。','']
    lines += [f"- h₂={h:g}：GL100相对误差均值{avg([r for r in original if r['study']=='fd_step' and float(r['h_second'])==h],'relative_l2_gl100'):.6e}" for h in [.01,5e-4,1e-5,1e-6]]
    lines+=['','## 差异、核查与限制','','正确保留β通量，原文印刷矩阵疑似漏β仍待正式版/代码核对；中心差分作用于单侧基函数的光滑延拓，未跨界面对分片解差分。原文和本项目行权重γ50对应平方权重2500，无块样本数归一化。主界面按θ均匀，另有弧长对照；最小二乘gelsd float64 rcond1e−12，作者种子、dtype、阈值和确切采样机制未获代码。','',
              '比原表误差更低不等于更好的算法，可能来自初始化/精度/求解截断/采样实现等差异；目前无法把差异唯一归因。GL20与GL100在误差很小时可有明显相对差别，本项目同时保留，不只选较好积分值。正式版全文、PG全文缺口仍未解决。','',
              '新增文献查询：OpenAlex在本次请求中没有给出两篇期刊正式版的开放全文URL；这不是无公开PDF存在的证明。作者公开主页题头显示中文姓名“汪飞”，本论文统一用英文作者Fei Wang，以避免沿用原请求中“王飞”的未经核实中文对应。来源快照已保存。']
    (ROOT/'docs/reproduction_results.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print('Generated thesis tables, copied source figures and reproduction report')


if __name__=='__main__':main()
