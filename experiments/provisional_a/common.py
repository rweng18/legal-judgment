import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
def read(path):return json.loads(Path(path).read_text(encoding='utf8'))
def records(path):return [json.loads(s) for s in Path(path).read_text(encoding='utf8').splitlines() if s.strip()]
def dump(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
def jsonl(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(''.join(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n' for r in rows),encoding='utf8')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def textsha(s):return hashlib.sha256(s.encode('utf8')).hexdigest()
def output(config):return HERE/'outputs'/config['run_name']
def split_for(year,c):return 'train' if year<=c['train_end'] else 'validation' if year<=c['validation_end'] else 'test'
