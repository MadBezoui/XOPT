"""Check separately recomputed witnesses against immutable baseline interventions.

This checks recorded identities and numerical witness consistency, not MILP optimality
or an independently solved oracle. UNRESOLVED rows block this gate.
"""
import hashlib
import json
import math
from pathlib import Path
from provenance import verify_sources


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def read_rows(path):
    data = path.read_bytes()
    return digest_bytes(data), [(json.loads(line), digest_bytes(line)) for line in data.splitlines() if line.strip()]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(root):
    root = Path(root)
    res = root / 'experiments/results'
    baseline_hash, baseline_rows = read_rows(res / 'single_lever.jsonl')
    expected = {}
    for row, line_hash in baseline_rows:
        if row['status'] == 'RESTRICTED_SOLVER_OPTIMAL':
            key = (row['profile'], row['key'])
            require(key not in expected, f'duplicate historical baseline: {key}')
            expected[key] = (row, line_hash)
    require(len(expected) == 94, 'expected 94 historical baseline interventions')
    parents = {}
    for profile in ('main','scale','long'):
        filehash, rows = read_rows(res / (profile+'.jsonl'))
        for row, linehash in rows:
            if row['job']['method'] != 'ccg':
                continue
            key = (profile, row['key'])
            require(key not in parents, f'duplicate historical parent: {key}')
            parents[key] = (row, linehash, filehash)
    _, rows = read_rows(res / 'corrections_20261028/single_lever_revalidated.jsonl')
    seen = set()
    for row, _ in rows:
        key = (row['profile'], row['key'])
        require(key in expected and key in parents and key not in seen, f'unexpected or duplicate revalidation: {key}')
        seen.add(key)
        old, oldline = expected[key]
        parent, pline, pfile = parents[key]
        require(row['historical_file_sha256'] == baseline_hash and row['historical_record_sha256'] == oldline, f'historical baseline identity mismatch: {key}')
        require(row['parent_file_sha256'] == pfile and row['parent_record_sha256'] == pline, f'parent identity mismatch: {key}')
        verify_sources(root, row['source_sha256'], current_only=True, required={
            'experiments/src/XOPT.jl', 'experiments/src/anytime.jl',
            'experiments/scripts/revalidate_single_lever_20261028.jl'})
        require(row['status'] == 'VALIDATED' and row['forward_status'] == 'OPTIMAL', f'unresolved intervention: {key}')
        v = row['verification']; w = row['witness']; m=parent['instance']; job=parent['job']
        require(v['valid'] is True and v['arithmetic'] == 'Float64' and v['exact_certificate'] is False, f'bad numerical verification: {key}')
        require(v['oracle_status'] in ('OPTIMAL','INFEASIBLE'), f'unresolved oracle: {key}')
        require(w['status'] == 'FEASIBLE_VALIDATED', f'wrong witness status: {key}')
        n, t = int(m['I']), int(m['T']); size=n*t
        for field in ('delta','y','q','state'):
            require(len(w[field]) == size and all(isinstance(x,(int,float)) and math.isfinite(x) for x in w[field]), f'invalid witness {field}: {key}')
        amount=float(old['amount']); historical=float(old['objective'])
        require(amount >= 0 and row['historical_amount'] == amount and row['historical_objective'] == historical, f'historical intervention changed: {key}')
        i, period, bit = parent['foil'][0]; idx=(period-1)*n+(i-1)
        require(len(parent['foil']) == 1 and 0 <= idx < size and bit in (0,1), f'invalid historical foil: {key}')
        for k, value in enumerate(w['delta']):
            wanted=(1-2*bit)*amount if k == idx else 0.0
            require(abs(value-wanted) <= 1e-9, f'witness intervention differs: {key}')
        cost=amount/float(m['fixed'][idx]) + (.01 if amount > 1e-6 else 0.)
        residual=abs(cost-historical)
        require(residual <= 1e-5 and abs(row['objective_residual']-residual) <= 1e-10, f'baseline objective mismatch: {key}')
        tol=1e-5
        require(abs(w['y'][idx]-bit)<=tol, f'foil mismatch: {key}')
        require(all(-tol<=y<=1+tol and abs(y-round(y))<=tol for y in w['y']), f'nonbinary witness: {key}')
        require(all(q>=-tol for q in w['q']) and all(s>=-tol for s in w['state']), f'negative witness: {key}')
        for tt in range(t):
            require(sum(w['q'][tt*n+i] for i in range(n)) <= m['capacity'][tt]+tol, f'capacity violation: {key}')
            for ii in range(n):
                k=tt*n+ii; prev=m['initial'][ii] if tt==0 else w['state'][k-n]
                demand=m['demand'][k] if m['family']=='retail' else 0.
                require(abs(w['state'][k]-m['retention']*prev-w['q'][k]+demand)<=tol, f'balance violation: {key}')
                require(w['q'][k]<=w['y'][k]*m['capacity'][tt]+tol, f'activation violation: {key}')
                if m['family']=='hospital':
                    require(w['state'][k]>=m['demand'][k]-tol, f'demand violation: {key}')
                elif tt==t-1:
                    require(abs(w['state'][k])<=tol, f'terminal stock violation: {key}')
        witness_cost=sum((m['fixed'][k]+w['delta'][k])*w['y'][k]+m['unit'][k]*w['q'][k]+m['holding'][k]*w['state'][k] for k in range(size))
        require(abs(witness_cost-v['witness_cost'])<=1e-5, f'witness cost mismatch: {key}')
        offset = -job['margin'] if job['mode']=='strong' else job['epsilon']
        if v['oracle_status']=='INFEASIBLE':
            require(job['mode']=='strong', f'weak oracle infeasible: {key}')
        else:
            require(v['oracle_bound'] is not None and witness_cost <= v['oracle_bound']+offset+v['comparison_tolerance']+1e-8, f'oracle comparison failed: {key}')
    require(seen == set(expected), 'missing baseline intervention revalidations')
    return {'count':len(seen),'validated':len(seen),'scope':'fresh reconstructed witnesses for historical interventions; Float64, not intervention optimality or original witnesses'}

if __name__ == '__main__':
    import sys
    print(json.dumps(validate(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[2]), indent=2))
