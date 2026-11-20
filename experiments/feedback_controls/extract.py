"""Offline, resumable extraction with the pinned frozen checkpoint and all tokens."""
import os
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
import argparse,time
from importlib.metadata import version
from common import *
import numpy as np

def main():
    import torch
    from transformers import AutoTokenizer,AutoModel
    from encoder import SETTINGS,content_chunks
    ap=argparse.ArgumentParser();ap.add_argument('--snapshot',required=True);args=ap.parse_args()
    snapshot=Path(args.snapshot)
    expected={'config.json':'716ea70c3c3e74bfe8496cc04cba7cd52f4ca45401e74042bb1058fe0390a1b6',
              'vocab.txt':'3aaa02f2e3a397eee0f813caa567c87cddab1045a4a6b8ac6261f0cc799efb8f',
              'pytorch_model.bin':'6b4f1da798ff101a66ad5cb11c6daa7f99cd41e7909277e01398576e8bd789bd'}
    for name,h in expected.items():assert digest((snapshot/name).read_bytes())==h,name
    torch.set_num_threads(SETTINGS['threads']);torch.manual_seed(20261023)
    tokenizer=AutoTokenizer.from_pretrained(str(snapshot),use_fast=False,local_files_only=True)
    assert type(tokenizer).__name__==SETTINGS['tokenizer'] and tokenizer.num_special_tokens_to_add(False)==2
    model=AutoModel.from_pretrained(str(snapshot),local_files_only=True)
    model.eval().requires_grad_(False)
    assert not model.training and not any(p.requires_grad for p in model.parameters())
    settings={'encoder':SETTINGS,'checkpoint_sha256':expected,
              'software':{k:version(k) for k in ['torch','transformers','tokenizers','numpy']},
              'code_sha256':digest(Path(__file__).read_bytes())}
    rows=load_rows();variants=records(HERE/'inputs/variants.jsonl');quality=records(HERE/'inputs/quality_v1/variants.jsonl')
    assert [r['case_id'] for r in rows]==[r['case_id'] for r in variants]==[r['case_id'] for r in quality]
    for r,q in zip(variants,quality):r['texts'].update(q['texts'])
    names=['FULL','MASKED',*[f'RANDOM_{s}' for s in SEEDS],'REVISED',*[f'REVISED_RANDOM_{s}' for s in SEEDS]]
    cache=HERE/'.cache/encoder';cache.mkdir(parents=True,exist_ok=True)
    out=HERE/'results/embeddings';out.mkdir(parents=True,exist_ok=True)
    prefix=json.dumps(settings,sort_keys=True).encode();start=time.perf_counter();counts=[]
    for name in names:
        vectors=[];firsts=[]
        for n,r in enumerate(variants,1):
            txt=r['texts'][name];identity=digest(prefix+b'\0'+txt.encode('utf8'));target=cache/(identity+'.npz')
            if target.exists():
                z=np.load(target);allv=z['all'];first=z['first'];nt=int(z['tokens']);nc=int(z['chunks'])
            else:
                chunks=content_chunks(tokenizer,txt);nt=sum(map(len,chunks));nc=len(chunks)
                total=np.zeros(768,dtype=np.float64);first=None
                with torch.inference_mode():
                    for i in range(0,len(chunks),SETTINGS['batch_size_chunks']):
                        batch=chunks[i:i+SETTINGS['batch_size_chunks']]
                        enc=[tokenizer.prepare_for_model(c,add_special_tokens=True,return_special_tokens_mask=True) for c in batch]
                        inputs=tokenizer.pad(enc,padding=True,return_tensors='pt')
                        special=inputs.pop('special_tokens_mask').numpy().astype(bool)
                        content=inputs['attention_mask'].numpy().astype(bool)&~special
                        assert inputs['input_ids'].shape[1]<=512 and content.sum(1).tolist()==list(map(len,batch))
                        h=model(**inputs).last_hidden_state.numpy()
                        total+=h[content].sum(0,dtype=np.float64)
                        if first is None:first=h[0][content[0]].mean(0,dtype=np.float64).astype(np.float32)
                allv=(total/nt).astype(np.float32)
                tmp=cache/(identity+'.tmp.npz');np.savez(tmp,all=allv,first=first,tokens=nt,chunks=nc);os.replace(tmp,target)
            assert allv.shape==first.shape==(768,) and np.isfinite(allv).all() and np.isfinite(first).all()
            vectors.append(allv);firsts.append(first)
            counts.append({'case_id':r['case_id'],'variant':name,'text_sha256':text_hash(txt),'tokens':nt,'chunks':nc})
            if n%40==0 or n==len(rows):print(f'{name}: {n}/{len(rows)}; total {time.perf_counter()-start:.1f}s',flush=True)
        np.save(out/f'{name}.npy',np.stack(vectors))
        if name in ['FULL','MASKED','REVISED']:np.save(out/f'{name}_FIRST.npy',np.stack(firsts))
    write(out/'index.json',{'settings':settings,'elapsed_seconds':time.perf_counter()-start,
        'case_ids':[r['case_id'] for r in rows],'texts':counts,
        'sha256':{p.name:digest(p.read_bytes()) for p in out.glob('*.npy')}})
    print('EXTRACTION COMPLETE',flush=True)

if __name__=='__main__':main()
