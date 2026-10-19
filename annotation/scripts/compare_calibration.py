"""Compare three calibration or batch submissions; agreement is not accuracy."""
import argparse,json
from collections import Counter
from itertools import combinations
from pathlib import Path
from common import ROOT,read_records,validate,dump
def main():
 p=argparse.ArgumentParser();p.add_argument('files',nargs=3);p.add_argument('--output',required=True)
 p.add_argument('--expected',type=Path,default=ROOT/'calibration'/'manifest.json',help='Calibration or A/B/C manifest; all three inputs must cover it exactly')
 a=p.parse_args()
 if len({Path(f).resolve() for f in a.files})!=3:raise ValueError('Provide three distinct reviewer files, not duplicate paths.')
 expected=json.loads(a.expected.read_text(encoding='utf8'))['case_ids']
 if not expected or len(set(expected))!=len(expected):raise ValueError('Expected manifest must have nonempty unique case IDs.')
 sources={r['case_id']:r for r in read_records(ROOT/'source'/'cases.jsonl')};groups=[]
 for file in a.files:
  rows=read_records(file);v=validate(rows,sources,expected)
  if not v['passed']:raise ValueError(f'{file}: {v["errors"]}')
  groups.append({r['case_id']:r for r in rows})
 fields=[('eligibility','scope'),('eligibility','property_status'),('eligibility','binary_task'),('outcome','appellate_disposition'),('outcome','binary_label')]
 comparisons=[];disagreements=[]
 for i,j in combinations(range(3),2):
  for section,key in fields:
   pairs=[(groups[i][c][section][key],groups[j][c][section][key]) for c in expected]
   agree=sum(x==y for x,y in pairs)/len(pairs);cx=Counter(x for x,y in pairs);cy=Counter(y for x,y in pairs)
   chance=sum(cx[v]*cy[v] for v in set(cx)|set(cy))/len(pairs)**2
   comparisons.append({'reviewer_files':[a.files[i],a.files[j]],'field':f'{section}.{key}','agreement':agree,
                       'cohen_kappa':(agree-chance)/(1-chance) if chance<1 else None})
 for c in expected:
  differences={f'{s}.{k}':[g[c][s][k] for g in groups] for s,k in fields if len({json.dumps(g[c][s][k]) for g in groups})>1}
  if differences:disagreements.append({'case_id':c,'differences':differences})
 dump(a.output,{'cases':len(expected),'expected_manifest':str(a.expected),'pairwise':comparisons,'disagreements':disagreements,
                'note':'Core-field comparison only. Shared-model agreement is not correctness; review extra features separately. Human adjudication required; no majority-vote gold labels. Report previously discussed cases separately from fresh independent agreement.'})
 print('Saved comparison for',len(expected),'cases; disagreements:',len(disagreements))
if __name__=='__main__':main()
