"""Label-independent preprocessing of opinion text. No annotation spans are inputs."""
import hashlib
import html
import random
import re

VERSION = 'mask_v1_training_rules'
ABBREVIATIONS = {'v','vs','inc','corp','co','ltd','llc','j','jj','p.j','a.j','j.p','st','no','nos','dr','mr','mrs','ms','jr','sr','dept','assn','assoc','univ','auth','ctr','hous','ins','mt','ave','approx','id','cf','e.g','i.e'}

def words(text):
    return list(re.finditer(r'\S+', text))

def sentence_spans(text):
    """Keep parenthetical precedents together and protect common legal abbreviations."""
    out=[];start=0;depth=0
    for i,ch in enumerate(text):
        if ch in '([':depth+=1
        elif ch in ')]':depth=max(0,depth-1)
        if ch not in '.!?' or depth or (i+1<len(text) and not text[i+1].isspace()):continue
        prev=re.search(r'([A-Za-z.]+)$',text[start:i])
        token=prev.group(1).lower() if prev else ''
        if ch=='.' and (token in ABBREVIATIONS or re.fullmatch(r'[a-z](?:\.[a-z])*',token)):continue
        if i+1<len(text) and not re.match(r'\s+[\"\u201c\u2018\[*(]*[A-Z]',text[i+1:]):continue
        s=start
        while s<i+1 and text[s].isspace():s+=1
        if text[s:i+1].strip():out.append((s,i+1))
        start=i+1
    s=start
    while s<len(text) and text[s].isspace():s+=1
    if s<len(text):out.append((s,len(text)))
    return out

def clean_text(raw):
    text=html.unescape(re.sub(r'<[^>]+>',' ',raw))
    text=re.sub(r'\[\*\d+\]|(?<!\w)\*\d+\b',' ',text)
    text=re.sub(r'\s+',' ',text).strip()
    log=[]
    marker=re.search(r'\b(?:In an action\b|Appeals? from\b|Order(?:s| and judgment)?, (?:Supreme|same) court\b|Judgment, Supreme Court\b|It is hereby ORDERED\b|Ordered that\b)',text,re.I)
    if marker and marker.start()>0:
        prefix=text[:marker.start()]
        if re.search(r'Slip Op|Appellate Division|SUPREME COURT OF THE STATE|for (?:appellant|respondent)|, J\.',prefix,re.I):
            log.append({'kind':'header','text':prefix});text=text[marker.start():]
    # Only explicit separate-opinion introductions; majority references to a dissent stay.
    dissent=re.search(r'\b(?:All concur except .{0,180}?dissent.{0,80}?following memorandum:|[A-Z][a-z]+, J\.?\s*\((?:dissenting|concurring in part and dissenting in part)\))',text)
    if dissent:log.append({'kind':'separate_opinion','text':text[dissent.start():]});text=text[:dissent.start()]
    text=re.sub(r'\[Prior Case History:.*?\]',' ',text)
    text=re.sub(r'\bEntered: [A-Z][a-z]+ \d{1,2}, \d{4}.*$',' ',text)
    # Judicial concurrence is metadata; retain any subsequent Ordered disposition.
    text=re.sub(r'\b(?:Concur|Present\s*)[\u2014\u2013-].*?\bJJ\.', ' ',text)
    text=re.sub(r'\b[A-Z][a-z]+(?:[ -][A-Z][a-z]+)?, (?:J\.P\.,|P\.J\.,|J\.,)?\s*(?:[A-Z][a-z]+(?:[ -][A-Z][a-z]+)?,?\s*(?:and\s*)?){1,8}JJ?\., concur\.', ' ',text)
    return re.sub(r'\s+',' ',text).strip(),log

def without_parentheses(text):
    while re.search(r'\([^()]*\)',text):text=re.sub(r'\([^()]*\)',' ',text)
    return text

def outcome_rule(sentence):
    s=without_parentheses(sentence)
    if re.search(r'\b(?:it is hereby )?ordered that\b',s,re.I):return 'operative_order'
    if re.match(r'^(?:Order(?:s| and judgment)?|Judgment),',s,re.I) and re.search(r'\b(?:affirmed|reversed|vacated|modified)\b',s,re.I):return 'opening_order_disposition'
    if re.search(r'\bwe\s+(?:(?:therefore|accordingly|now|unanimously)\s+)?(?:affirm|reverse|vacate)\b',s,re.I):return 'we_current_disposition'
    if re.search(r'\b(?:order|judgment)\s+(?:must|should)\s+be\s+(?:affirmed|reversed|vacated)\b',s,re.I):return 'required_disposition'
    if re.search(r'\b(?:Supreme Court|motion court|court below)\s+(?:properly|correctly|erred|should have)\b',s,re.I):return 'express_review_of_appealed_ruling'
    if re.search(r'\bwe (?:agree|disagree) with (?:the )?Supreme Court',s,re.I):return 'express_agreement_with_appealed_ruling'
    if re.search(r'\b(?:summary judgment|motion|complaint|cross motion)\b.{0,100}\b(?:was|were|is|are|should have been)\s+(?:properly\s+)?(?:granted|denied|dismissed)\b',s,re.I) and re.match(r'^(?:Accordingly|Thus|Therefore|Summary judgment (?:was|should))',s,re.I):return 'repeated_current_result'
    return None

def mask_text(full):
    spans=sentence_spans(full);kept=[];removed=[]
    for i,(a,b) in enumerate(spans):
        s=full[a:b];rule=outcome_rule(s)
        if rule:removed.append({'sentence_index':i,'start':a,'end':b,'text':s,'words':len(words(s)),'rule':rule})
        else:kept.append(s)
    return ' '.join(kept),removed

def random_remove(full,budget,seed,case_id):
    """Uniform random sentence order; partial final sentence for exact word budget.

    All FULL sentences are eligible, including outcome sentences. No label is used.
    Keep original order of retained tokens. Five fixed seeds characterize variability.
    """
    spans=sentence_spans(full);tokens=words(full)
    groups=[[i for i,t in enumerate(tokens) if a<=t.start()<b] for a,b in spans]
    rng=random.Random(int(hashlib.sha256(f'{seed}:{case_id}'.encode()).hexdigest()[:16],16))
    order=list(range(len(groups)));rng.shuffle(order);drop=set();partial=False
    for k in order:
        left=budget-len(drop)
        if left<=0:break
        ids=groups[k]
        if len(ids)<=left:drop.update(ids)
        else:
            a=rng.randrange(len(ids)-left+1);drop.update(ids[a:a+left]);partial=True
    assert len(drop)==budget and budget<len(tokens)
    return ' '.join(t.group() for i,t in enumerate(tokens) if i not in drop),{'removed_word_indices':sorted(drop),'partial_final_sentence':partial,'removed_words':budget}
