# Native Qwen3-4B pilot

This pilot evaluates a small local model on the two biomedical analyses through a native Python execution tool.

The model was Qwen/Qwen3-4B in bfloat16 with Transformers 5.15.1 and PyTorch 2.6.0+cu124 on an NVIDIA H100. Thinking was disabled. Sampling used temperature 0.7, top-p 0.8 and top-k 20, with seeds 20261031, 20261032 and 20261033. Each attempt had a fresh workspace containing only the statement and public input files. Each model call was limited to 4,096 output tokens and the total context to 32,768 tokens. A task could use up to 20 model turns and 1,800 seconds. A Python subprocess could run for up to 120 seconds within that budget. Three independent processes ran one attempt per task, with the same model and task settings across attempts.

The harness executes fenced Python code in subprocesses on a shared host filesystem. Each task workspace contains the statement and public data. Evaluator files remain in the separate repository checkout. Library installation paths in exported error traces are abbreviated as `<site-packages>`; model messages, code, errors and outcomes are preserved.

## Outcomes

| Case | Attempt | Model turns | Seconds | Input tokens | Output tokens | Task score |
|---|---:|---:|---:|---:|---:|---:|
| 001 | 1 | 2 | 48.7 | 4914 | 1858 | 0 |
| 002 | 1 | 2 | 65.5 | 6272 | 2567 | 0 |
| 001 | 2 | 2 | 59.1 | 5321 | 2260 | 0 |
| 002 | 2 | 2 | 52.8 | 5735 | 2031 | 0 |
| 001 | 3 | 2 | 57.3 | 5283 | 2230 | 0 |
| 002 | 3 | 2 | 98.8 | 7706 | 3979 | 0 |

All six attempts guessed `data/parkinsons.csv`, received `FileNotFoundError`, and ended at the file-discovery stage. The actual filenames were present in each task's `data/` directory. The measured outcome is therefore file discovery and error recovery under this model and tool protocol; statistical-analysis performance remains unmeasured.

The revised statements give the exact input filenames and parsing commands. The six traces above correspond to the original statements.

## Official CLI evaluation of the revised statements

PenguinHarness CLI 0.2.18 was run with Node.js 24.18.0, its default agent and Qwen3-4B through an OpenAI chat endpoint served by Transformers 5.15.1. The model used bfloat16, disabled thinking and server seed 20261101 on an H100. Each case had a fresh session and workspace, a 32,768-token context, 4,096 output tokens per request and a 1,800-second time limit. The native reference evaluator scored the resulting workspace.

| Case | Model requests | Seconds | Numerical result |
|---|---:|---:|---|
| 001 | 66 | 286.838 | Failed: prediction file absent |
| 002 | 5 | 31.164 | Failed: prediction file absent |

Both attempts read the correct input table. In case 001 the model extracted an incorrect participant identifier and then repeatedly attempted ineffective edits. In case 002 it loaded the data and ended with an intention to write the analysis. Both sessions ended before producing predictions. These outcomes identify implementation and completion failures under this small model. Statistical estimation accuracy remains unmeasured for these attempts.

The model messages, tool calls and outputs are in `official_cli/`, alongside the measured results. Workspace and library paths are abbreviated in the exported traces. `run_penguin_native.py` reproduces the CLI invocation and subsequent numerical evaluation. Supply the package, output directory, installed CLI path, Python executable and configured model id as its arguments.

## Reference analysis and verification

Both reference analyses passed the complete numerical verifiers. Fresh CPU fits in temporary workspaces also passed against the committed reference predictions, taking approximately 5 and 39 seconds respectively in the recorded environment. The executable procedure is `replay_references.py`, with software versions and outcomes in `reference_replay.json`.

Eight deliberately incorrect outputs, covering a missing prediction row, an invalid fold, an altered prediction and an incorrect metric in each task, were rejected. The check first requires the unmodified reference to pass and then verifies assertion failures for each altered output. The diagnostic calculation identifies 32 distinct participant labels in the CSV, compared with 31 participants in the source narrative. Reference fitting and scoring use the observed labels.

The diagnostic results show higher patient Brier error under patient splitting for both fixed estimators. The symptom-severity analysis shows a large validation-protocol gap and inconclusive conditional intervals for additional acoustic information in unseen patients. These estimates describe the supplied retrospective cohorts under the prescribed analysis.

## Reproduction

Recompute and grade both reference analyses on CPU using the task requirements:

```bash
python replay_references.py --package /path/to/packages/penguinharness-benchmark-biomedical-repeated-measures --output reference_replay.json
```

Install the scientific dependencies in the statement directories and PyTorch 2.6.0 with Transformers 5.15.1 in a GPU environment. Download the original Qwen/Qwen3-4B model separately.

```bash
python run_pilot.py --model /path/to/Qwen3-4B --package /path/to/packages/penguinharness-benchmark-biomedical-repeated-measures --output /path/to/pilot-results --attempt 1
```

Repeat with attempts 2 and 3. Model executions resume from saved conversation and random-generator state after an interruption. Hardware and software differences can change generated trajectories. The reference fits and numerical evaluation are separately reproducible on CPU.

The task package, reference calculations and pilot runner were prepared with assistance from OpenAI Codex. The exported pilot code and responses were generated by Qwen3-4B.
