"""Summarize the recourse-cost lever study of docs/levers_protocol_20261017.md.

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

ROOT = Path(__file__).resolve().parents[2]
RES, TAB, FIG = (ROOT / p for p in ['experiments/results', 'article/tables', 'article/figures'])
FINAL = '--final' in sys.argv
TOL = 1e-5


def load(profile, expected):
    out = []
    for f in sorted(RES.glob(f'levers_{profile}_w*.jsonl')):
        out += [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
    keys = [a['key'] for a in out]
    assert len(keys) == len(set(keys)), profile
    for a in out:
        for path, h in a['source_sha256'].items():
            assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == h, (profile, path)
    if FINAL:
        assert len(out) == expected, (profile, len(out))
    return out


def med(x, fmt='.3f'):
    x = pd.Series(x, dtype=float).dropna()
    return format(x.median(), fmt) if len(x) else '--'


macros = {}
enum = load('enum', 40)
bench = load('bench', 210)

# Correctness against independent enumeration.
rows = []
for a in enum:
    e, dd, tt = a['enumeration'], a['dual'], a['trajectory']
    eo = e.get('objective')
    def agree(r):
        if e['status'] == 'INFEASIBLE':
            return r['status'] == 'SOLVER_INFEASIBLE', None
        if r['status'] != 'SOLVER_VALIDATED':
            return False, None
        return abs(r['objective'] - eo) <= 1e-6, abs(r['objective'] - eo)
    ad, dd_diff = agree(dd)
    at, tt_diff = agree(tt)
    vd, vt = a.get('dual_verification') or {}, a.get('trajectory_verification') or {}
    rows.append(dict(key=a['key'], levers=a['levers'], mode=a['mode'], estatus=e['status'], dual_agree=ad, traj_agree=at,
                     dual_diff=dd_diff, traj_diff=tt_diff, dual_valid=vd.get('valid'), traj_valid=vt.get('valid'),
                     kkt=vd.get('kkt_gap'), dual_it=dd['iterations'], traj_it=tt['iterations'], enum_s=a['enumeration_seconds']))
E = pd.DataFrame(rows)
if len(E):
    E.to_csv(RES / 'levers_enum.csv', index=False)
    diffs = pd.concat([E.dual_diff, E.traj_diff]).dropna()
    macros.update(LeverEnumCases=len(E), LeverEnumDualAgree=int(E.dual_agree.sum()), LeverEnumTrajAgree=int(E.traj_agree.sum()),
                  LeverEnumFeasible=int((E.estatus == 'OPTIMAL').sum()), LeverEnumInfeasible=int((E.estatus == 'INFEASIBLE').sum()),
                  LeverEnumMaxDiff=f"{diffs.max():.1e}" if len(diffs) else '--')

# Benchmark.
rows = []
for a in bench:
    r, m = a['result'], a['instance']
    ok = r['status'] == 'SOLVER_VALIDATED'
    v = a.get('verification') or {}
    if ok:
        assert v.get('valid') is True, (a['key'], {k: v.get(k) for k in ('physical', 'actionable', 'lever_bounds', 'lever_support', 'kkt_gap', 'gap')})
    rows.append(dict(key=a['key'], id=m['id'], I=m['I'], T=m['T'], size=f"{m['I']}/{m['T']}", mode=a['mode'], lev=a['levers'], cuts=a['cuts'],
                     status=r['status'], ok=ok, inf=r['status'] == 'SOLVER_INFEASIBLE', obj=r.get('objective') if ok else None,
                     it=r['iterations'], s=r['seconds'], cont=(r.get('changed_unit', 0) + r.get('changed_holding', 0)) if ok else None,
                     fixed_used=r.get('changed_fixed') if ok else None, hit=r.get('dual_bound_active') if ok else None,
                     kkt=v.get('kkt_gap') if ok else None, primary=a.get('primary_status')))
B = pd.DataFrame(rows)
if len(B):
    B.to_csv(RES / 'levers_bench.csv', index=False)
    macros.update(LeverBenchRuns=len(B), LeverBenchValid=int(B.ok.sum()), LeverBenchInf=int(B.inf.sum()),
                  LeverBenchUnres=int((~B.ok & ~B.inf).sum()), LeverDualHits=int(B.hit.fillna(False).sum()),
                  LeverMaxKKT=f"{B.kkt.dropna().max():.1e}" if B.kkt.notna().any() else '--')
    q = B.set_index(['id', 'mode', 'lev', 'cuts'])
    def get(i, md, lev, cuts='dual'):
        try:
            return q.loc[(i, md, lev, cuts)]
        except KeyError:
            return None
    pairs = []
    for (i, md), _ in B.groupby(['id', 'mode']):
        f, fph, ph = get(i, md, 'F'), get(i, md, 'FPH'), get(i, md, 'PH')
        if f is None or fph is None or ph is None:
            continue
        pairs.append(dict(id=i, mode=md, size=f['size'], f_ok=f['ok'], f_inf=f['inf'], fph_ok=fph['ok'], fph_inf=fph['inf'], ph_ok=ph['ok'], ph_inf=ph['inf'],
                          f_obj=f['obj'], fph_obj=fph['obj'], ph_obj=ph['obj'], fph_cont=fph['cont']))
    P = pd.DataFrame(pairs, columns=['id','mode','size','f_ok','f_inf','fph_ok','fph_inf','ph_ok','ph_inf','f_obj','fph_obj','ph_obj','fph_cont'])
    both = P[P.f_ok & P.fph_ok]
    improve = both[both.fph_obj < both.f_obj - TOL]
    viol = both[both.fph_obj > both.f_obj + TOL]
    gained = P[P.f_inf & P.fph_ok]
    phboth = P[P.f_ok & P.ph_ok]
    macros.update(LeverQueries=len(P), LeverBothValid=len(both), LeverImprove=len(improve), LeverViolations=len(viol),
                  LeverImproveMedian=f"{100*np.median((improve.f_obj-improve.fph_obj)/improve.f_obj):.1f}" if len(improve) else '--',
                  LeverImproveMax=f"{100*np.max((improve.f_obj-improve.fph_obj)/improve.f_obj):.1f}" if len(improve) else '--',
                  LeverFInf=int(P.f_inf.sum()), LeverGained=len(gained), LeverPHValid=int(P.ph_ok.sum()), LeverPHInf=int(P.ph_inf.sum()),
                  LeverPHRatio=med(phboth.ph_obj / phboth.f_obj, '.2f'), LeverContUsed=int((P.fph_ok & (P.fph_cont > 0)).sum()))
    # Dual versus trajectory cuts.
    comp = []
    for (i, md, lev), x in B[B.lev != 'F'].groupby(['id', 'mode', 'lev']):
        if set(x.cuts) != {'dual', 'trajectory'}:
            continue
        d, t = x[x.cuts == 'dual'].iloc[0], x[x.cuts == 'trajectory'].iloc[0]
        comp.append(dict(lev=lev, size=d['size'], dstat=d['status'], tstat=t['status'], dit=d['it'], tit=t['it'], ds=d['s'], ts=t['s'],
                         dobj=d['obj'], tobj=t['obj'], bothres=(d['ok'] or d['inf']) and (t['ok'] or t['inf'])))
    C = pd.DataFrame(comp, columns=['lev','size','dstat','tstat','dit','tit','ds','ts','dobj','tobj','bothres'])
    res = C[C.bothres.astype(bool)]
    macros.update(LeverCutPairs=len(C), LeverCutResolved=len(res), LeverCutStatusDis=int((res.dstat != res.tstat).sum()),
                  LeverCutFewer=int((res.dit < res.tit).sum()), LeverCutMore=int((res.dit > res.tit).sum()), LeverCutEqual=int((res.dit == res.tit).sum()),
                  LeverCutObjDiff=f"{np.nanmax(np.abs(res.dobj - res.tobj)):.1e}" if res.dobj.notna().any() else '--',
                  LeverCutTimeRatio=med(res.ts / res.ds, '.2f'),
                  LeverDualOnlyResolved=int(((C.dstat.isin(['SOLVER_VALIDATED', 'SOLVER_INFEASIBLE'])) & ~(C.tstat.isin(['SOLVER_VALIDATED', 'SOLVER_INFEASIBLE']))).sum()),
                  LeverTrajOnlyResolved=int((~(C.dstat.isin(['SOLVER_VALIDATED', 'SOLVER_INFEASIBLE'])) & (C.tstat.isin(['SOLVER_VALIDATED', 'SOLVER_INFEASIBLE']))).sum()))
    inf = res[(res.dstat == 'SOLVER_INFEASIBLE') & (res.tstat == 'SOLVER_INFEASIBLE')]
    macros.update(LeverInfPairs=len(inf), LeverInfDualIt=med(inf.dit, '.1f'), LeverInfTrajIt=med(inf.tit, '.1f'))
    # Table by size, lever set and cut type.
    lines = [r'\begin{tabular}{lllrrrrrr}', r'\toprule',
             r'$I/T$ & Levers & Cuts & $n$ & Valid. & Inf. & Unres. & Median s & Median iter. \\', r'\midrule']
    order = {'F': 0, 'PH': 1, 'FPH': 2}
    for (sz, lev, cuts), x in sorted(B.groupby(['size', 'lev', 'cuts']), key=lambda kv: (tuple(map(int, kv[0][0].split('/'))), order[kv[0][1]], kv[0][2])):
        lines.append(f"{sz} & {lev} & {'Dual' if cuts=='dual' else 'Trajectory'} & {len(x)} & {int(x.ok.sum())} & {int(x.inf.sum())} & {int((~x.ok & ~x.inf).sum())} & "
                     f"{med(x.s, '.2f')} & {med(x.it, '.1f')} \\\\")
    lines += [r'\bottomrule', r'\end{tabular}']
    (TAB / 'levers_bench.tex').write_text('\n'.join(lines) + '\n')
    # Figure: objective of PH and FPH against F, and iterations dual versus trajectory.
    if len(P) and len(res):
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
        x = P[P.f_ok & P.ph_ok]
        ax[0].scatter(x.f_obj, x.ph_obj, s=14, label='PH (continuous levers only)', color='C3')
        x = P[P.f_ok & P.fph_ok]
        ax[0].scatter(x.f_obj, x.fph_obj, s=14, marker='s', facecolors='none', edgecolors='C0', label='FPH (all levers)')
        lim = [0, max(1e-3, np.nanmax(np.r_[P.f_obj.dropna(), P.ph_obj.dropna(), P.fph_obj.dropna()])) * 1.05]
        ax[0].plot(lim, lim, ls='--', color='gray', lw=.8); ax[0].set_xlim(lim); ax[0].set_ylim(lim)
        ax[0].set_xlabel('Objective with activation levers only (F)'); ax[0].set_ylabel('Objective with recourse levers'); ax[0].legend(frameon=False, fontsize=8)
        ax[1].scatter(res.dit, res.tit, s=14, color='C2')
        m = max(1, np.nanmax(np.r_[res.dit, res.tit])) + 1
        ax[1].plot([0, m], [0, m], ls='--', color='gray', lw=.8); ax[1].set_xlim(0, m); ax[1].set_ylim(0, m)
        ax[1].set_xlabel('Iterations with dual cuts'); ax[1].set_ylabel('Iterations with trajectory cuts')
        for a_ in ax: a_.grid(alpha=.3)
        fig.tight_layout(); fig.savefig(FIG / 'levers.pdf'); fig.savefig(FIG / 'levers.png', dpi=150); plt.close(fig)

# Illustration: one query explained by activation edits (F) and by recourse-cost edits alone (PH).
if len(B):
    recs = {a['key']: a for a in bench}
    sel = B[(B.lev == 'PH') & B.ok & (B.cuts == 'dual') & (B.I >= 2)].sort_values(['cont', 'key'], ascending=[False, True])
    cand = list(sel.key)
    for k in cand:
        i_, md = k.split('|')[0], k.split('|')[1]
        kf = f'{i_}|{md}|F|dual'
        if kf in recs and recs[kf]['result']['status'] == 'SOLVER_VALIDATED':
            a_ph, a_f = recs[k], recs[kf]
            m = a_ph['instance']; I, T = m['I'], m['T']
            mat = lambda v: np.array(v, dtype=float).reshape(T, I).T
            f0, p0, h0 = mat(m['fixed']), mat(m['unit']), mat(m['holding'])
            panels = [(mat(a_f['result']['delta']) / f0, 'Activation-cost edits (F)'),
                      (mat(a_ph['result']['zp']) / p0, 'Unit-cost edits (PH)'),
                      (mat(a_ph['result']['zh']) / h0, 'Holding-cost edits (PH)')]
            fig, ax = plt.subplots(1, 3, figsize=(10, 2.6), sharey=True)
            for a_, (v, title) in zip(ax, panels):
                im = a_.imshow(v, cmap='RdBu_r', vmin=-.8, vmax=.8, aspect='auto')
                a_.set_title(title, fontsize=9); a_.set_xticks(range(T)); a_.set_xticklabels(range(1, T + 1)); a_.set_xlabel('Period')
                for (r_, c_), val in np.ndenumerate(v):
                    if abs(val) > 1e-6:
                        a_.text(c_, r_, f'{val:+.2f}', ha='center', va='center', fontsize=7)
            ax[0].set_yticks(range(I)); ax[0].set_yticklabels([f'Item {r_+1}' for r_ in range(I)])
            fig.colorbar(im, ax=ax, shrink=.8, label='Relative edit')
            fig.savefig(FIG / 'levers_example.pdf', bbox_inches='tight'); fig.savefig(FIG / 'levers_example.png', dpi=150, bbox_inches='tight'); plt.close(fig)
            macros.update(LeverExampleId=i_.replace('_', '\\_'), LeverExampleMode=md, LeverExampleF=f"{a_f['result']['objective']:.3f}",
                          LeverExamplePH=f"{a_ph['result']['objective']:.3f}")
            break

(TAB / 'levers_numbers.tex').write_text(''.join(f'\\newcommand{{\\{k}}}{{{v}}}\n' for k, v in sorted(macros.items())))
json.dump(macros, open(RES / 'levers_summary.json', 'w'), indent=1, default=str)
print(json.dumps(macros, indent=1, default=str))
