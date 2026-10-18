"""Audit and summarize the prospectively specified supplementary experiments."""
from pathlib import Path
import collections
import hashlib
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
RES, TAB, FIG = (ROOT / p for p in ['experiments/results', 'article/tables', 'article/figures'])
EXPECTED = {'extended': 90, 'compound': 128, 'capacity_stress': 32, 'timing_repairs': 6}
raw = {p: [json.loads(l) for l in (RES / f'revision_{p}.jsonl').read_text().splitlines()] for p in EXPECTED}
rows = []
for profile, records in raw.items():
    assert len(records) == EXPECTED[profile], (profile, len(records))
    assert len({a['key'] for a in records}) == len(records)
    for a in records:
        for path, expected in a['source_sha256'].items():
            assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
        o = a.get('output', {})
        ub, lb = o.get('upper_bound'), o.get('lower_bound')
        feasible = ub is not None
        optimal = o.get('status') == 'SOLVER_VALIDATED'
        if feasible:
            assert o['verification']['valid'] is True, a['key']
            assert o['verification']['exact_certificate'] is False
            assert abs(o['result']['objective'] - ub) < 1e-8
            assert lb is not None and lb <= ub + 1e-5, a['key']
            assert abs(o['absolute_gap'] - max(0., ub-lb)) < 1e-8
            assert 0 <= o['first_feasible_seconds'] <= o['seconds'] + 1e-6
        if optimal:
            assert feasible and ub-lb <= 1e-5
        if o.get('status') == 'SOLVER_INFEASIBLE':
            assert not feasible
        m = a['instance']
        rows.append(dict(profile=profile, key=a['key'], id=m['id'], family=m['family'], I=m['I'], T=m['T'], seed=m['seed'],
            mode=a['mode'], method=a.get('method', 'cold' if profile=='compound' else 'menu'), K=a.get('K'), budget=a.get('budget'),
            literals=a.get('literal_count', len(a.get('foil', []))), factor=a.get('factor'),
            status=o.get('status', a.get('status')), feasible=feasible, optimal=optimal, upper_bound=ub, lower_bound=lb,
            absolute_gap=o.get('absolute_gap'), relative_gap=o.get('relative_gap'), seconds=o.get('seconds'),
            first_seconds=o.get('first_feasible_seconds'), periods=o.get('result', {}).get('changed_periods') if feasible else None))
all_df = pd.DataFrame(rows)
all_df.to_csv(RES / 'revision_all_attempts.csv', index=False)
repair_keys = {a['key'] for a in raw['timing_repairs']}
original_lines = {json.loads(l)['key']: l for l in (RES/'revision_extended.jsonl').read_text().splitlines()}
for a in raw['timing_repairs']:
    assert a['timing_rule_passed'], 'Interrupted repeat: retain it and report timing unresolved'
    assert a['original_record_sha256'] == hashlib.sha256(original_lines[a['key']].encode()).hexdigest()
    assert a['original_file_sha256'] == hashlib.sha256((RES/'revision_extended.jsonl').read_bytes()).hexdigest()
df = pd.concat([all_df[(all_df.profile!='timing_repairs') & ~((all_df.profile=='extended') & all_df.key.isin(repair_keys))],
                all_df[all_df.profile=='timing_repairs'].assign(profile='extended')],ignore_index=True)
assert len(df)==250
df.to_csv(RES / 'revision_results.csv', index=False)

def med(x, fmt='.3f'):
    x = pd.Series(x).dropna()
    return format(x.median(), fmt) if len(x) else '--'

def table(name, columns, lines, align):
    text = '\\begin{tabular}{'+align+'}\n\\toprule\n'+' & '.join(columns)+' \\\\\n\\midrule\n'
    text += '\n'.join(' & '.join(map(str, row))+' \\\\' for row in lines)+'\n\\bottomrule\n\\end{tabular}\n'
    (TAB / name).write_text(text)

