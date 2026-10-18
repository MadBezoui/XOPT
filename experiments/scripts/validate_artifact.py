from pathlib import Path
import json,hashlib,math,collections
ROOT=Path(__file__).resolve().parents[2];RES=ROOT/'experiments/results'
assert sorted(p.name for p in ROOT.iterdir() if p.name!='.git')==['article','data','experiments'],'Root must contain exactly three content directories (excluding Git metadata)'
manifest=json.loads((ROOT/'data/metadata/downloads.json').read_text())
for entry in manifest:
 p=ROOT/entry['file'];assert p.stat().st_size==entry['bytes'];assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256'],p
source=hashlib.sha256((ROOT/'experiments/src/XOPT.jl').read_bytes()).hexdigest()
profiles={'correctness':40,'main':120,'sensitivity':72,'scale':36,'capacity':16,'long':12,'multifoil':24}
allrecords=[]
for profile,n in profiles.items():
 records=[json.loads(l) for l in (RES/(profile+'.jsonl')).read_text().splitlines()]
 assert len(records)==n,(profile,len(records),n)
 assert len({r['key'] for r in records})==n
 for r in records:
  assert r['source_sha256']==source
  m=r['instance'];assert len(m['demand'])==m['I']*m['T']
  if r['status']=='SOLVER_VALIDATED':assert r['verification']['valid']
 allrecords.extend(records)
# Check monotonicity on the same instances, not across differing feasible subsets.
sens=[r for r in allrecords if r['profile']=='sensitivity'];groups=collections.defaultdict(list)
for r in sens:groups[(r['instance']['id'],r['job']['mode'],r['job']['epsilon'])].append(r)
for key,g in groups.items():
 g=sorted(g,key=lambda r:r['job']['K']);vals=[r['result']['objective'] if r['status']=='SOLVER_VALIDATED' else math.inf for r in g]
 assert all(b<=a+1e-5 for a,b in zip(vals,vals[1:])),(key,vals)
rr=[json.loads(l) for l in (RES/'robustness.jsonl').read_text().splitlines()];assert len(rr)==50
assert all(r['radius']['status'] in ['NUMERICAL_BRACKET','NUMERICAL_CLIPPED'] for r in rr)
assert all(r['radius']['lower']>0 for r in rr if r['mode']=='strong')
sl=[json.loads(l) for l in (RES/'single_lever.jsonl').read_text().splitlines()];assert len(sl)==108
assert all(r['verification']['valid'] for r in sl if r['status']=='RESTRICTED_SOLVER_OPTIMAL')
cert=json.loads((RES/'saved_witness_validation.json').read_text());assert cert['all_valid'];assert cert['checked']==sum(r['status']=='SOLVER_VALIDATED' for r in allrecords)
report={'passed':True,'primary_runs':len(allrecords),'raw_files_verified':len(manifest),'saved_witnesses_verified':cert['checked'],'radius_audits':len(rr),'single_lever_runs':len(sl),'core_sha256':source,'checks':['three content directories/no root files (Git metadata excluded)','download checksums','expected run counts and unique keys','core provenance','saved witness numerical feasibility and reported oracle bounds','sparsity monotonicity','radius bracketing','single-lever validity']}
external=json.loads((RES/'external_summary.json').read_text())
external_records=[json.loads(l) for l in (RES/'external_reference.jsonl').read_text().splitlines()]
assert len(external_records)==168
for r in external_records:
 for name,sha in r['source_sha256'].items():
  assert hashlib.sha256((ROOT/'experiments/src'/name).read_bytes()).hexdigest()==sha
 if r['result']['status']=='SOLVER_VALIDATED':assert r['verification']['valid']
assert external['paired_queries']==84
assert not external['status_disagreements']
assert external['max_objective_difference']<1e-5
report['external_comparison_runs']=external['runs']
revision=json.loads((RES/'revision_summary.json').read_text())
fresh=json.loads((RES/'revision_validation.json').read_text())
assert revision['runs']==250 and fresh['valid']
assert fresh['checked']==revision['retained_feasible']
assert fresh['validator_sha256']==hashlib.sha256((ROOT/'experiments/scripts/validate_revision.jl').read_bytes()).hexdigest()
for profile,n in {'extended':90,'compound':128,'capacity_stress':32,'timing_repairs':6}.items():
 path=RES/f'revision_{profile}.jsonl';rows=[json.loads(l) for l in path.read_text().splitlines()]
 assert len(rows)==n and len({r['key'] for r in rows})==n
 for r in rows:
  for name,sha in r['source_sha256'].items():
   assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha
 digest=hashlib.sha256(path.read_bytes()).hexdigest()
 for r in fresh['records']:
  if r['profile']==profile:assert r['valid'] and r['input_sha256']==digest
report['supplementary_runs']=revision['runs']
report['supplementary_retained_attempts']=revision['retained_attempts']
report['supplementary_incumbents_freshly_verified']=fresh['checked']
report['checks'].extend(['supplementary counts, source hashes and saved-record digests','fresh supplementary incumbent checks'])
report['arithmetic']='Float64, tolerance-based checks; no exact proof certificates'
(RES/'validation_report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
# Portable manifest of deliverable sources and computed outputs (omit volatile TeX caches).
files=[]
for folder in ['article','experiments','data']:
 for p in sorted((ROOT/folder).rglob('*')):
  if p.is_file() and not any(x in p.parts for x in ['archive','archive_v1','release','previews']) and p.suffix not in ['.zip'] and p.name not in ['artifact_sha256.json','validation_report.json'] and p.suffix not in ['.aux','.log','.fdb_latexmk','.fls','.out','.pyc'] and '.DS_Store' not in p.name:
   files.append({'file':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(ROOT/'experiments/results/artifact_sha256.json').write_text(json.dumps(files,indent=2))
