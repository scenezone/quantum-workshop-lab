# Hardware comparison: ibm_fez, round 1

Run `20261124-104424_hardware-round1`. Methods: no mitigation, our recipe (v1), IBM Runtime resilience levels 1 and 2.

## Jobs, in submission order

| Method | Job ID | Quantum seconds (IBM) | Resource Units (IBM) | Wall time s |
|---|---|---|---|---|
| none | `dc2hqceq4uuc73a5b8c0` | 27.0 | 0.439 | 287 |
| recipe | `dc2hskdhdvas73bm87u0` | 22.0 | 0.360 | 283 |
| recipe | `dc2huqthdvas73bm8asg` | 0.0 | 0.109 | 14 |
| ibm_rl1 | `dc2huuthdvas73bm8b50` | 30.0 | 0.496 | 45 |
| ibm_rl2 | `dc2hvclhdvas73bm8br0` | 83.0 | 1.373 | 119 |

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
| Bell | 1 | 0.0797 ± 0.0038 | 0.0126 ± 0.0102 | 0.0258 ± 0.0058 | 0.0255 ± 0.0081 |
| GHZ-5 | 4 | 0.1181 ± 0.0047 | 0.0137 ± 0.0137 | 0.0153 ± 0.0071 | 0.0449 ± 0.0019 |
| Ising-4 | 36 | 0.0090 ± 0.0054 | 0.0228 ± 0.0144 | 0.0340 ± 0.0059 | 0.0188 ± 0.0389 |
| Mirror-4 | 12 | 0.1196 ± 0.0031 | 0.0209 ± 0.0105 | 0.0689 ± 0.0010 | 0.0297 ± 0.0028 |
| Grover-4-3it | 111 | 0.4383 ± 0.0050 | 0.3365 ± 0.0791 | 0.4137 ± 0.0022 | 0.0295 ± 0.0066 |
| QFT-6 | 88 | 0.1231 ± 0.0024 | 0.0850 ± 0.0091 | 0.1037 ± 0.0023 | 0.0349 ± 0.0034 |
| QAOA-5-p2 | 34 | 0.1931 ± 0.0061 | 0.0401 ± 0.0196 | 0.1082 ± 0.0093 | 0.0344 ± 0.0112 |
| QAOA-6 | 31 | 0.1602 ± 0.0115 | 0.0883 ± 0.0324 | 0.1166 ± 0.0138 | 0.0154 ± 0.0141 |

## Pre-registered targets (PREREGISTRATION.md A7)

| Target | Result | Detail |
|---|---|---|
| H1 vs IBM level 2 | **FAIL** | recipe lower RMSE on 3/8; usage (RUs) recipe 0.469 vs level 2 1.373 |
| H2 vs IBM level 1 (deep) | **PASS** | mean over 5 deep: recipe 0.1145 vs 0.85 x level 1 0.1319 |
| H3 beats no mitigation | **PASS** | recipe clearly better than none on 7/8 |

