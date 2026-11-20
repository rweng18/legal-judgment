"""Versioned, training-audit-motivated mask corrections; no case-ID rules."""
import re
from common import *

def revised_mask(text):
    # An abbreviation can finish a sentence immediately before an operative order.
    starts={0,len(text)}
    for a,b in policy_spans(text,'new'): starts.update([a,b])
    for m in re.finditer(r'(?<=[.!?])\s+(?=(?:It is hereby )?[Oo][Rr][Dd][Ee][Rr][Ee][Dd] that\b|[“\"‘])',text):
        starts.update([m.start(),m.end()])
    parts=[];deleted=[]
    points=sorted(starts)
    for a,b in zip(points,points[1:]):
        part=text[a:b]
        if not part.strip(): continue
        rule=NEW.outcome_rule(part.strip())
        # A cited quotation states an earlier rule. Do not classify its internal
        # 'Supreme Court properly ...' language as the current appeal's order.
        quoted_rule=bool(re.match(r'^\s*[“\"‘]',part) and re.search(r'[”\"’]\s*\([^)]*\bv\b.*\)\.?\s*$',part))
        if not rule or quoted_rule:
            parts.append(part.strip());continue
        spans=[]
        joined=re.search(r',?\s+and\s+we\s+(?:affirm|reverse|vacate)\b[^.]*',part,re.I)
        if rule=='we_current_disposition' and joined:
            spans=[(joined.start(),joined.end())]
        else:
            # Keep trailing citations to prior decisions; discard the current
            # court's result clause. This rule is applied uniformly to all cases.
            cite=re.search(r'\(\s*(?:(?:see|cf\.?|compare)\s+)?[^()]{0,100}\bv\s+[^()]*',part,re.I)
            spans=[(0,cite.start() if cite else len(part))]
        pos=0
        for lo,hi in spans:
            parts.append(part[pos:lo].strip())
            deleted.append({'start':a+lo,'end':a+hi,'text':part[lo:hi],'reason':rule})
            pos=hi
        parts.append(part[pos:].strip())
    kept=' '.join(x for x in parts if x)
    return kept,deleted

def main():
    target=HERE/'inputs/quality_v1'
    if (target/'protocol.json').exists():raise FileExistsError('Quality protocol already frozen')
    rows=load_rows();out=[];logs=[]
    for r in rows:
        full=r['texts']['FULL'];masked,deleted=revised_mask(full)
        assert masked.strip()
        loss=len(full.split())-len(masked.split());assert 0<=loss<len(full.split())
        texts={'REVISED':masked};log={'case_id':r['case_id'],'deleted':deleted,'removed_words':loss,'random':{}}
        for seed in SEEDS:
            name=f'REVISED_RANDOM_{seed}';texts[name],log['random'][name]=random_remove(full,loss,seed,r['case_id'])
            assert len(texts[name].split())==len(masked.split())
        out.append({'case_id':r['case_id'],'texts':texts});logs.append(log)
    byid={r['case_id']:r for r in out}
    assert 'properly shifted' in byid['NY-4509516']['texts']['REVISED']
    assert 'A defendant who moves' in byid['NY-5950295']['texts']['REVISED']
    assert 'we affirm' not in byid['NY-5950295']['texts']['REVISED']
    assert byid['NY-4427636']['texts']['REVISED'].startswith('In an action')
    assert 'Zanki v Cahill' in byid['NY-5980564']['texts']['REVISED']
    jsonl(target/'variants.jsonl',out);jsonl(target/'removal_logs.jsonl',logs)
    write(target/'protocol.json',{'version':'quality_v1','date':'2026-11-19',
        'authorization':'User agreed to recommendations and requested experiments.',
        'change':'Uniform abbreviation/order boundaries, quotation boundaries, preserve cited quoted rules, split joined and-we disposition, preserve trailing case citations.',
        'source_review':'User reports completed human review; exact final-test review manifest still not supplied. No blanket status promotion.',
        'dedup_remove':['NY-6112018'],'dedup_retain':'NY-4306359',
        'dedup_scope':'Confirmed Mann duplicate only; other global candidate pairs remain grouped pending confirmation. Not a claim of complete corpus deduplication.',
        'experiments':'Separate dedup-only, mask-only, and combined interventions; all selected classifiers fixed C; revised five-seed controls for LR and BERT.',
        'selection':'Rule design based on four previously flagged training cases, two of each class; no validation predictions used.',
        'final_test':'Not accessed; candidate IDs/labels still require a specific reviewed manifest.',
        'sha256':{n:digest((target/n).read_bytes()) for n in ['variants.jsonl','removal_logs.jsonl']},
        'code_sha256':digest(Path(__file__).read_bytes())})
    print('Frozen quality variants for',len(out),'cases')

if __name__=='__main__':main()
