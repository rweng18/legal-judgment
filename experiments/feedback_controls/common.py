"""Fixed development protocol for the November feedback; never loads test text."""
import csv
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = '0837ed2bf4c1d3abc7fd3b0ea652f5a5461894db'
ABC = ROOT / 'experiments/provisional_abc'
SHARED = ROOT / 'experiments/provisional_b'
REFERENCE = ABC / 'runs/abc_complete_provisional_v1'
SEEDS = [11, 23, 37, 51, 71]
SELECTED_C = {'TFIDF_LR': 10., 'TFIDF_SVM': 10., 'LEGAL_BERT_LR': .1}
sys.path.insert(0, str(SHARED))
sys.path.insert(0, str(ABC))

def digest(b): return hashlib.sha256(b).hexdigest()
def text_hash(s): return digest(s.encode('utf8'))
def read(p): return json.loads(Path(p).read_text(encoding='utf8'))
def records(p): return [json.loads(s) for s in Path(p).read_text(encoding='utf8').splitlines() if s.strip()]
def write(p, data):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n')
def jsonl(p, rows):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(''.join(json.dumps(x,ensure_ascii=False,allow_nan=False)+'\n' for x in rows),encoding='utf8',newline='\n')
def csvout(p, rows):
    rows=list(rows);p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def blob(path): return subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

OLD=module('old_mask_controls','experiments/provisional_a/preprocessing.py')
NEW=module('new_mask_controls','annotation/submissions/hyunsang/preprocessing/batch_c/provisional_v1/b_mask_v2.py')
SENTENCES=module('random_sentence_controls','annotation/submissions/becca/MVP/preprocessing/masked_text_v2.py')

def random_remove(text,budget,seed,cid):
    """A MVP control: identical SHA seed and sentence rule, exact whitespace-word loss."""
    import random
    tokens=list(re.finditer(r'\S+',text)); spans=list(SENTENCES.sentence_spans(text))
    groups=[[i for i,t in enumerate(tokens) if a<=t.start()<b] for a,b in spans]
    assert sorted(i for g in groups for i in g)==list(range(len(tokens)))
    assert 0<=budget<len(tokens)
    rng=random.Random(int(text_hash(f'{seed}:{cid}')[:16],16))
    order=list(range(len(groups)));rng.shuffle(order);drop=set();partial=False
    for j in order:
        left=budget-len(drop)
        if left<=0:break
        ids=groups[j]
        if len(ids)<=left:drop.update(ids)
        else:
            start=rng.randrange(len(ids)-left+1);drop.update(ids[start:start+left]);partial=True
    assert len(drop)==budget
    # Preserve the exact original when the loss budget is zero.
    kept=text if not drop else ' '.join(t.group() for i,t in enumerate(tokens) if i not in drop)
    return kept,{'removed_word_indices':sorted(drop),'partial_final_sentence':partial,
                 'removed_words':budget,'removed_spans':[{'start':tokens[i].start(),'end':tokens[i].end(),'text':tokens[i].group()} for i in sorted(drop)]}

def policy_spans(text,boundaries):
    if boundaries=='old':return OLD.sentence_spans(text)
    spans=[];pos=0
    for part in NEW.split_legal(text):
        start=text.index(part,pos);end=start+len(part);spans.append((start,end));pos=end
    return spans

def component_mask(text,boundaries,rules):
    """2x2 intervention: only old/new boundaries and old/new outcome matcher vary."""
    spans=policy_spans(text,boundaries);kept=[];removed=[]
    match=OLD.outcome_rule if rules=='old' else NEW.outcome_rule
    for a,b in spans:
        reason=match(text[a:b])
        if reason:removed.append({'start':a,'end':b,'text':text[a:b],'reason':reason})
        else:kept.append(text[a:b])
    return ' '.join(kept),removed

def load_rows():
    from prepare import load_release
    return load_release(HERE/'inputs/release/release.json')[1]

