# Hardware comparison: ibm_fez, round 2

Run `20261124-105849_hardware-round2`. Methods: no mitigation, our recipe (v1), IBM Runtime resilience levels 1 and 2.

## Jobs, in submission order

| Method | Job ID | Quantum seconds (IBM) | Resource Units (IBM) | Wall time s |
|---|---|---|---|---|
| ibm_rl2 | `dc2i17inj2vs73dgonn0` | 83.0 | 1.373 | 734 |
| ibm_rl1 | `dc2i6seq4uuc73a5bp1g` | 30.0 | 0.496 | 728 |
| recipe | `dc2ici5hdvas73bm8u0g` | 22.0 | 0.360 | 82 |
| recipe | `dc2id6lhdvas73bm8uvg` | 0.0 | 0.109 | 36 |
| none | `dc2idflhdvas73bm8vd0` | 27.0 | 0.439 | 45 |

IBM's full usage metrics for every job are saved verbatim in `results.json` (`metrics`).

## Quantum seconds

| Method | Estimated | Measured |
|---|---|---|
| none | 24.0 | 27.0 |
| recipe | 24.0 | 22.0 |
| ibm_rl1 | 23.3 | 30.0 |
| ibm_rl2 | 63.6 | 83.0 |

## RMSE vs exact (± bootstrap std)

| Circuit | 2q gates | None | Recipe | IBM level 1 | IBM level 2 |
|---|---|---|---|---|---|
| Bell | 1 | 0.0573 ± 0.0034 | 0.0148 ± 0.0095 | 0.0121 ± 0.0049 | 0.0141 ± 0.0029 |
| GHZ-5 | 4 | 0.1316 ± 0.0052 | 0.0105 ± 0.0122 | 0.0575 ± 0.0066 | 0.0602 ± 0.0078 |
| Ising-4 | 36 | 0.0022 ± 0.0042 | 0.0157 ± 0.0128 | 0.0237 ± 0.0043 | 0.0140 ± 0.0134 |
| Mirror-4 | 12 | 0.1004 ± 0.0029 | 0.0332 ± 0.0097 | 0.0672 ± 0.0012 | 0.0259 ± 0.0022 |
| Grover-4-3it | 111 | 0.4305 ± 0.0051 | 0.3293 ± 0.1461 | 0.4484 ± 0.0025 | 0.0301 ± 0.0065 |
| QFT-6 | 88 | 0.1096 ± 0.0024 | 0.0837 ± 0.0143 | 0.1020 ± 0.0023 | 0.0385 ± 0.0043 |
| QAOA-5-p2 | 34 | 0.1868 ± 0.0060 | 0.0621 ± 0.0204 | 0.1251 ± 0.0092 | 0.0217 ± 0.0070 |
| QAOA-6 | 31 | 0.1667 ± 0.0110 | 0.0654 ± 0.0303 | 0.1096 ± 0.0150 | 0.0659 ± 0.0177 |

## Pre-registered targets (PREREGISTRATION.md A7)

| Target | Result | Detail |
|---|---|---|
| H1 vs IBM level 2 | **FAIL** | recipe lower RMSE on 2/8; usage (RUs) recipe 0.469 vs level 2 1.373 |
| H2 vs IBM level 1 (deep) | **PASS** | mean over 5 deep: recipe 0.1112 vs 0.85 x level 1 0.1375 |
| H3 beats no mitigation | **PASS** | recipe clearly better than none on 6/8 |

