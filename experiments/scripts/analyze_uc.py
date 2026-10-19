"""Summarize the unit commitment case study of docs/uc_protocol_20261017.md.

Run with --final to enforce the expected attempt counts."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':8,'axes.labelsize':8,'legend.fontsize':6.5,'xtick.labelsize':7,'ytick.labelsize':7,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'savefig.bbox':'tight','savefig.pad_inches':0.02})

ROOT = Path(__file__).resolve().parents[2]
RES, TAB, FIG = (ROOT / p for p in ['experiments/results', 'article/tables', 'article/figures'])
TAB.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
FINAL = '--final' in sys.argv


def load(profile, expected=None):
    out = []
    for f in sorted(RES.glob(f'uc_{profile}_w*.jsonl')):
        out += [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
    keys = [a['key'] for a in out]
    assert len(keys) == len(set(keys)), profile
    for a in out:
        for path, h in a['source_sha256'].items():
            assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == h, (profile, path)
    if FINAL and expected is not None:
        assert len(out) == expected, (profile, len(out))
    return out


def med(x, fmt='.2f'):
    x = pd.Series(x, dtype=float).dropna()
    return format(x.median(), fmt) if len(x) else '--'


macros = {}
enum, bench = load('enum'), load('bench', 160)

# Correctness against enumeration of commitments and dispatch vertices.
rows = []
for a in enum:
    e = a['enumeration']
    def agree(r):
        if e['status'] == 'INFEASIBLE':
            return r['status'] == 'SOLVER_INFEASIBLE', None
        if r['status'] != 'SOLVER_VALIDATED':
            return False, None
        return abs(r['objective'] - e['objective']) <= 1e-6, abs(r['objective'] - e['objective'])
    ad, ddiff = agree(a['dual'])
    at, tdiff = agree(a['trajectory'])
    vd = a.get('dual_verification') or {}
    rows.append(dict(estatus=e['status'], dual_agree=ad, traj_agree=at, dual_diff=ddiff, traj_diff=tdiff, dual_valid=vd.get('valid'),
                     dual_it=a['dual']['iterations'], traj_it=a['trajectory']['iterations'],
                     dual_unres=a['dual']['status'] not in ('SOLVER_VALIDATED', 'SOLVER_INFEASIBLE'),
                     traj_unres=a['trajectory']['status'] not in ('SOLVER_VALIDATED', 'SOLVER_INFEASIBLE')))
E = pd.DataFrame(rows)
if len(E):
    diffs = pd.concat([E.dual_diff, E.traj_diff]).dropna()
    both = E[~E.dual_unres & ~E.traj_unres]
    macros.update(UCEnumCases=len(E), UCEnumFeasible=int((E.estatus == 'OPTIMAL').sum()), UCEnumInfeasible=int((E.estatus == 'INFEASIBLE').sum()),
                  UCEnumDualAgree=int(E.dual_agree.sum()), UCEnumTrajAgree=int(E.traj_agree.sum()),
                  UCEnumTrajUnres=int(E.traj_unres.sum()), UCEnumDualUnres=int(E.dual_unres.sum()),
                  UCEnumMaxDiff=f'{diffs[diffs <= 1e-6].max():.1e}' if len(diffs) else '--',
                  UCEnumWorstGap=f'{diffs.max():.3f}' if len(diffs) else '--',
                  UCEnumDualIt=med(both.dual_it, '.1f'), UCEnumTrajIt=med(both.traj_it, '.1f'),
                  UCEnumTrajMoreIt=int((both.traj_it > both.dual_it).sum()), UCEnumTrajFewerIt=int((both.traj_it < both.dual_it).sum()))

# Benchmark.
rows = []
for a in bench:
    r, v = a['result'], a.get('verification') or {}
    q = a['key'].split('|')
    rows.append(dict(key=a['key'], query='|'.join(q[:3]), day=q[0], lev=a['levers'], cuts=a['cuts'], mode=a['mode'], status=r['status'],
                     ok=r['status'] == 'SOLVER_VALIDATED', inf=r['status'] == 'SOLVER_INFEASIBLE', obj=r.get('objective'),
                     s=r['seconds'], it=r['iterations'], valid=v.get('valid'), kkt=v.get('kkt_gap'), hit=r.get('dual_bound_active'),
                     periods=r.get('changed_periods'), nl=r.get('changed_noload'), mc=r.get('changed_marginal'),
                     start=json.loads(json.dumps(a['foil']))[0][2] == 1))
B = pd.DataFrame(rows)
order = [('F-R', 'dual'), ('F', 'dual'), ('M', 'dual'), ('FM', 'dual'), ('FM', 'trajectory')]
names = {'F-R': 'Activation, ramps', 'F': 'Activation', 'M': 'Marginal', 'FM': 'Both'}
lines = [r'\begin{tabular}{llrrrrrr}', r'\toprule', r'Levers & Cuts & $n$ & Valid. & Inf. & Unres. & Median s & Median iter. \\', r'\midrule']
for lev, cuts in order:
    g = B[(B.lev == lev) & (B.cuts == cuts)]
    if not len(g):
        continue
    lines.append(f"{names[lev]} & {'Dual' if cuts == 'dual' else 'Trajectory'} & {len(g)} & {int(g.ok.sum())} & {int(g.inf.sum())} & "
                 f"{int((~g.ok & ~g.inf).sum())} & {med(g.s)} & {med(g[g.ok | g.inf].it, '.1f')} \\\\")
lines += [r'\bottomrule', r'\end{tabular}']
(TAB / 'uc_bench.tex').write_text('\n'.join(lines) + '\n')

if len(B):
    ok = B[B.ok]
    macros.update(UCRuns=len(B), UCQueries=B['query'].nunique(), UCValid=int(B.ok.sum()), UCInf=int(B.inf.sum()), UCUnres=int((~B.ok & ~B.inf).sum()),
                  UCVerified=int((ok.valid == True).sum()), UCMaxKKT=f"{ok.kkt.max():.1e}" if ok.kkt.notna().any() else '--',
                  UCDualHits=int((ok.hit == True).sum()))
    P = B[B.cuts == 'dual'].pivot_table(index='query', columns='lev', values=['ok', 'inf', 'obj', 'mc', 'nl', 'periods'], aggfunc='first')
    def col(v, l):
        return P[(v, l)] if (v, l) in P.columns else pd.Series(np.nan, index=P.index)
    okF, okFM, okM = col('ok', 'F').astype(bool), col('ok', 'FM').astype(bool), col('ok', 'M').astype(bool)
    infF = col('inf', 'F').astype(bool)
    both = okF & okFM
    imp = (col('obj', 'F') - col('obj', 'FM'))[both]
    viol = int((imp < -1e-6).sum())
    better = imp[imp > 1e-6]
    macros.update(UCBothValid=int(both.sum()), UCImprove=int((imp > 1e-6).sum()), UCViolations=viol,
                  UCImproveMedian=f'{(better / col("obj", "F")[better.index]).median() * 100:.0f}' if len(better) else '--',
                  UCImproveMax=f'{(better / col("obj", "F")[better.index]).max() * 100:.0f}' if len(better) else '--',
                  UCGained=int((infF & okFM).sum()), UCFInf=int(infF.sum()),
                  UCMValid=int(okM.sum()), UCMInf=int(col('inf', 'M').astype(bool).sum()),
                  UCContUsed=int((col('mc', 'FM')[okFM] > 0).sum()), UCFMValid=int(okFM.sum()))
    okMF = okM & okF
    macros['UCMRatio'] = med((col('obj', 'M') / col('obj', 'F'))[okMF], '.2f')
    # Ramps: same activation levers with and without ramp limits.
    R = B[B.lev.isin(['F', 'F-R'])].pivot_table(index='query', columns='lev', values=['ok', 'inf', 'obj'], aggfunc='first')
    rb = R[('ok', 'F')].astype(bool) & R[('ok', 'F-R')].astype(bool)
    macros.update(UCRampValid=int(R[('ok', 'F-R')].astype(bool).sum()), UCRampBoth=int(rb.sum()),
                  UCRampDiffer=int((abs(R[('obj', 'F')] - R[('obj', 'F-R')])[rb] > 1e-6).sum()))
    # Cut families on the same queries.
    C = B[B.lev == 'FM'].pivot_table(index='query', columns='cuts', values=['ok', 'inf', 'it', 's', 'obj'], aggfunc='first')
    res = (C[('ok', 'dual')].astype(bool) | C[('inf', 'dual')].astype(bool)) & (C[('ok', 'trajectory')].astype(bool) | C[('inf', 'trajectory')].astype(bool))
    dis = int(((C[('ok', 'dual')].astype(bool) != C[('ok', 'trajectory')].astype(bool)) & res).sum())
    rc = C[res]
    jo = rc[rc[('ok', 'dual')].astype(bool)]
    macros.update(UCCutPairs=len(C), UCCutResolved=int(res.sum()), UCCutStatusDis=dis,
                  UCCutFewer=int((rc[('it', 'dual')] < rc[('it', 'trajectory')]).sum()), UCCutMore=int((rc[('it', 'dual')] > rc[('it', 'trajectory')]).sum()),
                  UCCutObjDiff=f"{abs(jo[('obj', 'dual')] - jo[('obj', 'trajectory')]).max():.1e}" if len(jo) else '--',
                  UCCutTimeRatio=med((rc[('s', 'trajectory')] / rc[('s', 'dual')]), '.2f'),
                  UCDualOnly=int(((C[('ok', 'dual')].astype(bool) | C[('inf', 'dual')].astype(bool)) & ~(C[('ok', 'trajectory')].astype(bool) | C[('inf', 'trajectory')].astype(bool))).sum()),
                  UCTrajOnly=int((~(C[('ok', 'dual')].astype(bool) | C[('inf', 'dual')].astype(bool)) & (C[('ok', 'trajectory')].astype(bool) | C[('inf', 'trajectory')].astype(bool))).sum()))

    # Illustration: the first validated start query with ramp limits, in key order.
    recs = {a['key']: a for a in bench}
    sel = B[(B.lev == 'F-R') & B.ok & B.start].sort_values('key')
    if len(sel):
        a = recs[sel.key.iloc[0]]; m = a['instance']; G, T = len(m['pmin']), len(m['demand'])
        mat = lambda x: np.array(x, dtype=float).reshape(T, G).T if np.array(x).ndim == 1 else np.array(x, dtype=float)
        de = mat(a['result']['delta']) / np.array(m['noload'])[:, None]; u = mat(a['result']['u'])
        fig, ax = plt.subplots(1, 2, figsize=(4.6, 2.5), sharey=True)
        ax[0].imshow(u, cmap='Greys', vmin=0, vmax=1.6, aspect='auto'); ax[0].set_title('(a)', loc='left')
        im = ax[1].imshow(de, cmap='RdBu_r', vmin=-.8, vmax=.8, aspect='auto'); ax[1].set_title('(b)', loc='left')
        g0, t0, v0 = a['foil'][0]
        for a_ in ax:
            a_.set_xticks(range(T)); a_.set_xticklabels(range(1, T + 1), fontsize=5.5); a_.set_xlabel('Hour')
            a_.add_patch(plt.Rectangle((t0 - 1.5, g0 - 1.5), 1, 1, fill=False, lw=1.5, ec='black'))
        ax[0].set_yticks(range(G)); ax[0].set_yticklabels(m['names'], fontsize=5.5)
        fig.colorbar(im, ax=ax[1], shrink=.8, label='Relative edit')
        fig.savefig(FIG / 'uc_example.pdf', bbox_inches='tight'); fig.savefig(FIG / 'uc_example.png', dpi=150, bbox_inches='tight'); plt.close(fig)
        r = a['result']
        macros.update(UCExampleDay=pd.Timestamp(a['key'].split('|')[0].split('_')[1]).strftime('%-d %B %Y'), UCExampleUnit=m['names'][g0 - 1].replace('_', '\\_'), UCExampleHour=t0,
                      UCExampleMode=a['mode'], UCExampleObj=f"{r['objective']:.3f}", UCExamplePeriods=r['changed_periods'], UCExampleEdits=r['changed_noload'])
    other = earlier = 0
    for a in bench:
        if a['levers'] in ('F', 'F-R') and a['result']['status'] == 'SOLVER_VALIDATED':
            m = a['instance']; G, T = len(m['pmin']), len(m['demand'])
            dd = np.array(a['result']['delta'], dtype=float); dd = dd.reshape(T, G).T if dd.ndim == 1 else dd
            g0, t0, _ = a['foil'][0]; ch = np.argwhere(abs(dd) > 1e-6)
            other += any(g != g0 - 1 for g, t in ch); earlier += any(t < t0 - 1 for g, t in ch)
    macros.update(UCOtherUnit=int(other), UCEarlierHour=int(earlier))
    okFR = B[(B.lev == 'F-R') & B.ok]
    macros.update(UCFRMedianPeriods=med(okFR.periods, '.0f'), UCFRMaxPeriods=int(okFR.periods.max()) if len(okFR) else 0,
                  UCFRMedianS=med(okFR.s, '.0f'), UCFRunres=int((B.lev == 'F-R').sum() - okFR.shape[0] - B[(B.lev == 'F-R') & B.inf].shape[0]))

(TAB / 'uc_numbers.tex').write_text(''.join(f'\\newcommand{{\\{k}}}{{{v}}}\n' for k, v in sorted(macros.items())))
print(json.dumps(macros, indent=1))
