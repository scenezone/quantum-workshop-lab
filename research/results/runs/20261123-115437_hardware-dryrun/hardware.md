# Hardware comparison: FakeKingston (DRY RUN, local simulator)

Run `20261123-115437_hardware-dryrun`. Methods: no mitigation, our recipe (vv1), IBM Runtime resilience levels 1 and 2.

> **DRY RUN, not evidence.** The Sampler jobs (none, recipe) ran locally on a fake backend, one PUB per local job. The IBM Estimator jobs were built and checked but not executed: local mode cannot simulate observables laid out on all 156 qubits, and it ignores resilience levels anyway. Quantum seconds are estimates.

## Quantum seconds

| Method | Estimated | Measured |
|---|---|---|
| none | 24.0 | n/a |
| recipe | 24.0 | n/a |
| ibm_rl1 | 23.2 | n/a |
| ibm_rl2 | 63.4 | n/a |

## RMSE vs exact (± bootstrap std)

| Circuit | 2q gates | None | Recipe | IBM level 1 | IBM level 2 |
|---|---|---|---|---|---|
| Bell | 1 | 0.0211 ± 0.0019 | 0.0012 ± 0.0040 | not run | not run |
| GHZ-5 | 4 | 0.0677 ± 0.0037 | 0.0150 ± 0.0101 | not run | not run |
| Ising-4 | 36 | 0.0100 ± 0.0059 | 0.0093 ± 0.0110 | not run | not run |
| Mirror-4 | 12 | 0.0645 ± 0.0024 | 0.0112 ± 0.0070 | not run | not run |
| Grover-4-3it | 111 | 0.2298 ± 0.0045 | 0.0019 ± 0.0136 | not run | not run |
| QFT-6 | 88 | 0.0459 ± 0.0017 | 0.0186 ± 0.0054 | not run | not run |
| QAOA-5-p2 | 34 | 0.1176 ± 0.0046 | 0.0102 ± 0.0103 | not run | not run |
| QAOA-6 | 31 | 0.1063 ± 0.0107 | 0.0137 ± 0.0206 | not run | not run |

## Pre-registered targets (PREREGISTRATION.md A7)

| Target | Result | Detail |
|---|---|---|
| H1 vs IBM level 2 | n/a (dry run) | recipe lower RMSE on 0/8; quantum s recipe 24.0 vs level 2 63.4 |
| H2 vs IBM level 1 (deep) | n/a (dry run) | mean over 5 deep: recipe 0.0107 vs 0.85 x level 1 nan |
| H3 beats no mitigation | n/a (dry run) | recipe clearly better than none on 7/8 |
