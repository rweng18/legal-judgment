import re

def n_words(s): return len(s.split())

ABBR=['v','vs','inc','corp','co','ltd','llc','j','jj','p.j','a.j','j.p','st','no','nos','dr','mr','mrs','ms','jr','sr','dept','assn','assoc','univ','auth','ctr','hous','ins','mt','ave','approx','id','cf','e.g','i.e','rd','dev','mgt','auth','dist','n.y','l.p']
ABBR_RE=re.compile(r'(?<!\w)('+ '|'.join(re.escape(x) for x in sorted(ABBR,key=len,reverse=True))+r')\.(?=\W|$)',re.I)
SENT_END=re.compile(r'(?<=[.!?])\s+(?=[“”"\'\u2018\u2019\[]*[A-Z])')
CUES=re.compile(r'\b(?:it is hereby )?ordered that\b|\bwe\s+(?:(?:therefore|accordingly|now|unanimously)\s+)?(?:affirm|reverse|vacate)\b|\b(?:order|judgment)\s+(?:must|should)\s+be\s+(?:affirmed|reversed|vacated)\b',re.I)

def split_legal(text):
 # Protect periods inside abbreviations, then recover the original spelling.
 protected=ABBR_RE.sub(lambda m:m.group().replace('.','\ue000'),text)
 # Protect decimals and legal citation markers like AD3d (no period there).
 protected=re.sub(r'(?<=\d)\.(?=\d)', '\ue000', protected)
 pieces=[];start=0
 for match in SENT_END.finditer(protected):
  end=match.start();piece=protected[start:end].replace('\ue000','.').strip()
  if piece:pieces.append(piece)
  start=match.end()
 tail=protected[start:].replace('\ue000','.').strip()
 if tail:pieces.append(tail)
 return pieces

def remove_parentheticals(s):
 for _ in range(10):
  nexts=re.sub(r'\([^()]*\)',' ',s)
  if nexts==s:break
  s=nexts
 return s

def outcome_rule(sent):
 s=remove_parentheticals(sent)
 if re.search(r'\b(?:it is hereby )?ordered that\b',s,re.I):return 'operative_order'
 if re.match(r'^(?:Orders?|Order and judgment|Judgment),',s,re.I) and re.search(r'\b(?:affirmed|reversed|vacated|modified)\b',s,re.I):return 'opening_disposition'
 if re.search(r'\bwe\s+(?:(?:therefore|accordingly|now|unanimously)\s+)?(?:affirm|reverse|vacate)\b',s,re.I):return 'we_current_disposition'
 if re.search(r'\b(?:order|judgment)\s+(?:must|should)\s+be\s+(?:affirmed|reversed|vacated)\b',s,re.I):return 'required_disposition'
 if re.search(r'\b(?:Supreme Court|motion court|court below)\s+(?:properly|correctly|erred|should have)\b',s,re.I):return 'express_review_of_appealed_ruling'
 if re.search(r'\bwe (?:agree|disagree) with (?:the )?Supreme Court',s,re.I):return 'express_agreement_with_appealed_ruling'
 if re.search(r'\b(?:summary judgment|motion|complaint|cross motion)\b.{0,100}\b(?:was|were|is|are|should have been)\s+(?:properly\s+)?(?:granted|denied|dismissed)\b',s,re.I) and re.match(r'^(?:Accordingly|Thus|Therefore|Summary judgment (?:was|should))',s,re.I):return 'repeated_current_result'
 return None

def mask(s):
 pieces=split_legal(s);kept=[];removed=[]
 for idx,part in enumerate(pieces):
  rule=outcome_rule(part)
  if rule:removed.append({'sentence_index':idx,'reason':rule,'sentence':part,'words':n_words(part)})
  else:kept.append(part)
 return ' '.join(kept),removed,pieces

def flags(full,masked,removed,pieces):
 loss=100*(n_words(full)-n_words(masked))/n_words(full)
 found=list(CUES.finditer(masked));x=[]
 if not masked.strip():x.append('EMPTY_MASKED')
 if n_words(masked)<60:x.append('SHORT_MASKED_LT60')
 if loss>=35:x.append('MASK_LOSS_GE35PCT')
 if any(d['words']>80 for d in removed):x.append('REMOVED_SENTENCE_GT80WORDS')
 if any(n_words(p)>180 for p in pieces):x.append('LONG_SEGMENT_GT180WORDS')
 if found:x.append('POSSIBLE_RESIDUAL_CUE')
 return x,loss,[m.group(0) for m in found[:5]]

