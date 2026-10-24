"""Execute the generated notebook with this interpreter, using only local cache dirs."""
import argparse,os,sys
from pathlib import Path
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager
from common import HERE,read,dump,output

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-name');a=p.parse_args();c=read(HERE/'config.json')
    if a.run_name:c['run_name']=a.run_name
    out=output(c);cache=HERE/'.cache';kernel=cache/'kernels/provisional-a'
    dump(kernel/'kernel.json',{'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'Python (provisional A)','language':'python'})
    for variable,name in [('IPYTHONDIR','ipython'),('JUPYTER_RUNTIME_DIR','jupyter_runtime'),('MPLCONFIGDIR','matplotlib'),('TEMP','tmp'),('TMP','tmp')]:
        folder=cache/name;folder.mkdir(parents=True,exist_ok=True);os.environ[variable]=str(folder)
    km=KernelManager(kernel_name='provisional-a',kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(cache/'kernels')]))
    path=out/'provisional_A_results.ipynb';nb=nbformat.read(path,as_version=4)
    NotebookClient(nb,km=km,timeout=120,resources={'metadata':{'path':str(out)}}).execute()
    assert all(cell.get('execution_count') is not None for cell in nb.cells if cell.cell_type=='code')
    assert not any(o.get('output_type')=='error' for cell in nb.cells for o in cell.get('outputs',[]))
    nbformat.write(nb,path);print(f'Executed {sum(c.cell_type=="code" for c in nb.cells)} code cells: {path}')
