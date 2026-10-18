"""All-query comparison with the independently implemented published scheme."""
from pathlib import Path
import json, statistics, collections

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / 'experiments/results'
(ROOT/'article/tables').mkdir(parents=True,exist_ok=True)
records = [json.loads(s) for s in (RES/'external_reference.jsonl').read_text().splitlines()]
assert len(records) == 168
pairs = collections.defaultdict(dict)
for a in records:
    key = (a['profile'], a['key'])
    assert a['method'] not in pairs[key]
    pairs[key][a['method']] = a
    if a['result']['status'] == 'SOLVER_VALIDATED':
        assert a['verification']['valid']
assert len(pairs) == 84 and all(set(p) == {'xopt','literature'} for p in pairs.values())
disagreements = []
errors = []
for key,p in pairs.items():
    x,l = (p[m]['result'] for m in ['xopt','literature'])
    if x['status'] != l['status']:
        disagreements.append({'key':key,'xopt':x['status'],'literature':l['status']})
    if x['status'] == l['status'] == 'SOLVER_VALIDATED':
        errors.append(abs(x['objective']-l['objective']))
summary = {'paired_queries':len(pairs),'runs':len(records),'jointly_validated':len(errors),
           'status_disagreements':disagreements,'max_objective_difference':max(errors,default=None),
           'independent_author_software_execution':False,'reference':'arXiv:2510.17624v2, Algorithm 1 and equation (14)',
           'methods':{}}
lines=[]
for method in ['xopt','literature']:
    rr=[a['result'] for a in records if a['method']==method]
    counts=dict(collections.Counter(a['status'] for a in rr))
    median=statistics.median(a['seconds'] for a in rr)
    summary['methods'][method]={'counts':counts,'median_seconds_all_queries':median}
    lines.append(' & '.join([{'xopt':'Pattern CCG','literature':'Literature CG (reimplementation)'}[method],str(len(rr)),str(counts.get('SOLVER_VALIDATED',0)),str(counts.get('SOLVER_INFEASIBLE',0)),str(sum(n for k,n in counts.items() if k not in ['SOLVER_VALIDATED','SOLVER_INFEASIBLE'])),f'{median:.3f}'])+r' \\')
(RES/'external_summary.json').write_text(json.dumps(summary,indent=2))
(ROOT/'article/tables/external_reference.tex').write_text('\\begin{tabular}{lrrrrr}\n\\toprule\nMethod & $n$ & Valid. & Inf. & Unresolved & Median s \\\\\n\\midrule\n'+'\n'.join(lines)+'\n\\bottomrule\n\\end{tabular}\n')
macros={'ExternalPairs':len(pairs),'ExternalJoint':len(errors),'ExternalDisagreements':len(disagreements),
        'ExternalMaxDiff':f'{max(errors,default=0):.2e}'}
(ROOT/'article/tables/external_numbers.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+str(v)+'}' for k,v in macros.items())+'\n')
print(json.dumps(summary,indent=2))
