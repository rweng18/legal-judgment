"""Create and execute a portable notebook for one completed experiment run."""
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

from encoder import HERE


def build(run, filename="Batch_B_results.ipynb"):
    if Path(filename).name != filename:
        raise ValueError("Notebook filename must be a name inside the run directory.")
    path = run / filename
    if path.exists():
        raise FileExistsError(path)
    markdown = nbformat.v4.new_markdown_cell
    code = nbformat.v4.new_code_cell
    cells = [
        markdown("# Batch B · Frozen LEGAL-BERT and lexical comparison\n\n"
                 "The run uses the user's assumption that supplied labels have been reviewed. "
                 "Family assignments retain their provisional status. All scores use the same "
                 "2021–2022 development cases. Parameters are selected on MASKED training folds."),
        code("from pathlib import Path\nimport json, hashlib\nimport numpy as np\nimport pandas as pd\n"
             "from IPython.display import display, Image\n"
             "RUN = Path('.')\nread = lambda name: json.loads((RUN / name).read_text())\n"
             "run = read('run.json')\nsplits = pd.read_csv(RUN / 'splits.csv')\n"
             "reporting = read('reporting_summary.json')\n"
             "display(pd.read_csv(RUN / 'class_counts.csv').fillna(''))\n"
             "display(run['release'])"),
        markdown("## MASKED training selection\n\n"
                 "Three family-grouped folds within 2010–2020. Mean balanced accuracy determines C, "
                 "then macro F1 and smaller C break ties. Each model uses its selected C for both variants."),
        code("selection = read('selection.json')\n"
             "display(pd.DataFrame([dict(model=name, C=t['C'], "
             "balanced_accuracy=t['balanced_accuracy'], macro_f1=t['macro_f1'], "
             "selected=t['C']==result['selected_C']) "
             "for name,result in selection.items() for t in result['grid']]))"),
        markdown("## Shared development results\n\n"
                 "Accuracy is the overall correct fraction, alongside the training-majority baseline. "
                 "Balanced accuracy is mean recall across labels 0 and 1 and the primary selection metric. "
                 "Macro F1 averages F1 across both labels. Recall 0 and recall 1 are reported separately. "
                 "Confusion matrices use true rows and predicted columns, both ordered 0, 1. "
                 "The figure shows raw counts and row percentages; tables show exact row-normalized fractions."),
        code("results = pd.read_csv(RUN / 'results.csv')\ndisplay(results)\n"
             "display(Image(filename=str(RUN / 'confusion_matrices.png')))\n"
             "for condition in reporting['conditions']:\n"
             "    print(condition['model'], condition['variant'])\n"
             "    for key in ['counts', 'row_normalized']:\n"
             "        print(key)\n"
             "        display(pd.DataFrame(condition[key], index=pd.Index([0,1],name='True'), "
             "columns=pd.Index([0,1],name='Predicted')))\n"
             "paired = results.pivot(index='model', columns='variant', values='balanced_accuracy')\n"
             "paired['FULL minus MASKED'] = paired['FULL'] - paired['MASKED']\ndisplay(paired)"),
        markdown("## Encoder and reproducibility\n\n"
                 "The encoder stays frozen in evaluation/inference mode. Every chunk contains up to "
                 "510 content tokens plus CLS/SEP. Pooling excludes specials and padding, and weights "
                 "each chunk by content length."),
        code("display(run['encoder_settings'])\ndisplay(run['software'])\n"
             "display(read('verification.json'))\ndisplay(read('length_summary.json'))"),
        markdown("## Verify saved predictions and vectors"),
        code("from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, confusion_matrix\n"
             "pred = pd.read_csv(RUN / 'predictions.csv')\n"
             "expected = splits.loc[splits.period=='validation'].set_index('case_id')['label'].to_dict()\n"
             "for _, result in results.iterrows():\n"
             "    p = pred[(pred.model==result.model) & (pred.variant==result.variant)]\n"
             "    assert len(p)==len(expected) and p.set_index('case_id')['label'].to_dict()==expected\n"
             "    for key, value in [('accuracy',accuracy_score(p.label,p.prediction)),"
             "('balanced_accuracy',balanced_accuracy_score(p.label,p.prediction)),"
             "('macro_f1',f1_score(p.label,p.prediction,labels=[0,1],average='macro'))]:\n"
             "        assert np.isclose(result[key],value,rtol=0,atol=1e-12)\n"
             "    cm = next(x['counts'] for x in read('confusion_matrices.json')['conditions'] "
             "if x['model']==result.model and x['variant']==result.variant)\n"
             "    assert confusion_matrix(p.label,p.prediction,labels=[0,1]).tolist()==cm\n"
             "    detail = next(x for x in reporting['conditions'] "
             "if x['model']==result.model and x['variant']==result.variant)\n"
             "    cm = np.asarray(cm)\n"
             "    normalized = cm / cm.sum(axis=1,keepdims=True)\n"
             "    assert np.allclose(detail['row_normalized'], normalized,rtol=0,atol=1e-12)\n"
             "    assert np.allclose([result.recall_0,result.recall_1],np.diag(normalized))\n"
             "for name, checksum in reporting['source_sha256'].items():\n"
             "    assert hashlib.sha256((RUN/name).read_bytes()).hexdigest()==checksum\n"
             "for count in reporting['class_counts']:\n"
             "    if count['scope'].startswith('cv_'):\n"
             "        subset = splits[splits.period=='train']\n"
             "        held_out = subset.held_out_cv_fold==int(count['fold'])\n"
             "        subset = subset[held_out if count['scope']=='cv_held_out' else ~held_out]\n"
             "    else:\n"
             "        subset = splits[splits.period==count['scope']]\n"
             "    assert len(subset)==count['n']\n"
             "    assert [(subset.label==label).sum() for label in [0,1]]==[count['label_0'],count['label_1']]\n"
             "index = read('embedding_index.json')\n"
             "assert [r['case_id'] for r in index['rows']]==splits.case_id.tolist()\n"
             "for name, checksum in index['files_sha256'].items():\n"
             "    assert hashlib.sha256((RUN/name).read_bytes()).hexdigest()==checksum\n"
             "    vectors = np.load(RUN/name,allow_pickle=False)\n"
             "    assert vectors.shape==(len(splits),768) and np.isfinite(vectors).all()\n"
             "print(f'Verified {len(results)} conditions on {len(expected)} shared evaluation cases and both embedding matrices.')"),
    ]
    nb = nbformat.v4.new_notebook(cells=cells, metadata={"kernelspec": {
        "name": "legal-bc-run", "language": "python", "display_name": "Legal B+C run"}})
    cache = HERE / ".cache"
    cache.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=cache) as temp:
        kernels = Path(temp) / "kernels"
        kernel = kernels / "legal-bc-run"
        kernel.mkdir(parents=True)
        (kernel / "kernel.json").write_text(json.dumps({
            "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
            "display_name": "Legal B+C run", "language": "python",
        }))
        os.environ["IPYTHONDIR"] = str(Path(temp) / "ipython")
        os.environ["JUPYTER_RUNTIME_DIR"] = temp
        manager = KernelManager(kernel_name="legal-bc-run",
                                kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(kernels)]))
        NotebookClient(nb, km=manager, timeout=120, resources={"metadata": {"path": str(run)}}).execute()
    nbformat.validate(nb)
    nbformat.write(nb, path)
    print(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--filename", default="Batch_B_results.ipynb")
    args = parser.parse_args()
    build(args.run.resolve(), args.filename)
