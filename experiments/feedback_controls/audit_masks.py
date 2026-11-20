"""Training/validation two-class passage checks; does not change masking rules."""
from common import *

def main():
    source={r['case_id']:r for r in load_rows()}
    revised={r['case_id']:r['texts']['REVISED'] for r in records(HERE/'inputs/quality_v1/variants.jsonl')}
    checks=[
      ('NY-4509516','train',0,'Supreme Court properly shifted the burden','quoted earlier rule','Ordered that the order is affirmed','Restore the cited burden rule. Current merits language such as triable issues still conveys the court reasoning.'),
      ('NY-5950295','train',0,'A defendant who moves for summary judgment','quoted general rule','and we affirm','The previous mask joined the quoted rule to we affirm; the revision separates these spans.'),
      ('NY-4427636','train',1,'In an action to recover damages','procedural history','Ordered that the order is reversed','The revision restores history lost at the LLC. boundary. Notice evidence and the cited rule remain.'),
      ('NY-5980564','train',1,'Zanki v Cahill','previous-decision citation','Accordingly, the Supreme Court should have granted','The long conclusion contained citations, not 100+ words of unique factual reasoning. Preserve its authorities while removing the current conclusion.'),
      ('NY-8511862','validation',0,'the defendant failed to establish, prima facie','reasoning','Ordered that the order is affirmed','Facts, the historical denial and failure-of-proof reasoning survive. Full original and revised variants inspected.'),
      ('NY-6459053','validation',0,'The Supreme Court denied the motion.','prior ruling','Ordered that the order is affirmed','Prior ruling and notice reasoning survive; the complete Winegrad citation is restored. Full original and revised variants inspected.'),
      ('NY-5304378','validation',1,'the plaintiff demonstrated that he had a potentially meritorious opposition','reasoning','Ordered that the order entered March 8, 2018, is reversed','Residual cue: generic the court should have granted remains. Law-office-failure reasoning and historical orders survive. This post-freeze check did not trigger rule changes.'),
      ('NY-5957906','validation',1,'triable issues of fact as to whether the ice','reasoning','Ordered that the order is reversed','The repeated explicit result is removed; one removed sentence also carries failure-of-proof reasoning. Related reasoning remains elsewhere; masking is not semantically lossless.')]
    audit=[]
    for cid,period,label,keep,kind,drop,note in checks:
        r=source[cid];assert r['period']==period and r['label']==label
        full=r['texts']['FULL'];old=r['texts']['MASKED'];new=revised[cid]
        assert keep in full and keep in new and drop in full and drop not in new
        audit.append({'case_id':cid,'period':period,'label':label,'preserved_quote':keep,'preserved_kind':kind,
            'preserved_in_original_mask':keep in old,'preserved_in_revision':True,'current_disposition_removed':drop,
            'source_full_start':full.index(keep),'source_full_end':full.index(keep)+len(keep),
            'FULL_sha256':text_hash(full),'MASKED_sha256':text_hash(old),'REVISED_sha256':text_hash(new),
            'technical_review_note':note,'review_status':'assistant_technical_audit_not_human_adjudication'})
    write(HERE/'results/two_class_mask_audit.json',{'design':'Four training flags motivated the frozen rules; four validation cases (two per class) checked after freeze without retuning. This is not a blinded validation audit.','cases':audit,
        'unresolved_findings':['NY-5304378 retains generic court-should-have wording.','Previously audited NY-9301972 retains unanimously affirmed in original and revised text.','Current-result and reasoning clauses can be inseparable under rule-based deletion.']})
    print('Verified two examples per class in both training and validation; residual problems recorded.')

if __name__=='__main__':main()
