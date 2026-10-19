"""Summarize the audit-response study of docs/audit_protocol_20261017.md.

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
EXPECTED = {'long': 48, 'sparsity': 600, 'margin': 180, 'naive': 288, 'bound': 100}
TOL = 1e-5


def load(profile):
    out = []
    for f in sorted(RES.glob(f'audit_{profile}_w*.jsonl')):
        out += [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
    keys = [a['key'] for a in out]
    assert len(keys) == len(set(keys)), profile
    for a in out:
        for path, h in a['source_sha256'].items():
            assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == h, (profile, path)
    if FINAL and EXPECTED[profile] is not None:
        assert len(out) == EXPECTED[profile], (profile, len(out))
    return out


def jl_foil(foil):
    return '[' + ', '.join(f'({i}, {t}, {v})' for i, t, v in foil) + ']'


def med(x, fmt='.3f'):
    x = pd.Series(x, dtype=float).dropna()
    return format(x.median(), fmt) if len(x) else '--'


macros = {}
raw = {p: load(p) for p in EXPECTED}

# Analytical coordinate bound (Proposition 4.5).
bounds = {b['key']: b for b in raw['bound']}


def coord_lb(id_, foil, mode, eps=0., margin=0., lam=0.):
    b = bounds.get(f'{id_}|{jl_foil(foil)}')
    if b is None or b['inside_status'] != 'OPTIMAL':
        return None
    if b['outside_status'] == 'INFEASIBLE':
        return 0.
    if b['outside_status'] != 'OPTIMAL':
        return None
    s = margin if mode == 'strong' else -eps
    D = max(0., b['alpha_lb'] - b['beta_ub'] + s)
    return D / b['amax'] + (lam if D > 1e-6 else 0.)


# Sanity check against every validated global optimum of the primary and compound studies.
checks = []
for p in ['main', 'scale', 'long']:
    for a in map(json.loads, (RES / f'{p}.jsonl').read_text().splitlines()):
        if a['job']['method'] != 'ccg' or a['status'] != 'SOLVER_VALIDATED':
            continue
        lb = coord_lb(a['instance']['id'], a['foil'], a['job']['mode'], a['job']['epsilon'], a['job']['margin'], .01)
        if lb is not None:
            checks.append(dict(source=p, lb=lb, opt=a['result']['objective']))
for a in map(json.loads, (RES / 'revision_compound.jsonl').read_text().splitlines()):
    o = a['output']
    if o['status'] == 'SOLVER_VALIDATED':
        lb = coord_lb(a['instance']['id'], a['foil'], a['mode'], 0., a['margin'], .01)
        if lb is not None:
            checks.append(dict(source='compound', lb=lb, opt=o['upper_bound']))
for a in raw['sparsity']:
    o = a['output']
    if o['status'] == 'SOLVER_VALIDATED':
        lb = coord_lb(a['instance']['id'], a['foil'], a['mode'], 0., a['margin'], 0.)
        if lb is not None:
            checks.append(dict(source='sparsity', lb=lb, opt=o['upper_bound']))
chk = pd.DataFrame(checks)
if len(chk):
    chk['violation'] = chk.lb > chk.opt + TOL
    pos = chk[chk.opt > 1e-6]
    macros.update(BoundChecks=len(chk), BoundViolations=int(chk.violation.sum()),
                  BoundRatioMedian=med(pos.lb / pos.opt, '.3f'), BoundRatioMin=med([(pos.lb / pos.opt).min()], '.3f'))

# Baseline gap with the analytical bound, primary single-coordinate study.
sl = [json.loads(l) for l in (RES / 'single_lever.jsonl').read_text().splitlines()]
prim = {a['key']: a for p in ['main', 'scale', 'long'] for a in map(json.loads, (RES / f'{p}.jsonl').read_text().splitlines())}
gaps = []
for s in sl:
    if s['status'] != 'RESTRICTED_SOLVER_OPTIMAL':
        continue
    a = prim[s['key']]
    lb = coord_lb(a['instance']['id'], a['foil'], a['job']['mode'], a['job']['epsilon'], a['job']['margin'], .01)
    if lb is None:
        continue
    opt = a['result']['objective'] if a['status'] == 'SOLVER_VALIDATED' else None
    gaps.append(dict(profile=s['profile'], base=s['objective'], lb=lb, opt=opt,
                     gap=(s['objective'] - lb) / max(1e-9, s['objective'])))
g = pd.DataFrame(gaps)
if len(g):
    macros.update(BaselineBoundN=len(g), BaselineGapMedian=f"{100*g.gap.median():.1f}", BaselineGapMax=f"{100*g.gap.max():.1f}")
    gv = g.dropna(subset=['opt'])
    gv = gv[gv.opt > 1e-6]
    macros.update(BaselineTrueRatioMax=f"{(gv.base / gv.opt).max():.3f}", BaselineTrueRatioMedian=f"{(gv.base / gv.opt).median():.3f}")

# Long budgets.
rows = []
for a in raw['long']:
    o, m = a['output'], a['instance']
    ub, lb = o.get('upper_bound'), o.get('lower_bound')
    clb = coord_lb(m['id'], a['foil'], a['mode'], a['epsilon'], a['margin'], .01)
    comb = max(x for x in [lb, clb] if x is not None) if (lb is not None or clb is not None) else None
    feasible = ub is not None
    if feasible:
        assert o['verification']['valid'] is True, a['key']
    rows.append(dict(key=a['key'], family=m['family'], IT=f"{m['I']}/{m['T']}", seed=m['seed'], mode=a['mode'], method=a['method'],
                     budget=a['budget'], feasible=feasible, optimal=o['status'] == 'SOLVER_VALIDATED',
                     gap=o.get('relative_gap'), cgap=(max(0., ub - comb) / max(1e-9, abs(ub)) if feasible and comb is not None else None),
                     first=o.get('first_feasible_seconds'), seconds=o.get('seconds'),
                     overrun=o.get('seconds', 0) > a['budget'] + max(1., .05 * a['budget'])))
L = pd.DataFrame(rows)
if len(L):
    L.to_csv(RES / 'audit_long.csv', index=False)
    lines = [r'\begin{tabular}{lllrrrrrr}', r'\toprule',
             r'Family & $I/T$ & Method & Budget s & $n$ & Feas. & Opt. & Gap (\%) & Gap$^{+}$ (\%) \\', r'\midrule']
    for (fam, it, b, meth), x in L.groupby(['family', 'IT', 'budget', 'method'], sort=True):
        xf = x[x.feasible]
        lines.append(f"{fam.capitalize()} & {it} & {'Warm' if meth=='warm' else 'Cold'} & {int(b)} & {len(x)} & {int(x.feasible.sum())} & {int(x.optimal.sum())} & "
                     f"{med(100*xf.gap, '.1f')} & {med(100*xf.cgap, '.1f')} \\\\")
    lines += [r'\bottomrule', r'\end{tabular}']
    (TAB / 'audit_long.tex').write_text('\n'.join(lines) + '\n')
    for b in [600., 1800.]:
        for meth in ['cold', 'warm']:
            x = L[(L.budget == b) & (L.method == meth)]
            tag = f"{'Warm' if meth=='warm' else 'Cold'}{'Six' if b==600 else 'Eighteen'}"
            macros[f'{tag}N'] = len(x)
            macros[f'{tag}Feasible'] = int(x.feasible.sum())
            macros[f'{tag}Optimal'] = int(x.optimal.sum())
    macros['LongOverruns'] = int(L.overrun.sum())

# Active sparsity budget.
rows = []
for a in raw['sparsity']:
    o, m = a['output'], a['instance']
    feasible = o.get('upper_bound') is not None
    if feasible:
        assert o['verification']['valid'] is True, a['key']
    rows.append(dict(id=m['id'], family=m['family'], k=a['literal_count'], mode=a['mode'], K=a['K'], cb=a['cost_bound'],
                     physical=a['physical_foil_status'], status=o['status'], feasible=feasible,
                     optimal=o['status'] == 'SOLVER_VALIDATED', infeasible=o['status'] == 'SOLVER_INFEASIBLE',
                     cost=o['upper_bound'] if o['status'] == 'SOLVER_VALIDATED' else None,
                     periods=(o['result'] or {}).get('changed_periods') if feasible else None))
S = pd.DataFrame(rows)
if len(S):
    S.to_csv(RES / 'audit_sparsity.csv', index=False)
    Ks = [1, 2, 3, 4, 8]
    q = S.groupby(['id', 'k', 'mode', 'cb'])
    dec = adj = 0
    paired = []
    for key, x in q:
        x = x.set_index('K')
        for k0, k1 in zip(Ks, Ks[1:]):
            if k0 in x.index and k1 in x.index and x.loc[k0, 'optimal'] and x.loc[k1, 'optimal']:
                adj += 1
                dec += x.loc[k1, 'cost'] < x.loc[k0, 'cost'] - TOL
        if all(k in x.index and x.loc[k, 'optimal'] for k in Ks):
            paired.append(key)
    macros.update(SparsityAttempts=len(S), SparsityOptimal=int(S.optimal.sum()), SparsityInfeasible=int(S.infeasible.sum()),
                  SparsityUnresolved=int((~S.optimal & ~S.infeasible).sum()), SparsityAdjacent=adj, SparsityDecreases=int(dec),
                  SparsityPaired=len(paired), SparsityPhysicalInfeasible=int((S.physical == 'INFEASIBLE').sum()))
    # Queries whose cost strictly falls between K_T=1 or the first feasible budget and K_T=8.
    span = []
    for key, x in q:
        x = x[x.optimal].sort_values('K')
        if len(x) >= 2 and x.cost.iloc[0] > x.cost.iloc[-1] + TOL:
            span.append((x.cost.iloc[0] - x.cost.iloc[-1]) / x.cost.iloc[0])
    macros.update(SparsityTradeoffQueries=len(span), SparsityTradeoffMedian=f"{100*np.median(span):.1f}" if span else '--',
                  SparsityTradeoffMax=f"{100*np.max(span):.1f}" if span else '--',
                  SparsityQueries=len(q))
    lines = [r'\begin{tabular}{llrrrrrrr}', r'\toprule',
             r'Edit bound & Literals & $K_T$ & Opt. & Inf. & Unres. & Paired $n$ & Cost & Periods \\', r'\midrule']
    pk = set(paired)
    for (cb, k, K), x in S.groupby(['cb', 'k', 'K']):
        xp = x[[(i, kk, md, c) in pk for i, kk, md, c in zip(x.id, x.k, x['mode'], x.cb)]]
        lines.append(f"{cb:.1f} & {k} & {K} & {int(x.optimal.sum())} & {int(x.infeasible.sum())} & {int((~x.optimal & ~x.infeasible).sum())} & "
                     f"{len(xp)} & {med(xp.cost)} & {med(xp.periods, '.1f')} \\\\")
    lines += [r'\bottomrule', r'\end{tabular}']
    (TAB / 'audit_sparsity.tex').write_text('\n'.join(lines) + '\n')
    fig, axes = plt.subplots(1, 2, figsize=(4.6, 2.5))
    pk = set(paired)
    styles = {(.8, 2): ('C0', 'o', '-'), (.8, 3): ('C0', 's', '--'), (.4, 2): ('C3', 'o', '-'), (.4, 3): ('C3', 's', '--'),
              (.8, 4): ('C0', 'D', ':'), (.4, 4): ('C3', 'D', ':')}
    for (cb, k), (c, mk, ls) in styles.items():
        x = S[(S.cb == cb) & (S.k == k)]
        xp = x[[(i, kk, md, cc) in pk for i, kk, md, cc in zip(x.id, x.k, x['mode'], x.cb)]]
        lab = f'{k} literals, bound {cb:.1f}$c^0$'
        if len(xp):
            m = xp.groupby('K').cost.median()
            axes[0].plot(m.index, m.values, color=c, marker=mk, ls=ls, mfc=c if cb > .5 else 'none', label=f'{lab} ($n$={len(xp)//len(Ks)})')
        else:
            axes[0].plot([], [], color=c, marker=mk, ls=ls, mfc=c if cb > .5 else 'none', label=f'{lab} ($n$=0)')
        axes[1].plot(Ks, [int(x[x.K == K].optimal.sum()) for K in Ks], color=c, marker=mk, ls=ls, mfc=c if cb > .5 else 'none', label=lab)
    axes[0].set_ylabel('Median edit cost (paired)'); axes[1].set_ylabel('Gap closed (of 20)')
    axes[0].set_title('(a)', loc='left'); axes[1].set_title('(b)', loc='left')
    for ax in axes:
        ax.set_xlabel('Period budget $K_T$'); ax.set_xticks(Ks); ax.grid(alpha=.3)
    axes[0].legend(frameon=False, fontsize=6, loc='upper right')
    fig.tight_layout(); fig.savefig(FIG / 'audit_sparsity.pdf'); fig.savefig(FIG / 'audit_sparsity.png', dpi=150); plt.close(fig)

# Margin calibration.
rows = []
for a in raw['margin']:
    r = a['result']
    ok = a['status'] == 'SOLVER_VALIDATED'
    if ok:
        assert a['verification']['valid'] is True, a['key']
    rad = a.get('radius', {})
    rows.append(dict(id=a['instance']['id'], I=a['instance']['I'], gamma=a['margin'], nominal=a['nominal_objective'], status=a['status'],
                     ok=ok, cost=r['objective'] if ok else None,
                     radius=rad.get('lower') if ok and rad.get('status') in ('NUMERICAL_BRACKET', 'NUMERICAL_CLIPPED') else None))
Mg = pd.DataFrame(rows)
if len(Mg):
    Mg['rel'] = Mg.gamma / Mg.nominal
    Mg.to_csv(RES / 'audit_margin.csv', index=False)
    lines = [r'\begin{tabular}{rrrrrrr}', r'\toprule',
             r'$\gamma$ & Median $\gamma/V$ (\%) & $n$ & Valid. & Inf. & Median cost & Median radius (\%) \\', r'\midrule']
    for gm, x in Mg.groupby('gamma'):
        lines.append(f"{gm:g} & {med(100*x.rel, '.2f')} & {len(x)} & {int(x.ok.sum())} & {int((x.status=='SOLVER_INFEASIBLE').sum())} & "
                     f"{med(x.cost)} & {med(100*x.radius, '.2f')} \\\\")
    lines += [r'\bottomrule', r'\end{tabular}']
    (TAB / 'audit_margin.tex').write_text('\n'.join(lines) + '\n')
    for gm, name in [(.02, 'Two'), (.5, 'Half')]:
        x = Mg[Mg.gamma == gm]
        macros[f'Margin{name}Valid'] = int(x.ok.sum())
        macros[f'Margin{name}Radius'] = med(100 * x.radius, '.2f')
        macros[f'Margin{name}Cost'] = med(x.cost)
    x = Mg.dropna(subset=['radius', 'cost'])
    if len(x) > 2:
        macros['MarginRadiusCostCorr'] = f"{np.corrcoef(x.cost, x.radius)[0,1]:.2f}"
    fig, ax = plt.subplots(1, 2, figsize=(4.6, 2.4))
    for (gm, x), mk in zip(Mg[Mg.ok].groupby('gamma'), ['o', 's', '^', 'D', 'v', 'P']):
        ax[0].scatter(100 * x.rel, 100 * x.radius, s=9, marker=mk, label=f'$\\gamma={gm:g}$')
    ax[0].set_xscale('log'); ax[0].set_xlabel(r'$\gamma$ relative to nominal value (%)'); ax[0].set_ylabel('Radius (%)')
    ok = Mg[Mg.ok]
    ax[1].plot(*zip(*[(gm, x.cost.median()) for gm, x in ok.groupby('gamma')]), marker='o', label='Median intervention objective')
    ax[1].set_xscale('log'); ax[1].set_xlabel(r'Margin $\gamma$'); ax[1].set_ylabel('Median edit cost (circles)')
    ax2 = ax[1].twinx(); ax2.plot(*zip(*[(gm, 100*x.radius.median()) for gm, x in ok.groupby('gamma')]), marker='s', color='C3')
    ax2.set_ylabel('Median radius, % (squares)')
    ax[0].legend(frameon=False, fontsize=5.5); [a.grid(alpha=.3) for a in ax]
    ax[0].set_title('(a)', loc='left'); ax[1].set_title('(b)', loc='left')
    fig.tight_layout(); fig.savefig(FIG / 'audit_margin.pdf'); fig.savefig(FIG / 'audit_margin.png', dpi=150); plt.close(fig)

# Naive scenario handling.
rows = []
for a in raw['naive']:
    c, n = a['correct'], a['naive']
    cv = a.get('correct_verification', {}); nv = a.get('naive_verification', {})
    if c['status'] == 'SOLVER_VALIDATED':
        assert cv.get('valid') is True, a['key']
    rows.append(dict(source='primary' if a['source'] == 'primary' else 'stress', mode=a['mode'], family=a['family'],
                     cstat=c['status'], nstat=n['status'], cok=c['status'] == 'SOLVER_VALIDATED', nok=n['status'] == 'SOLVER_VALIDATED',
                     ninvalid=n['status'] == 'SOLVER_VALIDATED' and not nv.get('valid', False),
                     ccost=c['objective'] if c['status'] == 'SOLVER_VALIDATED' else None,
                     ncost=n['objective'] if n['status'] == 'SOLVER_VALIDATED' else None))
N = pd.DataFrame(rows)
if len(N):
    N.to_csv(RES / 'audit_naive.csv', index=False)
    both = N[N.cok & N.nok]
    under = both[both.ncost < both.ccost - TOL]
    false_expl = N[N.nok & ~N.cok & (N.cstat == 'SOLVER_INFEASIBLE')]
    macros.update(NaiveScenarios=len(N), NaiveValidated=int(N.nok.sum()), NaiveInvalid=int(N.ninvalid.sum()),
                  NaiveUnder=len(under), NaiveFalseExplain=len(false_expl), NaiveBoth=len(both),
                  NaiveUnderMedian=f"{100*np.median((under.ccost-under.ncost)/under.ccost):.1f}" if len(under) else '--',
                  NaiveCorrectValidated=int(N.cok.sum()))
    lines = [r'\begin{tabular}{llrrrrr}', r'\toprule',
             r'Menus & Family & Scenarios & Correct & Naive & Invalid & Understated \\', r'\midrule']
    for (src, fam), x in N.groupby(['source', 'family']):
        b = x[x.cok & x.nok]
        lines.append(f"{'Primary' if src=='primary' else 'Study 1'} & {fam.capitalize()} & {len(x)} & {int(x.cok.sum())} & {int(x.nok.sum())} & {int(x.ninvalid.sum())} & "
                     f"{int((b.ncost < b.ccost - TOL).sum())} \\\\")
    lines += [r'\bottomrule', r'\end{tabular}']
    (TAB / 'audit_naive.tex').write_text('\n'.join(lines) + '\n')

(TAB / 'audit_numbers.tex').write_text(''.join(f'\\newcommand{{\\{k}}}{{{v}}}\n' for k, v in sorted(macros.items())))
json.dump({k: v for k, v in macros.items()}, open(RES / 'audit_summary.json', 'w'), indent=1, default=str)
print(json.dumps(macros, indent=1, default=str))
