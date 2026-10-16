"""Merge explicitly selected final files. Never auto-select between reviewers."""
import argparse,json
from pathlib import Path
from common import ROOT,read_records,validate,dump,write_jsonl
def main():
 p=argparse.ArgumentParser();p.add_argument('files',nargs='+');p.add_argument('--output',required=True)
 p.add_argument('--expected',required=True,help='Manifest containing case_ids; source/all_expected.json for all 506')
 p.add_argument('--source',default=str(ROOT/'source'/'cases.jsonl'));p.add_argument('--partial',action='store_true');a=p.parse_args()
 rows=[r for f in a.files for r in read_records(f)];sources={r['case_id']:r for r in read_records(a.source)}
 expected=json.loads(Path(a.expected).read_text(encoding='utf8'))['case_ids']
 result=validate(rows,sources,expected,a.partial);dump(str(a.output)+'.validation.json',result)
 if not result['passed']:print('Merge refused: fix errors in validation report.');return 1
 write_jsonl(a.output,sorted(rows,key=lambda r:r['case_id']));print(f'Merged {len(rows)} cases. Existing duplicates are errors, never silently overwritten.');return 0
if __name__=='__main__':raise SystemExit(main())

