"""模型示意和精确解剖面；从保存CSV重绘，不把示意图当数值解。"""
from .common import ROOT,save_csv,plt
from src.pde_models import StraightInterfaceProblem
from pathlib import Path
import numpy as np,csv,json,shutil


def main():
    folder=ROOT/'results/model_illustration_20261016';folder.mkdir(exist_ok=True)
    path=folder/'exact_profile.csv'
    if not path.exists():
        rows=[];problem=StraightInterfaceProblem(1000,1,'jumps')
        for side,(a,b) in enumerate([(0,.5),(.5,1)]):
            x=np.linspace(a,b,201);points=np.column_stack((x,np.full_like(x,.5)))
            u,f,grad=problem.data(points,side)
            rows.extend({'side':side,'x':float(t),'y':.5,'exact_u':float(v),'exact_ux':float(dx)} for t,v,dx in zip(x,u,grad[:,0]))
        save_csv(path,rows)
        (folder/'config.json').write_text(json.dumps({'kind':'manufactured model illustration, not a numerical solve','beta':[1000,1],'variant':'jumps','profile_y':.5,'source':'src/pde_models.py StraightInterfaceProblem','points_per_side':201},indent=2))
    rows=list(csv.DictReader(path.open(encoding='utf-8-sig')))
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    ax=axes[0];ax.fill_between([0,.5],0,1,color='#d9e9fa');ax.fill_between([.5,1],0,1,color='#fce2d0');ax.plot([.5,.5],[0,1],'k--',lw=2)
    ax.text(.15,.65,r'$\Omega_1,\ \beta_1=1000$');ax.text(.58,.65,r'$\Omega_2,\ \beta_2=1$')
    ax.annotate(r'$n=(1,0)$',xy=(.72,.4),xytext=(.38,.4),arrowprops={'arrowstyle':'->'})
    ax.text(.52,.85,r'$\Gamma$');ax.set(xlim=(0,1),ylim=(0,1),xlabel='x',ylabel='y',title='Geometry and fixed normal');ax.set_aspect('equal')
    for side,color in [(0,'#215d9c'),(1,'#b64e16')]:
        b=[r for r in rows if int(r['side'])==side];axes[1].plot([float(r['x']) for r in b],[float(r['exact_u']) for r in b],color=color,label=f'Exact side {side+1}')
    axes[1].axvline(.5,color='k',ls='--',lw=1);axes[1].set(xlabel='x',ylabel='Exact u(x,0.5)',title='Manufactured profile with nonzero jump');axes[1].legend();axes[1].grid(alpha=.25)
    fig.suptitle('Straight interface; beta=(1000,1); [u]=0.1 and [beta du/dn]=0.05 at y=0.5')
    fig.text(.08,.01,'Source: exact_profile.csv; analytic manufactured data, not a fitted network',fontsize=8);fig.tight_layout(rect=(0,.04,1,.93))
    for ext in ['pdf','png']:fig.savefig(folder/f'model_geometry.{ext}',dpi=300,bbox_inches='tight')
    plt.close(fig)
    shutil.copy2(folder/'model_geometry.pdf',ROOT/'thesis/figures/model_geometry.pdf')
    manifest=ROOT/'thesis/asset_sources.csv';records=list(csv.DictReader(manifest.open(encoding='utf-8-sig')))
    records=[r for r in records if r['thesis_figure']!='model_geometry.pdf']
    records.append({'thesis_figure':'model_geometry.pdf','source':str((folder/'model_geometry.pdf').relative_to(ROOT))});save_csv(manifest,records)
    print('Model illustration saved; profile CSV kept immutable; no numerical solve.')


if __name__=='__main__':main()