summary = {'protocol': 'experiments/docs/revision_protocol_20261017.md', 'runs': len(df),
           'retained_attempts':len(all_df),'retained_feasible':int(all_df.feasible.sum()),
           'timing_repair':{'extra_runs':6,'interrupted_original_runs':4,'paired_blocks':3,
                           'original_extended_statuses':dict(all_df[all_df.profile=='extended'].status.value_counts()),
                           'repair_statuses':dict(all_df[all_df.profile=='timing_repairs'].status.value_counts()),
                           'max_elapsed_overrun_controlled_seconds':float((df.seconds-df.budget).max()),
                           'all_repeat_deadlines_passed':True},
           'profiles': {p: {'attempts': len(z), 'statuses': dict(z.status.value_counts()), 'feasible': int(z.feasible.sum()),
                            'optimal': int(z.optimal.sum())} for p,z in df.groupby('profile')}}
extended = df[df.profile=='extended']
assert len(extended[extended.method=='baseline']) == 18
assert len(extended[(extended.method!='baseline') & (extended.budget==20)]) == 36
assert len(extended[(extended.method!='baseline') & (extended.budget>20)]) == 36
assert (extended[extended.budget>20].seed == 1).all()
pair = extended[extended.method!='baseline'].pivot(index=['id','mode','budget'], columns='method', values=['optimal','upper_bound'])
joint = pair[(pair['optimal']['cold']==True) & (pair['optimal']['warm']==True)]
differences = (joint['upper_bound']['cold']-joint['upper_bound']['warm']).abs().astype(float)
assert not len(differences) or differences.max() < 1e-5
summary['paired_optima'] = {'n': len(joint), 'max_objective_difference': float(differences.max()) if len(joint) else None}
lines = []
for (fam,I,T,method),z in extended[extended.budget==20].groupby(['family','I','T','method']):
    good = z[z.feasible]
    lines.append([fam.capitalize(), f'{I}/{T}', method.capitalize(), len(z), int(z.feasible.sum()), int(z.optimal.sum()), med(good.first_seconds), med(100*good.relative_gap, '.1f')])
table('revision_anytime.tex', ['Family','$I/T$','Method','$n$','Feas.','Opt.','First s','Gap (\%)'], lines, 'lllrrrrr')
long = extended[(extended.method!='baseline') & (extended.seed==1)]
lines = []
long_summary = []
for (budget,method),z in long.groupby(['budget','method']):
    good=z[z.feasible]
    lines.append([int(budget),method.capitalize(),len(z),int(z.feasible.sum()),int(z.optimal.sum()),med(good.first_seconds),med(100*good.relative_gap,'.1f')])
    long_summary.append({'budget':budget,'method':method,'n':len(z),'feasible':int(z.feasible.sum()),'optimal':int(z.optimal.sum()),
                         'median_first_seconds':float(good.first_seconds.median()) if len(good) else None,
                         'median_relative_gap':float(good.relative_gap.median()) if len(good) else None})
table('revision_budgets.tex',['Budget s','Method','$n$','Feas.','Opt.','First s','Gap (\%)'],lines,'rlrrrrr')
summary['long_budgets'] = long_summary
summary['twenty_seconds'] = {method: {'n':len(z),'feasible':int(z.feasible.sum()),'optimal':int(z.optimal.sum()),
    'statuses':dict(z.status.value_counts()),'median_first_seconds':float(z[z.feasible].first_seconds.median()) if z.feasible.any() else None}
    for method,z in extended[extended.budget==20].groupby('method')}

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'savefig.bbox':'tight'})
COL = ['#0072B2','#D55E00','#009E73','#CC79A7']
def save(fig,name):
    fig.savefig(FIG/(name+'.pdf'));fig.savefig(FIG/(name+'.png'),dpi=220);plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(7.2,2.6),constrained_layout=True)
for color,method in zip(COL,['cold','warm']):
    z=long[long.method==method].groupby('budget')
    for ax,field,label in zip(axes,['feasible','optimal'],['Validated incumbent / 6','Closed numerical gap / 6']):
        counts=z[field].sum();ax.plot(counts.index,counts,marker='o' if method=='cold' else 's',
            linestyle='-' if method=='cold' else '--',markerfacecolor=color if method=='cold' else 'none',color=color,label=method.capitalize())
        ax.set(xlabel='Total budget (seconds)',ylabel=label,xticks=[20,60,120,300],yticks=range(7),ylim=(-.15,6.3))
        ax.legend(frameon=False,fontsize=8)
