"""Create and execute the portable A-C complete-comparison results notebook."""
import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager


def build(run):
    path = run / 'A_C_complete_results.ipynb'
    if path.exists():
        raise FileExistsError(path)
    md, code = nbformat.v4.new_markdown_cell, nbformat.v4.new_code_cell
    nb = nbformat.v4.new_notebook(cells=[
        md('# A–C · Complete development comparison\n\n'
           '279 training cases; the same 42 development cases across majority, TF-IDF LR, linear SVM and frozen LEGAL-BERT LR, '
           'each with FULL and MASKED text. A retains team-reviewed status; B/C retain explicit provisional assumptions. '
           'No final-test evaluation. This notebook reads and independently verifies saved results; it does not refit models.'),
        code("from pathlib import Path\nimport json, hashlib\nimport numpy as np\nimport pandas as pd\n"
             "from IPython.display import display, Image\nRUN=Path('.')\n"
             "read=lambda n:json.loads((RUN/n).read_text())\nrun=read('run.json')\n"
             "display(pd.read_csv(RUN/'batch_class_counts.csv'))\n"
             "display(pd.read_csv(RUN/'class_counts.csv').fillna(''))\ndisplay(run['assumptions'])"),
        md('## MASKED training-fold selection\n\n'
           'The same three family-grouped folds are reused across all learned models. Select C by mean balanced accuracy, '
           'then macro F1, then smaller C. Selected settings are fixed across FULL/MASKED. '
           'Vocabulary/IDF, balanced class weights and the encoder classifier’s scaler are fitted within training pipelines only.'),
        code("selection=read('selection.json')\n"
             "display(pd.DataFrame([dict(model=m,C=t['C'],balanced_accuracy=t['balanced_accuracy'],macro_f1=t['macro_f1'],selected=t['C']==s['selected_C']) "
             "for m,s in selection.items() for t in s['grid']]))\n"
             "display(run['models'])"),
        md('## Shared development metrics\n\n'
           'Accuracy is overall correctness; balanced accuracy is mean recall across labels 0 and 1; macro F1 averages the two label F1 scores. '
           'Matrices use true rows and predicted columns in order 0 affirmed, 1 reversed/vacated. '
           'The figure shows raw counts and row percentages; exact normalized fractions are displayed below.'),
        code("results=pd.read_csv(RUN/'results.csv')\ndisplay(results)\n"
             "display(Image(filename=str(RUN/'confusion_matrices.png')))\n"
             "paired=results.pivot(index='model',columns='variant',values='balanced_accuracy')\n"
             "paired['FULL minus MASKED']=paired.FULL-paired.MASKED\ndisplay(paired)\n"
             "for c in read('reporting_summary.json')['conditions']:\n"
             "    print(c['model'],c['variant'])\n"
             "    display(pd.DataFrame(c['row_normalized'],index=pd.Index([0,1],name='True'),columns=pd.Index([0,1],name='Predicted')))"),
        md('## Frozen encoder and all-chunk coverage\n\n'
           'Pinned LEGAL-BERT; up to 510 content tokens per chunk plus CLS/SEP, no overlap or truncation. '
           'Mean pooling excludes specials/padding and weights chunks by content-token count. All chunks contribute; '
           'encoder weights stay frozen. Cache-only reload matches the extracted vectors. '
           'Saved matrices contain 321 opinion vectors per variant, ordered by embedding_index.json.'),
        code("display(run['encoder_settings'])\ndisplay(read('verification.json'))\n"
             "display(read('length_summary.json'))\ndisplay(run['software'])"),
        md('## Verify predictions, folds, metrics and embeddings'),
        code("from sklearn.metrics import accuracy_score,balanced_accuracy_score,f1_score,confusion_matrix\n"
             "pred=pd.read_csv(RUN/'predictions.csv')\nsplits=pd.read_csv(RUN/'splits.csv')\n"
             "train=splits[splits.period=='train']\ndev=splits[splits.period=='validation']\n"
             "expected=dev.set_index('case_id')['label'].to_dict()\n"
             "assert len(train)==279 and len(dev)==42 and len(results)==8 and len(pred)==336\n"
             "assert set(train.family_id).isdisjoint(dev.family_id)\n"
             "assert train.groupby('family_id').held_out_cv_fold.nunique().max()==1\n"
             "assert (pred[pred.model=='Majority'].prediction==train.label.value_counts().idxmax()).all()\n"
             "for _,r in results.iterrows():\n"
             "    p=pred[(pred.model==r.model)&(pred.variant==r.variant)]\n"
             "    assert len(p)==len(expected) and p.set_index('case_id')['label'].to_dict()==expected\n"
             "    if r.model!='Majority':\n"
             "        assert r.C==selection[r.model]['selected_C'] and (p.C==r.C).all()\n"
             "    cm=confusion_matrix(p.label,p.prediction,labels=[0,1])\n"
             "    metrics={'accuracy':accuracy_score(p.label,p.prediction),'balanced_accuracy':balanced_accuracy_score(p.label,p.prediction),"
             "'macro_f1':f1_score(p.label,p.prediction,labels=[0,1],average='macro'),'recall_0':cm[0,0]/cm[0].sum(),'recall_1':cm[1,1]/cm[1].sum()}\n"
             "    for k,v in metrics.items():\n"
             "        assert np.isclose(r[k],v,rtol=0,atol=1e-12)\n"
             "    saved=next(c for c in read('reporting_summary.json')['conditions'] if c['model']==r.model and c['variant']==r.variant)\n"
             "    assert saved['counts']==cm.tolist()\n"
             "    assert np.allclose(saved['row_normalized'],cm/cm.sum(axis=1,keepdims=True))\n"
             "for name,checksum in read('reporting_summary.json')['source_sha256'].items():\n"
             "    assert hashlib.sha256((RUN/name).read_bytes()).hexdigest()==checksum\n"
             "index=read('embedding_index.json')\n"
             "assert [r['case_id'] for r in index['rows']]==splits.case_id.tolist()\n"
             "for name,checksum in index['files_sha256'].items():\n"
             "    assert hashlib.sha256((RUN/name).read_bytes()).hexdigest()==checksum\n"
             "    vectors=np.load(RUN/name,allow_pickle=False)\n"
             "    assert vectors.shape==(321,768) and np.isfinite(vectors).all()\n"
             "print('Verified all 8 conditions, 336 predictions, identical evaluation IDs and both embedding matrices.')"),
        md('## Interpretation\n\n'
           'These are provisional development estimates. A/B validation cases have been inspected before; masks differ by batch; '
           'family-companion uncertainties remain. A FULL/MASKED difference between separately fitted pipelines is not a same-model phrase-deletion effect. '
           'All failed predictions are preserved. Reproduction instructions are in REPORT.md; select the recorded environment’s Python kernel to rerun this notebook.'),
    ], metadata={'kernelspec': {'name': 'python3', 'language': 'python', 'display_name': 'Python 3'}})
    with tempfile.TemporaryDirectory() as tmp:
        kernels=Path(tmp)/'kernels'
        kernel=kernels/'python3'
        kernel.mkdir(parents=True)
        (kernel/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],
                                                    'display_name':'Python 3','language':'python'}))
        os.environ['IPYTHONDIR']=str(Path(tmp)/'ipython')
        os.environ['JUPYTER_RUNTIME_DIR']=tmp
        manager=KernelManager(kernel_name='python3',kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(kernels)]))
        NotebookClient(nb,km=manager,timeout=120,resources={'metadata':{'path':str(run)}}).execute()
    nbformat.validate(nb)
    nbformat.write(nb,path)
    print(path)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path)
    build(parser.parse_args().run.resolve())
