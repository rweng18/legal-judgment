"""Compare independent annotations; agreement is not accuracy."""
import argparse,json
from collections import Counter
from itertools import combinations
from pathlib import Path
from common import ROOT,read_records,validate,dump
def main():
 p=argparse.ArgumentParser();p.add_argument('files',nargs=3);p.add_argument('--output',required=True);a=p.parse_args()
 expected=json.loads((ROOT/'calibration'/'manifest.json').read_text(encoding='utf8'))['case_ids']
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
 dump(a.output,{'cases':12,'pairwise':comparisons,'disagreements':disagreements,
                'note':'Small calibration sample; shared-model agreement is not correctness. Human adjudication required; no majority-vote gold labels.'})
 print('Saved calibration comparison; disagreements:',len(disagreements))
if __name__=='__main__':main()
