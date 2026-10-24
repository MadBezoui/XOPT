"""Deterministic tables and vector figures from retained JSONL observations."""
from pathlib import Path
import json, collections, hashlib, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parents[2];RES=ROOT/'experiments/results';FIG=ROOT/'article/figures';TAB=ROOT/'article/tables'
FIG.mkdir(parents=True,exist_ok=True);TAB.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':8,'axes.labelsize':8,'legend.fontsize':6.5,'xtick.labelsize':7,'ytick.labelsize':7,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'savefig.bbox':'tight','savefig.pad_inches':0.02})
COL=['#0072B2','#D55E00','#009E73','#CC79A7']
profiles=['correctness','main','sensitivity','scale','capacity','long','multifoil']
raw={p:[json.loads(l) for l in (RES/(p+'.jsonl')).read_text().splitlines()] for p in profiles if (RES/(p+'.jsonl')).exists()}
rows=[]
for p,records in raw.items():
 for a in records:
  m=a['instance'];j=a['job'];r=a.get('result',a.get('menu',{}))
  rows.append(dict(profile=p,id=m['id'],family=m['family'],I=m['I'],T=m['T'],seed=m['seed'],mode=j['mode'],method=j['method'],K=j['K'],epsilon=j['epsilon'],margin=j['margin'],status=a['status'],objective=r.get('objective'),seconds=r.get('seconds'),iterations=r.get('iterations'),cuts=r.get('cuts'),periods=r.get('changed_periods'),parameters=r.get('changed_parameters'),lower_bound=r.get('lower_bound'),valid=a.get('verification',{}).get('valid'),key=a['key']))
df=pd.DataFrame(rows);df.to_csv(RES/'all_results.csv',index=False)
assert not (df.valid==False).any(),'Independent verification failure'
correct=df[df.profile=='correctness'];pairs=correct.pivot(index=['id','mode'],columns='method',values=['status','objective'])
assert (pairs['status']['ccg']==pairs['status']['enumerate']).all()
err=(pairs['objective']['ccg']-pairs['objective']['enumerate']).abs().max()
assert err<1e-5
main=df[df.profile=='main']; paired=main[main.status=='SOLVER_VALIDATED'].pivot(index=['id','mode','family','seed'],columns='method',values='seconds').dropna()
ratio=paired['multicut']/paired['ccg']
summary={'runs':len(df),'status_counts':dict(df.status.value_counts()),'valid_explanations':int((df.valid==True).sum()),'correctness_pairs':len(pairs),'correctness_max_objective_difference':err,'main_paired_count':len(paired),'main_multicut_over_ccg_median':float(ratio.median()),'main_multicut_over_ccg_q1':float(ratio.quantile(.25)),'main_multicut_over_ccg_q3':float(ratio.quantile(.75))}
for p in profiles:
 z=df[df.profile==p];summary[p]={'n':len(z),'counts':dict(z.status.value_counts()),'total_seconds':float(z.seconds.sum())}

def save(fig,name):
 fig.savefig(FIG/(name+'.pdf'));fig.savefig(FIG/(name+'.png'),dpi=220);plt.close(fig)
def table(path,columns,lines,align):
 text='\\begin{tabular}{'+align+'}\n\\toprule\n'+' & '.join(columns)+' \\\\\n\\midrule\n'
 text+='\n'.join(' & '.join(map(str,row))+' \\\\' for row in lines)+'\n\\bottomrule\n\\end{tabular}\n'
 (TAB/path).write_text(text)
lines=[]
for (fam,method),z in main.groupby(['family','method']):
 good=z[z.status=='SOLVER_VALIDATED'];lines.append([fam.capitalize(),{'ccg':'CCG','multicut':'Multicut'}[method],len(z),len(good),sum(z.status=='SOLVER_INFEASIBLE'),f'{z.seconds.median():.3f}',f'{good.iterations.median():.1f}',f'{good.cuts.median():.1f}'])
table('main.tex',['Family','Method','$n$','Valid.','Inf.','Median s','Iter.','Cuts'],lines,'llrrrrrr')
lines=[]
for (fam,I,T),z in df[df.profile.isin(['scale','long'])].groupby(['family','I','T']):
 lines.append([fam.capitalize(),f'{I} / {T}',len(z),sum(z.status=='SOLVER_VALIDATED'),sum(z.status=='TIME_LIMIT'),f'{z.seconds.median():.2f}'])
table('scale.tex',['Family','$I/T$','$n$','Valid.','Unres.','Median s'],lines,'llrrrr')
# Match the instance set across every K before comparing intervention costs.
sensitivity=df[df.profile=='sensitivity'].copy()
common_ids={}
for (fam,mode,eps),z in sensitivity.groupby(['family','mode','epsilon']):
 status=z.pivot(index='id',columns='K',values='status')
 common_ids[(fam,mode,eps)]=set(status.index[(status=='SOLVER_VALIDATED').all(axis=1)])
