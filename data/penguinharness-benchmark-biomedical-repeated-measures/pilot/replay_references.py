import argparse
from importlib.metadata import version
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


def replay(package):
    results = []
    for case in sorted(package.glob('CASE-*')):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / 'workspace'
            shutil.copytree(case / 'statement', workspace)
            data = next((workspace / 'data').glob('*.data'))
            output = workspace / 'results'
            started = time.monotonic()
            subprocess.run([sys.executable, str(case / 'rubric/reference.py'),
                '--data', str(data), '--output', str(output)], cwd=workspace, check=True)
            checked = subprocess.run([sys.executable, str(case / 'rubric/evaluate.py'),
                '--data', str(data), '--output', str(output)], cwd=workspace,
                capture_output=True, text=True, check=True)
            results.append(dict(case=case.name, reference_passed=True,
                elapsed_seconds=time.monotonic() - started,
                verifier_stdout=checked.stdout.strip()))
    return dict(python=sys.version.split()[0],
        dependencies={name: version(name) for name in ['numpy', 'pandas', 'scipy', 'scikit-learn']},
        method='Fresh CPU fits in temporary statement workspaces, graded against committed reference outputs.',
        cases=results)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(replay(args.package.resolve()), indent=2) + '\n')