save(fig,'anytime_budgets')

compound=df[df.profile=='compound']
common={}
largest_increase=0.;strict_decreases=0;adjacent_pairs=0
for (fam,nlit,mode),z in compound.groupby(['family','literals','mode']):
    piv=z.pivot(index='id',columns='K',values='optimal')
    common[fam,nlit,mode]=set(piv.index[piv.all(axis=1)])
    values=z[z.optimal].pivot(index='id',columns='K',values='upper_bound').reindex(columns=[1,2,3,6])
    for left,right in zip([1,2,3],[2,3,6]):
        dif=(values[right]-values[left]).dropna()
        adjacent_pairs+=len(dif);strict_decreases+=int((dif < -1e-5).sum())
        if len(dif): largest_increase=max(largest_increase,float(dif.max()))
assert largest_increase<=1e-5
lines=[]
for (fam,nlit,K),z in compound.groupby(['family','literals','K']):
    paired_z=z[z.apply(lambda r:r.id in common[r.family,r.literals,r['mode']],axis=1)]
    lines.append([fam.capitalize(),int(nlit),int(K),int(z.optimal.sum()),int((z.status=='SOLVER_INFEASIBLE').sum()),int((~z.optimal & (z.status!='SOLVER_INFEASIBLE')).sum()),len(paired_z),med(paired_z.upper_bound),med(paired_z.periods,'.1f')])
table('revision_compound.tex',['Family','Literals','$K$','Opt.','Inf.','Unres.','Paired $n$','Cost','Periods'],lines,'lrrrrrrrr')
summary['compound_pairs']={'adjacent_solved_pairs':adjacent_pairs,'strict_cost_decreases':strict_decreases,'largest_positive_increase':largest_increase,
    'physical_statuses_across_attempts':dict(collections.Counter(a['physical_foil_status'] for a in raw['compound'])),
    'common_counts':{'|'.join(map(str,k)):len(v) for k,v in common.items()}}
fig,axes=plt.subplots(2,2,figsize=(7.2,4.6),constrained_layout=True,gridspec_kw={'height_ratios':[2,1]})
for col,fam in enumerate(['retail','hospital']):
    for color,(marker,style),(nlit,mode) in zip(COL,[('o','-'),('s','--'),('^',':'),('D','-.')],[(2,'weak'),(2,'strong'),(3,'weak'),(3,'strong')]):
        z=compound[(compound.family==fam)&(compound.literals==nlit)&(compound['mode']==mode)]
        paired_z=z[z.id.isin(common[fam,nlit,mode])]
        label=f'{nlit} literals, {mode} (n={len(common[fam,nlit,mode])})'
        if len(paired_z):
            v=paired_z.groupby('K').upper_bound.median();axes[0,col].plot(v.index,v,marker=marker,linestyle=style,color=color,label=label,markerfacecolor=color if mode=='weak' else 'none')
        else: axes[0,col].plot([],[],color=color,linestyle=style,label=label)
        counts=z.groupby('K').optimal.sum();axes[1,col].plot(counts.index,counts,marker=marker,linestyle=style,color=color,markerfacecolor=color if mode=='weak' else 'none')
    axes[0,col].set(title=fam.capitalize(),ylabel='Paired median explanation cost',xticks=[1,2,3,6]);axes[0,col].legend(fontsize=6,frameon=False)
    axes[1,col].set(xlabel='Maximum modified periods K',ylabel='Gap closed / 4',xticks=[1,2,3,6],yticks=range(5),ylim=(-.15,4.3))
save(fig,'compound_sensitivity')

