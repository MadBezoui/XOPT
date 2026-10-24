"""Fetch public source bytes with curl, then create traceable aggregate series.
Raw observations are never replaced with synthetic values.
"""
from pathlib import Path
import csv, datetime as dt, hashlib, io, json, re, subprocess, zipfile
from collections import defaultdict, Counter
import openpyxl
ROOT=Path(__file__).resolve().parents[2]; RAW=ROOT/'data/raw'; OUT=ROOT/'data/processed'; META=ROOT/'data/metadata'
for p in [RAW,OUT,META]: p.mkdir(parents=True,exist_ok=True)
NHS='https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/'
files=[('2024-04','2024/11/Monthly-AE-April-2024-revised.csv'),('2024-05','2024/06/Monthly-AE-May-2024.csv'),('2024-06','2024/07/Monthly-AE-June-2024.csv'),('2024-07','2024/11/Monthly-AE-July-2024-revised.csv'),('2024-08','2024/09/Monthly-AE-August-2024.csv'),('2024-09','2024/10/Monthly-AE-September-2024.csv'),('2024-10','2025/05/Monthly-AE-October-2024-revised.csv'),('2024-11','2025/05/Monthly-AE-November-2024-revised.csv'),('2024-12','2025/01/Monthly-AE-December-2024.csv'),('2025-01','2025/02/Monthly-AE-January-2025.csv'),('2025-02','2025/05/Monthly-AE-February-2025-revised.csv'),('2025-03','2025/04/Monthly-AE-March-2025.csv')]
manifest=[]
# An archived manifest is verified, never rewritten, so its retrieval dates and checksums stay authoritative.
ARCHIVED={e['file']:e for e in json.loads((META/'downloads.json').read_text())} if (META/'downloads.json').exists() else {}
def fetch(url,name,license):
 p=RAW/name
 if not p.exists() or p.stat().st_size==0:
  subprocess.run(['curl','-sS','-L','--fail','--retry','3',url,'-o',str(p)+'.part'],check=True)
  Path(str(p)+'.part').replace(p)
 assert p.stat().st_size>0
 key=str(p.relative_to(ROOT));digest=hashlib.sha256(p.read_bytes()).hexdigest()
 if key in ARCHIVED:
  assert ARCHIVED[key]['sha256']==digest and ARCHIVED[key]['bytes']==p.stat().st_size,('checksum mismatch',key)
  manifest.append(ARCHIVED[key])
 else:
  manifest.append(dict(file=key,url=url,bytes=p.stat().st_size,sha256=digest,license=license,retrieved_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
 return p
retail=fetch('https://archive.ics.uci.edu/static/public/352/online+retail.zip','online_retail.zip','CC-BY-4.0')
nhsfiles=[(date,fetch(NHS+url,'nhs_'+date+'.csv','Open Government Licence v3.0')) for date,url in files]
if not ARCHIVED: (META/'downloads.json').write_text(json.dumps(manifest,indent=2))
# Full-year Jan-Nov 2011, complete Monday-Sunday weeks, all countries.
# Product selection based ONLY on Jan-Mar calibration sales, separate from Apr-Nov test windows.
weekly=defaultdict(int); totals=Counter(); kept=0; excluded=Counter(); descriptions={}
with zipfile.ZipFile(retail) as z:
 xlsx=[n for n in z.namelist() if n.endswith('.xlsx')][0]
 with z.open(xlsx) as stream:
  wb=openpyxl.load_workbook(stream,read_only=True,data_only=True)
  rows=wb.active.iter_rows(values_only=True); header=next(rows)
  for row in rows:
   invoice,code,desc,quantity,date,price,customer,country=row[:8]
   if str(invoice).upper().startswith('C') or not quantity or quantity<=0 or not price or price<=0:
    excluded['cancelled_nonpositive']+=1; continue
   code=str(code)
   if not re.fullmatch(r'\d{5}[A-Za-z]?',code): excluded['nonproduct_code']+=1; continue
   if not isinstance(date,dt.datetime): excluded['invalid_date']+=1; continue
   day=date.date(); monday=day-dt.timedelta(days=day.weekday())
   if dt.date(2011,1,1)<=day<=dt.date(2011,3,31): totals[code]+=quantity
   if dt.date(2011,1,3)<=monday<=dt.date(2011,11,21): weekly[(code,monday)]+=int(quantity); kept+=1
   descriptions[code]=str(desc)
 wb.close()
products=[c for c,n in sorted(totals.items(),key=lambda x:(-x[1],x[0]))[:30]]
weeks=[dt.date(2011,1,3)+dt.timedelta(weeks=k) for k in range(47)]
with (OUT/'retail_weekly.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['series','period','date','demand','description'])
 for code in products:
  for k,day in enumerate(weeks,1): w.writerow([code,k,day,weekly[(code,day)],descriptions[code]])
# Source header is inspected; Type 1 attendances are selected (not corrected admission metrics).
nhs={}; nhsheaders={}
for date,p in nhsfiles:
 text=p.read_bytes().decode('utf-8-sig',errors='replace')
 rows=list(csv.reader(io.StringIO(text)))
 idx=next(i for i,r in enumerate(rows) if any('Org Code' in c for c in r))
 header=rows[idx]; nhsheaders[date]=header
 ci=next(i for i,c in enumerate(header) if 'Org Code' in c)
 ni=next(i for i,c in enumerate(header) if 'Org name' in c or 'Org Name' in c)
 ai=next(i for i,c in enumerate(header) if 'A&E attendances Type 1' in c)
 records={}
 for r in rows[idx+1:]:
  if len(r)<=ai: continue
  code=r[ci].strip()
  try: val=int(r[ai].replace(',','').strip())
  except ValueError: continue
  if len(code)==3 and code.startswith('R') and val>0: records[code]=(val,r[ni])
 nhs[date]=records
common=set.intersection(*(set(v) for v in nhs.values()))
# Rank only April; retain 30 complete providers. No interpolation.
providers=sorted(common,key=lambda c:(-nhs['2024-04'][c][0],c))[:30]
assert len(providers)>=10,(len(providers),nhsheaders)
with (OUT/'nhs_monthly.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['series','period','date','demand','description'])
 for code in providers:
  for k,(date,_) in enumerate(files,1): w.writerow([code,k,date,nhs[date][code][0],nhs[date][code][1]])
report={'retail_kept_rows':kept,'retail_exclusions':dict(excluded),'retail_products':products,'retail_weeks':len(weeks),'nhs_complete_providers':len(common),'nhs_selected':providers,'nhs_headers':nhsheaders,'real': ['sales quantities','Type 1 A&E attendances'], 'constructed':['setup and hiring costs','holding costs','workforce persistence','capacities','foil queries','capacity intervention menu'],'note':'NHS workload-inspired staffing benchmark, no patient trajectories or inferred ICU occupancy.'}
(META/'preprocessing.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='nhs_headers'},indent=2))
