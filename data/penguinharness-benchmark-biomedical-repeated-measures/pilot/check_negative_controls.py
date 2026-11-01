import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('--package', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
PACKAGE = args.package
results = []
for case in sorted(PACKAGE.glob('CASE-*')):
    data = next((case / 'statement/data').glob('*.data'))
    subprocess.run([sys.executable, str(case / 'rubric/evaluate.py'),
        '--data', str(data), '--output', str(case / 'rubric/reference_results')],
        capture_output=True, text=True, check=True)
    for mutation in ['missing_row', 'wrong_fold', 'wrong_prediction', 'wrong_metric']:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'results'
            shutil.copytree(case / 'rubric/reference_results', output)
            predictions = pd.read_csv(output / 'predictions.csv')
            if mutation == 'missing_row':
                predictions = predictions.iloc[1:]
            elif mutation == 'wrong_fold':
                predictions.loc[0, 'fold'] = -1
            elif mutation == 'wrong_prediction':
                column = 'probability' if 'probability' in predictions else 'prediction'
                predictions.loc[0, column] += 0.1
            else:
                metrics = pd.read_csv(output / 'metrics.csv')
                column = 'patient_brier' if 'patient_brier' in metrics else 'patient_mae'
                metrics.loc[0, column] += 0.1
                metrics.to_csv(output / 'metrics.csv', index=False)
            predictions.to_csv(output / 'predictions.csv', index=False)
            run = subprocess.run([sys.executable, str(case/'rubric/evaluate.py'), '--data', str(data), '--output', str(output)], capture_output=True, text=True)
            assert run.returncode == 1 and 'AssertionError' in run.stderr, (case.name, mutation, run.stderr)
            results.append(dict(case=case.name, mutation=mutation, rejected=True))
args.output.write_text(json.dumps(results,indent=2)+'\n')
print('All eight deliberately incorrect submissions were rejected.')