capacity=[]
for a in raw['capacity_stress']:
    o=a.get('output',{});phys=a.get('physical_scenario_statuses',[])
    winner=o.get('scenario',0);feasible=o.get('upper_bound') is not None
    nominal=next((r['result'] for r in o.get('scenarios',[]) if r.get('scenario')==1),{})
    restoration=bool(phys and phys[0]=='INFEASIBLE' and any(s=='OPTIMAL' for s in phys[1:]))
    expansion=feasible and winner>1
    if not feasible: classification='no_validated_incumbent'
    elif not expansion: classification='nominal_winner'
    elif phys[0]=='INFEASIBLE': classification='physical_restoration'
    elif nominal.get('status')=='SOLVER_VALIDATED' and o['upper_bound']<nominal['upper_bound']-1e-5: classification='cost_improvement'
    else: classification='expanded_nominally_feasible_unresolved_comparison'
    capacity.append(dict(key=a['key'],family=a['instance']['family'],factor=a['factor'],mode=a['mode'],
        nominal_physical_status=phys[0] if phys else None,physically_restorable=restoration,
        feasible=feasible,optimal=o.get('status')=='SOLVER_VALIDATED',expanded=expansion,classification=classification,
        nominal_peak_utilization=a.get('nominal_peak_utilization'),diagnostic_seconds=a.get('diagnostic_seconds')))
cap=pd.DataFrame(capacity);cap.to_csv(RES/'revision_capacity_classification.csv',index=False)
lines=[]
for (fam,factor),z in cap.groupby(['family','factor']):
    lines.append([fam.capitalize(),f'{factor:.2f}',len(z),int((z.nominal_physical_status=='INFEASIBLE').sum()),int(z.physically_restorable.sum()),int(z.feasible.sum()),int(z.optimal.sum()),int(z.expanded.sum())])
table('revision_capacity.tex',['Family','Factor','$n$','Nom. inf.','Restorable','Feas.','Opt.','Expanded'],lines,'lrrrrrrr')
summary['capacity']={'classification_counts':dict(cap.classification.value_counts()),'physically_restorable':int(cap.physically_restorable.sum()),
    'nominal_physical_infeasible':int((cap.nominal_physical_status=='INFEASIBLE').sum()),
    'peak_utilization_range':[float(cap.nominal_peak_utilization.min()),float(cap.nominal_peak_utilization.max())],
    'diagnostic_seconds_repeated_per_mode':True}
macros={'RevisionRuns':len(df),'RevisionFeasible':int(df.feasible.sum()),'RevisionOptimal':int(df.optimal.sum()),
        'WarmTwentyFeasible':summary['twenty_seconds']['warm']['feasible'],'ColdTwentyFeasible':summary['twenty_seconds']['cold']['feasible'],
        'WarmTwentyOptimal':summary['twenty_seconds']['warm']['optimal'],'ColdTwentyOptimal':summary['twenty_seconds']['cold']['optimal'],
        'RevisionBaselineFeasible':summary['twenty_seconds']['baseline']['feasible'],
        'CompoundOptimal':int(compound.optimal.sum()),'CompoundInfeasible':int((compound.status=='SOLVER_INFEASIBLE').sum()),
        'CompoundUnresolved':int((~compound.optimal & (compound.status!='SOLVER_INFEASIBLE')).sum()),
        'CompoundDecreases':strict_decreases,'CompoundAdjacentPairs':adjacent_pairs,
        'CapacityRestorable':int(cap.physically_restorable.sum()),'CapacityNominalInfeasible':int((cap.nominal_physical_status=='INFEASIBLE').sum()),
        'CapacityRestorationWinners':int((cap.classification=='physical_restoration').sum()),
        'CapacityCostWinners':int((cap.classification=='cost_improvement').sum()),
        'CapacityOptimal':int(cap.optimal.sum()),'CapacityFeasible':int(cap.feasible.sum()),'CapacityExpanded':int(cap.expanded.sum()),
        'RevisionRetainedAttempts':len(all_df),'RevisionRetainedFeasible':int(all_df.feasible.sum())}
(TAB/'revision_numbers.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+str(v)+'}' for k,v in macros.items())+'\n')
(RES/'revision_summary.json').write_text(json.dumps(summary,indent=2,default=lambda x:x.item())+'\n')
print(json.dumps(summary,indent=2,default=lambda x:x.item()))