lines=[]
paired_sensitivity=[]
for (fam,K,mode,eps),z in sensitivity.groupby(['family','K','mode','epsilon']):
 good=z[z.status=='SOLVER_VALIDATED'];paired_z=good[good.id.isin(common_ids[(fam,mode,eps)])]
 regime=f'$\\varepsilon={eps:g}$' if eps else ('Strong' if mode=='strong' else 'Weak')
 lines.append([fam.capitalize(),K,regime,f'{len(good)}/{len(z)}',len(paired_z),f'{paired_z.objective.median():.3f}',f'{paired_z.periods.median():.1f}'])
 paired_sensitivity.append({'family':fam,'K':int(K),'mode':mode,'epsilon':float(eps),'attempted':len(z),'validated':len(good),'paired_n':len(paired_z),'paired_median':float(paired_z.objective.median()),'conditional_median':float(good.objective.median())})
table('sensitivity.tex',['Family','$K$','Semantics','Valid.','Paired $n$','Paired med.','Periods'],lines,'lrllrrr')
(RES/'paired_sensitivity.json').write_text(json.dumps(paired_sensitivity,indent=2))
lines=[]
for fam,z in df[df.profile=='capacity'].groupby('family'):
 records=[a for a in raw['capacity'] if a['instance']['family']==fam]
 changed=sum(a['menu']['scenario']>1 for a in records)
 lines.append([fam.capitalize(),len(z),sum(z.status=='SOLVER_VALIDATED'),changed,f'{z.seconds.median():.3f}'])
table('capacity.tex',['Family','$n$','Valid.','Expanded winner','Median s'],lines,'lrrrr')
# Data profiles: raw observed series, normalized by stated calibration.
fig,axes=plt.subplots(1,2,figsize=(4.6,2.2),constrained_layout=True)
for ax,fam,filename,letter in zip(axes,['Retail','NHS'],['retail_weekly.csv','nhs_monthly.csv'],['(a)','(b)']):
 data=pd.read_csv(ROOT/'data/processed'/filename,dtype={'series':str})
 for code in data.series.unique()[:5]:
  z=data[data.series==code];v=z.demand.to_numpy();den=np.mean(v[:13]) if fam=='Retail' else v[0];ax.plot(z.period,v/max(den,1),lw=1,label=code)
 ax.set(xlabel='Week' if fam=='Retail' else 'Month',ylabel='Normalized volume');ax.set_title(letter,loc='left')
 if fam!='Retail':ax.set_xticks(range(1,13))
save(fig,'data_profiles')
# Paired runtime, preserving all jointly validated comparisons.
fig,axes=plt.subplots(1,2,figsize=(4.6,2.4),constrained_layout=True)
for c,fam in zip(COL,['retail','hospital']):
 z=paired.reset_index();z=z[z.family==fam];axes[0].scatter(z.ccg,z.multicut,s=17,label=fam.capitalize(),color=c,alpha=.75,marker='o' if fam=='retail' else '^')
lims=[max(1e-4,min(paired.min())*.7),max(paired.max())*1.3];axes[0].plot(lims,lims,'k--',lw=.8);axes[0].set(xscale='log',yscale='log',xlim=lims,ylim=lims,xlabel='CCG seconds',ylabel='Multicut seconds');axes[0].legend(frameon=False,fontsize=7)
for c,method in zip(COL,['ccg','multicut']):
 z=main[(main.method==method)&(main.status=='SOLVER_VALIDATED')].seconds.sort_values().to_numpy();axes[1].step(z,np.arange(1,len(z)+1)/len(main[main.method==method]),where='post',label={'ccg':'CCG','multicut':'Multicut'}[method],color=c,ls='-' if method=='ccg' else '--')
