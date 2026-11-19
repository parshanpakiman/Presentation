import os
os.environ['MPLCONFIGDIR']='/private/tmp/psmd-mpl'
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
r=Path(__file__).resolve().parents[1];d=r/'assets/figures/continuous-demos/random-feature-sequence';d.mkdir(exist_ok=True)
x=np.linspace(-4,12,500);z=(x-4)/8;target=1+.5*np.sin(3*z)+.25*np.cos(7*z)+.6*np.maximum(z-.2,0)
rng=np.random.RandomState(17);pool=48
fourier=np.cos(rng.uniform(0,2*np.pi,pool)[None,:]+z[:,None]*rng.normal(0,5,pool)[None,:]);knots=rng.uniform(-1,1,pool);relu=np.maximum(0,z[:,None]-knots[None,:]);counts=[1,3,5,12,24,48];errors=[]
for i,n in enumerate(counts,1):
 fig,axes=plt.subplots(1,2,figsize=(11,3.3),sharex=True,sharey=True,constrained_layout=True);errs=[]
 for ax,features,name in zip(axes,[fourier,relu],['Fourier','ReLU']):
  design=np.column_stack([np.ones(len(x)),features[:,:n]]);w=np.linalg.lstsq(design,target,rcond=1e-12)[0];fit=design@w;error=np.sqrt(np.mean((fit-target)**2));errs.append(float(error))
  ax.plot(x,target,'--',color='#182c3e',lw=2,label='Illustrative target');ax.plot(x,fit,color='#c73838',lw=2,label='Feature approximation');ax.set(title=f'{name} · N = {n}',xlabel='state s',ylim=(.15,2.2));ax.text(.03,.95,f'RMSE = {error:.4f}',transform=ax.transAxes,va='top',fontsize=10);ax.grid(alpha=.2);ax.legend(loc='lower right',fontsize=9)
 axes[0].set_ylabel('function value');fig.savefig(d/f'{i:02d}.png',dpi=130,bbox_inches='tight');plt.close(fig);errors.append(errs)
assert np.all(np.diff(np.array(errors),axis=0)<1e-10)
print('Verified nonincreasing errors:',errors)
