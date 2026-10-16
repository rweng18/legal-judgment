import argparse
import json
from pathlib import Path
from common import ROOT,read_records,validate,dump

def main():
 p=argparse.ArgumentParser(description='Validate one chunk or a whole batch; no external packages needed.')
 p.add_argument('annotations');p.add_argument('--source',default=str(ROOT/'source'/'cases.jsonl'))
 p.add_argument('--expected',required=True,help='Chunk .expected.json or batch/calibration manifest.json')
 p.add_argument('--partial',action='store_true',help='Permit missing expected IDs for an explicitly partial checkpoint')
 p.add_argument('--report',required=True);a=p.parse_args()
 try:
  rows=read_records(a.annotations);sources={r['case_id']:r for r in read_records(a.source)}
  expected=json.loads(Path(a.expected).read_text(encoding='utf8'))['case_ids']
  result=validate(rows,sources,expected,a.partial)
 except (ValueError,KeyError,OSError,TypeError) as e:result={'passed':False,'errors':[str(e)]}
 dump(a.report,result);print(json.dumps({k:v for k,v in result.items() if k!='evidence_offsets'},indent=2))
 return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())

