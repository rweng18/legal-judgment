import argparse,json,math,random,statistics
from collections import Counter
from common import ROOT,read_records,dump,validate
def main():
 p=argparse.ArgumentParser();p.add_argument('annotations');p.add_argument('--output',required=True)
 p.add_argument('--source',default=str(ROOT/'source'/'cases.jsonl'));a=p.parse_args()
 rows=read_records(a.annotations);sources={r['case_id']:r for r in read_records(a.source)}
 report=validate(rows,sources)
 if not report['passed']:dump(a.output,report);raise SystemExit(1)
 included=[r for r in rows if r['eligibility']['binary_task']=='include']
 training=[r['case_id'] for r in included if sources[r['case_id']]['date_filed'][:4]<='2020']
 rng=random.Random(20261019);audit=rng.sample(sorted(training),math.ceil(.1*len(training))) if training else []
 lengths=[sources[r['case_id']]['word_count'] for r in included]
 counts={name:dict(Counter(str(r['outcome']['binary_label']) for r in included if lo<=int(sources[r['case_id']]['date_filed'][:4])<=hi))
         for name,lo,hi in [('train',2010,2020),('validation',2021,2022),('test',2023,2024)]}
 result={'annotated_cases':len(rows),'eligibility':dict(Counter(r['eligibility']['binary_task'] for r in rows)),
         'outcomes_all_cases':dict(Counter(r['outcome']['appellate_disposition'] for r in rows)),
         'included_class_counts':dict(Counter(str(r['outcome']['binary_label']) for r in included)),
         'review_status':dict(Counter(r['run']['review_status'] for r in rows)),
         'planned_period_class_counts':counts,'needs_review':[r['case_id'] for r in rows if r['quality']['needs_review']],
         'unknown_field_counts':{key:sum(r['facts'][key]=='unclear' for r in rows) for key in ['premises_type','location','injured_role']},
         'accepted_words':{'min':min(lengths),'median':statistics.median(lengths),'mean':statistics.mean(lengths),'max':max(lengths)} if lengths else {},
         'random_training_audit_ids':audit,'audit_seed':20261019,
         'evaluation_needing_human_review':[r['case_id'] for r in rows if sources[r['case_id']]['date_filed'][:4]>='2021' and r['run']['review_status']=='llm_draft'],
         'note':'Availability and annotation statistics, not classifier metrics. Freeze merged version before drawing the training audit. Family grouping remains required.'}
 dump(a.output,result);print(json.dumps(result,indent=2))
if __name__=='__main__':main()

