import argparse
import json
from pathlib import Path
import shutil
import signal
import subprocess
import time


parser = argparse.ArgumentParser()
parser.add_argument('--package', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--cli', type=Path, required=True)
parser.add_argument('--python', required=True)
parser.add_argument('--model', required=True)
parser.add_argument('--seconds', type=int, default=1800)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
records = []
for case in sorted(args.package.glob('CASE-*')):
    folder = args.output / case.name
    workspace = folder / 'workspace'
    shutil.copytree(case / 'statement', workspace)
    command = [str(args.cli), 'run', '--workspace', str(workspace),
        '--provider', 'custom', '--model-id', args.model,
        '--title', case.name, '--json', '-m', (workspace / 'README.md').read_text()]
    started = time.monotonic()
    with (folder / 'run.json').open('w') as stdout, (folder / 'stderr.log').open('w') as stderr:
        process = subprocess.Popen(command, cwd=workspace, stdout=stdout, stderr=stderr)
        try:
            process.wait(timeout=args.seconds)
            timed_out = False
        except subprocess.TimeoutExpired:
            process.send_signal(signal.SIGINT)
            process.wait(timeout=60)
            timed_out = True
    elapsed = time.monotonic() - started
    result = json.loads((folder / 'run.json').read_text())
    session_id = result['sessionId']
    with (folder / 'trace.json').open('w') as trace:
        subprocess.run([str(args.cli), 'session', 'log', session_id, '--json'],
            stdout=trace, check=True)
    data, = (workspace / 'data').glob('*.data')
    checked = subprocess.run([args.python, str(case / 'rubric/evaluate.py'),
        '--data', str(data), '--output', str(workspace / 'results')],
        cwd=workspace, capture_output=True, text=True)
    (folder / 'evaluation.log').write_text(checked.stdout + checked.stderr)
    record = dict(case=case.name, model=args.model, wall_seconds=elapsed,
        timeout=timed_out, cli_returncode=process.returncode,
        session_status=result['status'], evaluator_returncode=checked.returncode,
        evaluation=checked.stdout.strip())
    records.append(record)
    (args.output / 'summary.json').write_text(json.dumps(records, indent=2) + '\n')
    print(json.dumps(record), flush=True)
