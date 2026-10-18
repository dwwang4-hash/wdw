"""原文Example4.1近似复现，区别原表数值和本项目真实输出。"""
from .common import SEEDS,create_run,save_config,save_csv,summarize,save_plot,plt
from pathlib import Path
import argparse,csv,json,traceback
import numpy as np
from src.flower_interface import solve_flower,flower_metrics

TEN_SEEDS=SEEDS+[89,107,131,151,173]
REFERENCE={(80,1000):1.18e-3,(160,1000):9.20e-6,(320,5000):3.17e-8}


def cases(literal=False):
    result=[]
    base={'h_second':5e-4,'rcond':1e-12,'initialization':'per_domain','interface_sampling':'theta'}
    for count,total in REFERENCE:
        for derivative in ['fd','analytic']:
            result.extend([{**base,'study':'main','count':count,'total':total,'derivative':derivative,'seed':s} for s in TEN_SEEDS])
    if literal:
        return [{**c,'initialization':'weight_bias'} for c in result]
    result.extend([{**base,'study':'init_interpretation','count':320,'total':5000,'derivative':'fd','initialization':'weight_bias','seed':s} for s in TEN_SEEDS])
    for step in [.01,5e-4,1e-5,1e-6]:
        result.extend([{**base,'study':'fd_step','count':160,'total':1000,'derivative':'fd','h_second':step,'seed':s} for s in SEEDS])
    for cutoff in [1e-14,1e-12,1e-10]:
        result.extend([{**base,'study':'rcond','count':320,'total':5000,'derivative':'fd','rcond':cutoff,'seed':s} for s in SEEDS])
    result.extend([{**base,'study':'interface_measure','count':320,'total':5000,'derivative':'fd','interface_sampling':'arclength','seed':s} for s in SEEDS])
    return result


def plot_only(run):
    rows=list(csv.DictReader((run/'raw/reproduction.csv').open(encoding='utf-8-sig')))
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for derivative in ['fd','analytic']:
        xs=[];means=[];std=[]
        for count,total in REFERENCE:
            b=[r for r in rows if r['study']=='main' and r['derivative']==derivative and int(r['count'])==count and r['status']=='ok']
            vals=np.array([float(r['relative_l2_gl20']) for r in b]);xs.append(count);means.append(vals.mean());std.append(vals.std(ddof=1))
        axes[0].errorbar(xs,means,yerr=std,marker='o',capsize=3,label=f'{derivative},10 seeds')
    axes[0].plot([80,160,320],list(REFERENCE.values()),'k--o',label='Original Table1 (not our data)')
    axes[0].set(yscale='log',xlabel='Features per subdomain',ylabel='Relative L2 (20x20 GL)',title='Approximate reproduction, N=1000,1000,5000')
    axes[0].legend(fontsize=7);axes[0].grid(alpha=.3)
    b=[r for r in rows if r['study']=='fd_step' and r['status']=='ok']
    steps=sorted(set(float(r['h_second']) for r in b));means=[np.mean([float(r['relative_l2_gl100']) for r in b if float(r['h_second'])==h]) for h in steps]
    if steps:
        axes[1].loglog(steps,means,'o-');axes[1].set(xlabel='Second derivative FD step',ylabel='Relative L2 (100x100 GL)',title='m=160,N=1000; 5-seed means')
    else:
        axes[1].text(.1,.5,'Literal initialization follow-up:\nweights U[-1.6,1.6]\nbiases U[-0.7,0.7]\nFD/analytic paired, all 10 seeds',transform=axes[1].transAxes)
        axes[1].set_axis_off()
    axes[1].grid(alpha=.3,which='both');fig.text(.1,-.02,'Source: raw/reproduction.csv; beta=(1,10); FD first step=1e-6; row gamma=50',fontsize=8)
    save_plot(run,fig,'flower_reproduction')


def run_experiment(run_id=None,literal=False):
    run=create_run('exp09',run_id);setting=cases(literal)
    save_config(run,{'experiment':'exp09_reproduction','level':'approximate reproduction of arXiv2308.03087v1 Example4.1',
                     'reference_table':{'m80_N1000':1.18e-3,'m160_N1000':9.20e-6,'m320_N5000':3.17e-8},'cases':setting,
                     'beta':[1,10],'row_gamma':50,'h_first':1e-6,'dtype':'float64','solver':'gelsd; QR/SVD rcond differences retained',
                     'quadrature':[20,100],'interface_validation':2048,'random_streams':'features=[seed,side,900];points=[seed,910]',
                     'literal_followup':literal,
                     'limits':'author seeds,dtype,rcond and interface sampling not uniquely specified; initialization interpretation shown explicitly; not strict reproduction'})
    rows=[];coefficients={};log=(run/'run.log').open('w',encoding='utf8')
    for config in setting:
        row={'case_index':len(rows),**config,'status':'ok'}
        try:
            model,bases,coeff,info=solve_flower(**{k:v for k,v in config.items() if k!='study'})
            coarse=flower_metrics(model,bases,coeff,20);fine=flower_metrics(model,bases,coeff,100)
            row.update(info);row.update({k+'_gl100' if k=='relative_l2' else k:v for k,v in fine.items()})
            row['relative_l2_gl20']=coarse['relative_l2'];row['quadrature_relative_change']=abs(coarse['relative_l2']-fine['relative_l2'])/fine['relative_l2']
            row['original_table_error']=REFERENCE[(config['count'],config['total'])];row['error_over_original_gl20']=row['relative_l2_gl20']/row['original_table_error']
            if not all(np.isfinite(v) for v in row.values() if isinstance(v,(int,float))):raise FloatingPointError('指标非有限')
            coefficients[f'case_{len(rows)}']=coeff
        except Exception:
            row['status']='failed';row['error']=traceback.format_exc();log.write(row['error']+'\n')
        rows.append(row);log.write(json.dumps(row,ensure_ascii=False)+'\n');log.flush();save_csv(run/'raw/reproduction.csv',rows)
        if len(rows)%10==0:print('completed',len(rows),'/',len(setting),flush=True)
    log.close();np.savez_compressed(run/'raw/coefficients.npz',**coefficients)
    save_csv(run/'tables/reproduction_summary.csv',summarize(rows,['study','count','total','derivative','h_second','rcond','initialization','interface_sampling'],
             ['relative_l2_gl20','relative_l2_gl100','interface_value_rms','interface_flux_rms','validation_pde_rms','data_rank','condition_raw','total_seconds','quadrature_relative_change']))
    plot_only(run);print(run);print('runs',len(rows),'failed',sum(r['status']!='ok' for r in rows),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run-id');parser.add_argument('--plot-run');parser.add_argument('--literal-only',action='store_true');args=parser.parse_args()
    plot_only(Path(args.plot_run)) if args.plot_run else run_experiment(args.run_id,args.literal_only)
