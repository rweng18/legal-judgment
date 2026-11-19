"""Build and execute a portable notebook from saved A-C lexical results."""
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
    path = run / 'A_C_logistic_results.ipynb'
    if path.exists():
        raise FileExistsError(path)
    md, code = nbformat.v4.new_markdown_cell, nbformat.v4.new_code_cell
    notebook = nbformat.v4.new_notebook(cells=[
        md('# Combined A–C · Majority and TF-IDF logistic regression\n\n'
           '279 training cases (2010–2020), 42 shared development evaluation cases (2021–2022). '
           'A retains team-reviewed status; B/C use explicit provisional assumptions. '
           'Reserved test cases are not evaluated. This notebook reads and verifies the saved run without refitting models.'),
        code("from pathlib import Path\nimport json, hashlib\nimport numpy as np\nimport pandas as pd\n"
             "from IPython.display import display, Image\n"
             "RUN = Path('.')\nread = lambda n: json.loads((RUN / n).read_text())\n"
             "run = read('run.json')\nresults = pd.read_csv(RUN/'results.csv')\n"
             "display(run['assumptions'])\ndisplay(pd.read_csv(RUN/'batch_class_counts.csv'))\n"
             "display(pd.read_csv(RUN/'class_counts.csv').fillna(''))"),
        md('## MASKED training selection\n\n'
           'Word unigrams/bigrams, min_df=2, max_features=30000, L2-normalized TF-IDF; L2 logistic regression with balanced training-class weights. '
           'Each fold fits a fresh pipeline. Three family-grouped folds select C by mean balanced accuracy, then macro F1, then smaller C. '
           'The selected C is fixed for separate FULL and MASKED fits.'),
        code("selection = read('selection.json')['TFIDF_LR']\n"
             "display(pd.DataFrame([{k:t[k] for k in ['C','balanced_accuracy','macro_f1']} for t in selection['grid']]))\n"
             "print('Selected C:',selection['selected_C'])\ndisplay(run['models']['TFIDF_LR'])"),
        md('## Development results\n\n'
           'Accuracy is the overall correct fraction. Balanced accuracy is mean recall across labels 0 and 1. '
           'Macro F1 is mean F1 across both labels. Matrices show raw counts and row-normalized percentages; true rows, predicted columns, order 0, 1.'),
        code("display(results)\ndisplay(Image(filename=str(RUN/'confusion_matrices.png')))\n"
             "for condition in read('reporting_summary.json')['conditions']:\n"
             "    print(condition['model'],condition['variant'])\n"
             "    display(pd.DataFrame(condition['row_normalized'],index=pd.Index([0,1],name='True'),columns=pd.Index([0,1],name='Predicted')))"),
        md('## Independent verification\n\n'
           'Recompute metrics from per-case predictions, check shared evaluation IDs, family separation, majority label, fixed C, and report checksums.'),
        code("from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, confusion_matrix\n"
             "pred = pd.read_csv(RUN/'predictions.csv')\nsplits = pd.read_csv(RUN/'splits.csv')\n"
             "expected = splits[splits.period=='validation'].set_index('case_id')['label'].to_dict()\n"
             "training = splits[splits.period=='train']\n"
             "assert len(expected)==42 and len(training)==279 and len(pred)==168\n"
             "assert set(training.family_id).isdisjoint(splits[splits.period=='validation'].family_id)\n"
             "assert training.groupby('family_id').held_out_cv_fold.nunique().max()==1\n"
             "majority = training.label.value_counts().idxmax()\n"
             "assert (pred[pred.model=='Majority'].prediction==majority).all()\n"
             "assert set(pred[pred.model=='TFIDF_LR'].C)=={selection['selected_C']}\n"
             "for _, result in results.iterrows():\n"
             "    p=pred[(pred.model==result.model)&(pred.variant==result.variant)]\n"
             "    assert len(p)==len(expected) and p.set_index('case_id')['label'].to_dict()==expected\n"
             "    cm=confusion_matrix(p.label,p.prediction,labels=[0,1])\n"
             "    values={'accuracy':accuracy_score(p.label,p.prediction),'balanced_accuracy':balanced_accuracy_score(p.label,p.prediction),"
             "'macro_f1':f1_score(p.label,p.prediction,labels=[0,1],average='macro'),"
             "'recall_0':cm[0,0]/cm[0].sum(),'recall_1':cm[1,1]/cm[1].sum()}\n"
             "    for key,value in values.items():\n"
             "        assert np.isclose(result[key],value,rtol=0,atol=1e-12)\n"
             "    stored=next(x for x in read('reporting_summary.json')['conditions'] if x['model']==result.model and x['variant']==result.variant)\n"
             "    assert stored['counts']==cm.tolist()\n"
             "    assert np.allclose(stored['row_normalized'],cm/cm.sum(axis=1,keepdims=True))\n"
             "for name,checksum in read('reporting_summary.json')['source_sha256'].items():\n"
             "    assert hashlib.sha256((RUN/name).read_bytes()).hexdigest()==checksum\n"
             "print('Verified all four conditions on identical evaluation cases; original failures remain in the saved predictions.')"),
        md('## Interpretation and reproducibility\n\n'
           'The FULL/MASKED contrast is a development comparison of separately fitted pipelines at fixed C. '
           'Retained outcome-related reasoning, different upstream masks by batch, prior A/B development exposure, '
           'small evaluation size and provisional B/C labels limit interpretation. '
           'See REPORT.md for the reproduction command and REPORTING.md for all counts. '
           'Select the installed environment’s Python kernel to rerun this notebook.'),
        code("display(run['software'])\ndisplay(read('verification.json'))"),
    ], metadata={'kernelspec': {'name': 'python3', 'language': 'python', 'display_name': 'Python 3'}})
    with tempfile.TemporaryDirectory() as tmp:
        kernels = Path(tmp) / 'kernels'
        kernel = kernels / 'python3'
        kernel.mkdir(parents=True)
        (kernel / 'kernel.json').write_text(json.dumps({
            'argv': [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
            'display_name': 'Python 3', 'language': 'python'}))
        os.environ['IPYTHONDIR'] = str(Path(tmp) / 'ipython')
        os.environ['JUPYTER_RUNTIME_DIR'] = tmp
        manager = KernelManager(kernel_name='python3', kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(kernels)]))
        NotebookClient(notebook, km=manager, timeout=120, resources={'metadata': {'path': str(run)}}).execute()
    nbformat.validate(notebook)
    nbformat.write(notebook, path)
    print(path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    build(parser.parse_args().run.resolve())
