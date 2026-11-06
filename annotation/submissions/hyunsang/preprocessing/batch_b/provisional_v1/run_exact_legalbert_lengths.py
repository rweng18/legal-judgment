"""Run from checked-out legal-judgment/experiments/provisional_b directory.
Usage: python /path/to/run_exact_legalbert_lengths.py /path/to/our_package
Requires numpy==2.3.4 transformers==4.57.1 and network/cache for pinned LEGAL-BERT.
"""
import sys, pathlib
package=pathlib.Path(sys.argv[1]).resolve()
repo=pathlib.Path.cwd()
assert (repo/'lengths.py').is_file() and (repo/'encoder_settings.json').is_file(), 'Run from legal-judgment/experiments/provisional_b'
from encoder import SETTINGS,load_tokenizer
assert SETTINGS['revision']=='15b570cbf88259610b082a167dacc190124f60f6'
import subprocess
subprocess.run([sys.executable,'lengths.py',str(package/'B_development_v2_PROVISIONAL.jsonl'),str(package/'B_v2_exact_token_lengths')],check=True)
print('Exact lengths generated:',package/'B_v2_exact_token_lengths')
