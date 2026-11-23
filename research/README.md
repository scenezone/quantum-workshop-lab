# Research: error mitigation and circuit optimization

Experiments for the planned mitigation and optimization layer on top of Qiskit. This folder is separate from the app: nothing in `backend/` or `frontend/` imports it, and CI does not run it.

Everything runs on local simulators (Qiskit Aer with fake IBM backend noise). No IBM account or hardware minutes are used.

| File | What it is |
|---|---|
| [POC_REPORT.md](POC_REPORT.md) | Proof-of-concept simulation report: method, data, results, conclusion |
| [PREREGISTRATION.md](PREREGISTRATION.md) | Targets written before results: held-out set, recipe, hardware targets, deviations |
| [DECISIONS.md](DECISIONS.md) | Agreed rules: budget, baselines, metrics, observables, open items |
| `baseline.py` | 14 training circuits, no mitigation, optimization levels 0-3, two backends |
| `heldout.py` | 6 held-out test circuits (never used to design the recipe) |
| `mitigation.py` | Mitigation methods at an equal quantum-seconds budget, from saved raw counts; `--set train` or `--set test` |
| `recipe.py` | Recipe v1 (frozen): readout+ZNE with guarded exponential or linear extrapolation per observable |
| `hardware.py` | Hardware comparison vs IBM resilience levels 1 and 2. Dry run by default; never submits without explicit flags |
| `selection_compare.py` | Transpiler seed selection: fewest gates vs highest ESP |
| `layout_check.py` | Which physical qubits a circuit uses, and how noisy they are |
| `folding.py` | Native unitary folding for ZNE (with self-checks) |
| `runlog.py` | Run folders: manifest + raw counts for every run |
| `zne_smoke.py` | Negative result: mitiq's own folding mis-scales ECR circuits |

## Setup

The research code uses its own virtual environment, with a newer Qiskit than the app. `FakeKingston` is only available in newer `qiskit-ibm-runtime` releases, and the app's pinned versions stay untouched.

It needs **Python 3.11 or 3.12**, because every usable `mitiq` release requires Python < 3.13. On Python 3.13, pip silently installs an empty `mitiq 0.0.0` placeholder instead.

```bash
cd research
py -3.12 -m venv .venv                                       # Windows
.venv/Scripts/python -m pip install -r requirements.txt
python3.12 -m venv .venv                                     # macOS / Linux
.venv/bin/python -m pip install -r requirements.txt
```

## Raw data and run records

Every run of `baseline.py`, `mitigation.py` and `selection_compare.py` creates `results/runs/<timestamp>_<kind>/` containing:

- `manifest.json`: the command, full configuration, seeds, a plain-language description of the method, package versions and git commit
- `counts*.json`: raw measurement counts, from which every reported number is computed
- the reports (`.md`, `.csv`) for that run

Run folders are never overwritten. The latest reports are also copied to the top of `results/` for convenience. `results/runs/20261120-142019_mitigation-v1-noraw/` is an early run from before raw counts were saved, and is kept as a record.

## Baseline

`baseline.py` runs 14 circuits **without error mitigation**: 10 core (Bell, GHZ-3/5, Grover-2/3, QFT-3/4, Bernstein-Vazirani-4, QAOA-3/4) and 4 deep (GHZ-7, Grover-4 with 2 iterations, QFT-5, QAOA-4 with p=2). They run on `FakeSherbrooke` (Eagle) and `FakeKingston` (Heron r2) at optimization levels 0-3.

For each configuration it transpiles with 20 seeds and keeps the best (fewest two-qubit gates, then depth). It then simulates 10 repeats and reports mean ± std of TVD, or of approximation ratio for QAOA.

```bash
.venv/Scripts/python baseline.py                     # a few minutes
```

## Mitigation

`mitigation.py` compares mitigation methods on `FakeKingston` at an **equal budget of 3.0 estimated quantum seconds per circuit per method**, overhead included. Estimated QPU time = Σ shots × (circuit duration + 250 µs rep delay); shots are derived from it.

The methods are none, readout, ZNE and readout+ZNE, each ZNE flavour with Richardson, linear, exponential and guarded-exponential extrapolation, plus the frozen recipe. The metric is RMSE of fixed observables vs exact values over 10 repeats. These are our own implementations, not Qiskit Runtime resilience levels.

It simulates each distinct circuit once and splits the shot record into disjoint chunks, so a run takes a few minutes. Analysis reads only the saved counts, so new estimators can be tried without simulating again. The held-out set refuses to run until the recipe is frozen, and its report evaluates the pre-registered targets.

```bash
.venv/Scripts/python mitigation.py --set train                       # 14 training circuits
.venv/Scripts/python mitigation.py --set test                        # 6 held-out circuits + targets
.venv/Scripts/python mitigation.py --analyze results/runs/<id>_mitigation-train   # re-analyze saved counts
```

## Hardware

`hardware.py` runs the hardware comparison: Bell, GHZ-5 and the 6 held-out circuits, with no mitigation, the recipe, and IBM resilience levels 1 and 2, in 5 jobs, reading back each job's measured `quantum_seconds`.

The default is a **dry run** on `FakeKingston`. It builds every job, runs the Sampler jobs locally, and prints the QPU-time estimate. The IBM Estimator jobs are built but not executed locally (see the dry-run report). Real hardware needs `--submit`, a saved IBM Quantum account, and `--confirm-qpu-seconds` at least equal to the estimate.

```bash
.venv/Scripts/python hardware.py                                                    # dry run (~17 min)
.venv/Scripts/python hardware.py --submit --backend ibm_kingston --confirm-qpu-seconds 200
```

## Seed selection

`selection_compare.py` compares two ways of choosing among 20 transpiled candidates: (A) fewest two-qubit gates then depth, and (B) highest ESP. Both use compile-time information only. ESP is partly circular on fake backends; see the caveat in the report.

```bash
.venv/Scripts/python selection_compare.py
```

## Other tools

```bash
.venv/Scripts/python layout_check.py                  # GHZ-5 qubits, errors, ESP vs TVD
.venv/Scripts/python folding.py                       # folding equivalence self-checks
.venv/Scripts/python zne_smoke.py                     # mitiq-folding negative result
```

All seeds are fixed, so reruns give identical numbers.
