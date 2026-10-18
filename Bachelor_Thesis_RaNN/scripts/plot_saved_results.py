"""只读封存CSV，在新目录重绘关键图；不重跑PDE，不修改原PNG/PDF。"""
import argparse,sys,csv,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    from experiments.common import ROOT,plt
    import numpy as np
    output=args.output or ROOT/'results/local_plots'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    output.mkdir(parents=True,exist_ok=False)
    paths=[ROOT/'results/raw/poisson_fdm.csv',ROOT/'results/runs/exp03_sampling_20261013/raw/sampling.csv']
    original={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    fdm=list(csv.DictReader(paths[0].open(encoding='utf-8-sig')))
    h=np.asarray([float(r['h']) for r in fdm]);e=np.asarray([float(r['relative_l2']) for r in fdm])
    fig,ax=plt.subplots(figsize=(6,4));ax.loglog(h,e,'o-',label='cloud FDM errors');ax.loglog(h,h*h*e[0]/h[0]**2,'--',label='O(h^2)');ax.set(xlabel='h',ylabel='Relative discrete L2',title='Poisson: n=15,31,63,127');ax.legend();ax.grid(alpha=.3,which='both')
    fig.text(.1,.01,'Source: results/raw/poisson_fdm.csv; saved data, no PDE rerun',fontsize=7)
    for ext in ['png','pdf']:fig.savefig(output/f'poisson_convergence.{ext}',dpi=300,bbox_inches='tight')
    plt.close(fig)
    rows=list(csv.DictReader(paths[1].open(encoding='utf-8-sig')));fig,axes=plt.subplots(1,3,figsize=(12,4))
    for ax,(b1,b2) in zip(axes,[(1,1),(1000,1),(1,1000)]):
        for index,method in enumerate(['A','B','C','D']):
            b=[r for r in rows if r['budget_mode']=='equations' and int(r['beta_left'])==b1 and int(r['beta_right'])==b2 and r['method']==method]
            values=[float(r['relative_l2']) for r in b];ax.scatter(index+np.linspace(-.1,.1,len(values)),values);ax.plot(index,np.mean(values),'k_',markersize=14)
        ax.set(xticks=range(4),xticklabels=['A','B','C','D'],yscale='log',ylabel='Independent relative L2',title=f'beta=({b1},{b2})');ax.grid(alpha=.25)
    fig.suptitle('Saved cloud results; 1232 equations, 64 features/side, scale=2, five seeds');fig.text(.1,.01,'Source: exp03_sampling_20261013/raw/sampling.csv; dots=all seeds, black=mean',fontsize=7);fig.tight_layout(rect=(0,.04,1,.94))
    for ext in ['png','pdf']:fig.savefig(output/f'sampling_equations.{ext}',dpi=300,bbox_inches='tight')
    plt.close(fig)
    if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in original.items()):raise AssertionError('原CSV发生变化')
    (output/'source_hashes.json').write_text(json.dumps(original,ensure_ascii=False,indent=2));print(output)


if __name__=='__main__':main()