axes[1].set(xscale='log',xlabel='Seconds',ylabel='Fraction validated',ylim=(0,1));axes[1].legend(frameon=False,fontsize=6.5)
axes[0].set_title('(a)',loc='left');axes[1].set_title('(b)',loc='left')
save(fig,'runtime')
fig,axes=plt.subplots(2,2,figsize=(4.6,3.9),constrained_layout=True,gridspec_kw={'height_ratios':[2,1]})
for col,fam in enumerate(['retail','hospital']):
 ax=axes[0,col];coverage=axes[1,col]
 for c,(mode,eps,label) in zip(COL,[('weak',0.,'Weak'),('weak',.1,'Approx., $\\varepsilon$=0.1'),('strong',0.,'Strong, $\\gamma$=0.1')]):
  z=sensitivity[(sensitivity.family==fam)&(sensitivity['mode']==mode)&(sensitivity.epsilon==eps)]
  common=common_ids[(fam,mode,eps)]
  zz=z[z.id.isin(common)].groupby('K').objective
  med=zz.median();ax.plot(med.index,med,marker={'Weak':'o'}.get(label,'s' if mode=='weak' else '^'),color=c,label=f'{label} (n={len(common)})')
 lo,hi=min(l.get_ydata().min() for l in ax.get_lines()),max(l.get_ydata().max() for l in ax.get_lines());span=max(hi-lo,1e-3);ax.set_ylim(lo-.08*span,hi+.8*span)
 counts=sensitivity[(sensitivity.family==fam)&(sensitivity['mode']=='weak')&(sensitivity.epsilon==0)].groupby('K').status.apply(lambda x:sum(x=='SOLVER_VALIDATED'))
 coverage.plot(counts.index,counts,'ko-',label='All three semantics')
 coverage.set(xlabel='Period budget $K_T$',ylabel='Validated / 4',xticks=[1,2,6],yticks=[0,1,2,3,4],ylim=(-.15,4.3))
 coverage.legend(fontsize=6.5,frameon=False);coverage.set_title(['(c)','(d)'][col],loc='left')
 ax.set(ylabel='Median cost (paired)',xticks=[1,2,6]);ax.set_title(['(a)','(b)'][col],loc='left');ax.legend(fontsize=6.5,frameon=False,loc='upper right')
save(fig,'sparsity')
# Transparent illustrative example, deterministic first validated nontrivial strong retail case.
cases=sorted([a for a in raw['main'] if a['status']=='SOLVER_VALIDATED' and a['job']['method']=='ccg' and a['job']['mode']=='strong' and a['instance']['family']=='retail' and a['instance']['I']==2],key=lambda a:a['key'])
a=cases[0];m=a['instance'];r=a['result'];I,T=m['I'],m['T'];mat=lambda x:np.array(x).reshape((I,T),order='F')
fig,axes=plt.subplots(3,1,figsize=(4.6,4.4),constrained_layout=True)
for i in range(I):axes[0].plot(range(1,T+1),mat(m['demand'])[i],marker='o',label='Item '+str(i+1),color=COL[i])
axes[0].set(ylabel='Normalized demand');axes[0].legend(fontsize=6.5,frameon=False);axes[0].set_title('(a)',loc='left')
for i in range(I):
 axes[1].step(range(1,T+1),mat(a['nominal_y'])[i]+i*1.4,where='mid',color=COL[i],ls='--',label=f'Nominal {i+1}')
 axes[1].step(range(1,T+1),mat(r['y'])[i]+i*1.4,where='mid',color=COL[i],label=f'Counterfactual {i+1}')
axes[1].set(ylabel='Setup (offset by item)',yticks=[0,1,1.4,2.4]);axes[1].legend(ncol=2,fontsize=6.5,frameon=False);axes[1].set_title('(b)',loc='left')
im=axes[2].imshow(mat(r['delta'])/mat(m['fixed']),aspect='auto',cmap='RdBu_r',vmin=-.8,vmax=.8,extent=[.5,T+.5,I+.5,.5]);axes[2].set(ylabel='Item',xlabel='Week in instance',yticks=range(1,I+1));axes[2].set_title('(c)',loc='left');fig.colorbar(im,ax=axes[2],label='Relative setup-cost edit',shrink=.8)
save(fig,'case_study');summary['case']={'id':m['id'],'foil':a['foil'],'objective':r['objective'],'periods':r['changed_periods'],'max_relative_edit':float(np.max(np.abs(mat(r['delta'])/mat(m['fixed']))))}
# A vector process diagram derived from the implemented method.
fig,ax=plt.subplots(figsize=(7.2,2.1));ax.set(xlim=(0,10),ylim=(0,2));ax.axis('off')
texts=[('Observe','Public demand series\nExplicit model assumptions'),('Propose','Partial binary foil\nSparse cost/capacity edits'),('Validate','Full-horizon MILP oracle\nBounds and stability radius')]
for k,(title,body) in enumerate(texts):
 x=.1+3.4*k;ax.add_patch(FancyBboxPatch((x,.35),2.9,1.3,boxstyle='round,pad=0.08',facecolor='#edf4f7',edgecolor=COL[k],lw=1.4));ax.text(x+1.45,1.32,title,ha='center',weight='bold',color=COL[k]);ax.text(x+1.45,.85,body,ha='center',va='center',fontsize=8)
 if k<2:ax.annotate('',xy=(x+3.3,1),xytext=(x+2.95,1),arrowprops={'arrowstyle':'->','color':'#333333'})
