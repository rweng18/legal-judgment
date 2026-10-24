"""Download only required files at the committed model revision; no API key needed."""
from huggingface_hub import snapshot_download
from common import HERE,read
if __name__=='__main__':
    lock=read(HERE/'model_lock.json')
    print(snapshot_download(lock['model'],revision=lock['revision'],cache_dir=str(HERE/'.cache/huggingface'),
        allow_patterns=['config.json','pytorch_model.bin','model.safetensors','vocab.txt','tokenizer_config.json','special_tokens_map.json','tokenizer.json']))
