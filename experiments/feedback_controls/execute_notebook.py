"""Execute every notebook cell in this environment; no fake execution counters."""
import os,sys
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager
from pathlib import Path
HERE=Path(__file__).resolve().parent
cache=HERE/'.cache';kernel=cache/'kernels/team11-feedback';kernel.mkdir(parents=True,exist_ok=True)
import json
(kernel/'kernel.json').write_text(json.dumps(dict(argv=[sys.executable,'-X','utf8','-m','ipykernel_launcher','-f','{connection_file}'],display_name='Python (Team 11 feedback)',language='python')),encoding='utf8')
for variable,name in [('IPYTHONDIR','ipython'),('JUPYTER_RUNTIME_DIR','runtime'),('MPLCONFIGDIR','matplotlib'),('TEMP','tmp'),('TMP','tmp')]:
    path=cache/name;path.mkdir(exist_ok=True);os.environ[variable]=str(path)
km=KernelManager(kernel_name='team11-feedback',kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(cache/'kernels')]))
path=HERE/'Team_11_Feedback_Experiments.ipynb';nb=nbformat.read(path,as_version=4)
print('Starting notebook kernel',flush=True)
NotebookClient(nb,km=km,timeout=120,startup_timeout=45,
    on_cell_start=lambda cell,cell_index:print('Executing cell',cell_index,flush=True),
    resources={'metadata':{'path':str(HERE)}}).execute()
assert all(c.get('execution_count') is not None for c in nb.cells if c.cell_type=='code')
assert not any(o.get('output_type')=='error' for c in nb.cells for o in c.get('outputs',[]))
nbformat.write(nb,path);print(f'Executed {sum(c.cell_type=="code" for c in nb.cells)} code cells successfully.')