save(fig,'graphical_abstract')
if (RES/'robustness.jsonl').exists():
 rr=[json.loads(l) for l in (RES/'robustness.jsonl').read_text().splitlines()];z=pd.DataFrame([{'mode':a['mode'],'family':a['family'],**a['radius']} for a in rr]);z.to_csv(RES/'robustness.csv',index=False)
 fig,axes=plt.subplots(1,2,figsize=(4.6,2.3),constrained_layout=True)
 for ax,fam,letter in zip(axes,['retail','hospital'],['(a)','(b)']):
  for i,mode in enumerate(['weak','strong']):
   vals=z[(z.family==fam)&(z['mode']==mode)]['lower'].to_numpy();ax.scatter(np.full(len(vals),i)+np.linspace(-.12,.12,len(vals)),vals*100,color=COL[i],s=22,alpha=.7)
  ax.set(xticks=[0,1],xticklabels=['Weak','Strong'],ylabel='Relative cost radius (%)');ax.set_title(letter,loc='left')
 save(fig,'robustness');summary['robustness']=z.groupby('mode')['lower'].agg(['count','median','min','max']).to_dict('index')
if (RES/'single_lever.jsonl').exists():
 sl=[json.loads(l) for l in (RES/'single_lever.jsonl').read_text().splitlines()]
 lines=[]
 for profile in ['main','scale','long']:
  z=[a for a in sl if a['profile']==profile];g=[a for a in z if a['status']=='RESTRICTED_SOLVER_OPTIMAL']
  assert all(a['verification']['valid'] for a in g)
  lines.append([profile.capitalize(),len(z),len(g),sum(a['status']=='EDIT_BOUND_EXCEEDED' for a in z),f"{np.median([a['optimization_seconds'] for a in g]):.3f}"])
 table('single_lever.tex',['Study','$n$','Valid.','Edit bound','Median s'],lines,'lrrrr')
 good=[a for a in sl if a['status']=='RESTRICTED_SOLVER_OPTIMAL' and a['global_status']=='SOLVER_VALIDATED']
 summary['single_lever']={'n':len(sl),'validated':sum(a['status']=='RESTRICTED_SOLVER_OPTIMAL' for a in sl),'paired':len(good),'global_improves':sum(a['objective']-a['global_objective']>1e-5 for a in good),'max_absolute_improvement':max(a['objective']-a['global_objective'] for a in good)}
if 'multifoil' in raw:
 lines=[]
 for (fam,mode),z in df[df.profile=='multifoil'].groupby(['family','mode']):
  lines.append([fam.capitalize(),mode.capitalize(),len(z),sum(z.status=='SOLVER_VALIDATED'),sum(z.status=='SOLVER_INFEASIBLE'),sum(z.status=='TIME_LIMIT'),f'{z.seconds.median():.3f}'])
 table('multifoil.tex',['Family','Semantics','$n$','Valid.','Inf.','Unres.','Median s'],lines,'llrrrrr')
(RES/'summary.json').write_text(json.dumps(summary,indent=2,default=lambda x:x.item()))
macros={'TotalRuns':len(df),'ValidatedRuns':sum(df.status=='SOLVER_VALIDATED'),'InfeasibleRuns':sum(df.status=='SOLVER_INFEASIBLE'),'TimeoutRuns':sum(df.status=='TIME_LIMIT'),'PairedCount':len(paired),'MedianRatio':f'{ratio.median():.2f}','RatioQone':f'{ratio.quantile(.25):.2f}','RatioQthree':f'{ratio.quantile(.75):.2f}'}
macros['CorrectnessMaxDiff']=f'{err:.2e}'
if 'single_lever' in summary:
 single=summary['single_lever']
 macros.update({'SingleRuns':len(sl),'SingleValidated':single['validated'],
   'SingleBoundExceeded':sum(a['status']=='EDIT_BOUND_EXCEEDED' for a in sl),
   'SinglePhysicallyInfeasible':sum(a['status']=='FOIL_INFEASIBLE' for a in sl),
   'SinglePaired':single['paired'],'GlobalImproves':single['global_improves'],
   'MaxGlobalImprovement':f"{single['max_absolute_improvement']:.4f}",
   'LongBaselineValidated':sum(a['profile']=='long' and a['status']=='RESTRICTED_SOLVER_OPTIMAL' for a in sl),
   'LongGlobalValidated':sum((df.profile=='long')&(df.status=='SOLVER_VALIDATED')),
   'LongTimeout':sum((df.profile=='long')&(df.status=='TIME_LIMIT'))})
if 'robustness' in summary:
 strong=summary['robustness']['strong'];weak=summary['robustness']['weak']
 macros.update({'WeakRadiusCount':int(weak['count']),'StrongRadiusCount':int(strong['count']),
   'StrongRadiusMin':f"{strong['min']*100:.3f}",'StrongRadiusMax':f"{strong['max']*100:.3f}",
   'StrongRadiusMedian':f"{strong['median']*100:.3f}"})
(TAB/'numbers.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+str(v)+'}' for k,v in macros.items())+'\n')
print(json.dumps(summary,indent=2,default=lambda x:x.item()))
