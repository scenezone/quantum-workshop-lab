# Hardware comparison: ibm_fez (smoke job)

Run `20261124-104212_hardware-smoke`. Methods: no mitigation, our recipe (v1), IBM Runtime resilience levels 1 and 2.

## Jobs, in submission order

| Method | Job ID | Quantum seconds (IBM) | Resource Units (IBM) | Wall time s |
|---|---|---|---|---|
| none | `dc2hpbdhdvas73bm83og` | 0.0 | 0.033 | 27 |
| ibm_rl1 | `dc2hpids2omc738c0fv0` | 3.0 | 0.038 | 11 |

IBM's full usage metrics for every job are saved verbatim in `results.json` (`metrics`).

## Quantum seconds

| Method | Estimated | Measured |
|---|---|---|
| none | 0.3 | 0.0 |
| recipe | nan | n/a |
| ibm_rl1 | 0.3 | 3.0 |
| ibm_rl2 | nan | n/a |

## RMSE vs exact (± bootstrap std)

| Circuit | 2q gates | None | Recipe | IBM level 1 | IBM level 2 |
|---|---|---|---|---|---|
| Bell | 1 | 0.0780 ± 0.0122 | not run | 0.0200 ± 0.0105 | not run |

## Pre-registered targets (PREREGISTRATION.md A7)

| Target | Result | Detail |
|---|---|---|
Not evaluated: this run does not contain all four methods (smoke run, or stopped at the usage cap).
