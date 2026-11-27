# Recipe v1.2 round on new circuits (Part H): ibm_marrakesh

Run `20261126-225723_hardware-v1-2`. Methods: none, recipe v1; v1.2 computed from v1's counts. No IBM resilience levels and no comparison with them.

## Jobs

| Method | Job ID | Charged s | RUs | Resubmitted |
|---|---|---|---|---|
| none | `dc46nvmq4uuc73a88nd0` | 15.0 | 0.238168 | - |
| recipe_v1 | `dc46o5ts2omc738erep0` | 12.0 | 0.197652 | - |
| recipe_v1 | `dc46oblhdvas73bp5ol0` | 5.0 | 0.068928 | - |

| Method | Estimated s | Charged s | RUs |
|---|---|---|---|
| none | 12.0 | 15.0 | 0.238168 |
| recipe_v1 | 12.0 | 17.0 | 0.26658 |

## Error vs exact (± bootstrap std)

| Circuit | Type | 2q | Exact | none | v1 (branch) | v1.2 (branch) | v1 class |
|---|---|---|---|---|---|---|---|
| W-4 | shallow | 6 | +1.000 | 0.0927 ± 0.0027 (+0.907) | 0.0394 ± 0.0082 (+0.961, exp) | 0.0394 ± 0.0082 (+0.961, exp) | good |
| Toffoli-3 | shallow | 7 | +1.000 | 0.0690 ± 0.0024 (+0.931) | 0.0087 ± 0.0066 (+0.991, exp) | 0.0087 ± 0.0066 (+0.991, exp) | good |
| CDKM-adder-3 | deep | 70 | +1.000 | 0.2856 ± 0.0041 (+0.714) | 0.0658 ± 0.0166 (+0.934, exp) | 0.0658 ± 0.0166 (+0.934, exp) | ambiguous |
| Draper-adder-4 | deep | 70 | +1.000 | 0.3560 ± 0.0043 (+0.644) | 0.1949 ± 0.0144 (+0.805, exp) | 0.1949 ± 0.0144 (+0.805, exp) | failure |

## Flag rules

d(s) = readout-corrected value at scale s minus the fully mixed value. v1.2 uses decay and alive; one_exp (v1.1 only) is shown for information.

| Circuit | d(1) / d(3) / d(5) | SE(d5) | decay | alive | one_exp (not used) | v1.2 flagged |
|---|---|---|---|---|---|---|
| W-4 | +0.678 / +0.620 / +0.563 | 0.008 | pass | pass | pass | no |
| Toffoli-3 | +0.825 / +0.752 / +0.681 | 0.008 | pass | pass | pass | no |
| CDKM-adder-3 | +0.702 / +0.450 / +0.293 | 0.009 | pass | pass | pass | no |
| Draper-adder-4 | +0.610 / +0.414 / +0.278 | 0.009 | pass | pass | pass | no |

## Pre-registered target and reported comparisons (PREREGISTRATION.md Part H)

| Item | Result | Detail |
|---|---|---|
| T1 W-4: v1.2 not clearly worse than no mitigation | **PASS** | v1.2 clearly better: 0.0394 vs 0.0927 (gap +0.0533, combined spread 0.0086) |
| T1 Toffoli-3: v1.2 not clearly worse than no mitigation | **PASS** | v1.2 clearly better: 0.0087 vs 0.0690 (gap +0.0603, combined spread 0.0070) |
| T1 CDKM-adder-3: v1.2 not clearly worse than no mitigation | **PASS** | v1.2 clearly better: 0.0658 vs 0.2856 (gap +0.2198, combined spread 0.0171) |
| T1 Draper-adder-4: v1.2 not clearly worse than no mitigation | **PASS** | v1.2 clearly better: 0.1949 vs 0.3560 (gap +0.1611, combined spread 0.0151) |
| reported W-4: recipe_v1 vs none | reported (no target) | recipe_v1 clearly better: 0.0394 vs 0.0927 (gap +0.0533, combined spread 0.0086) |
| reported W-4: recipe_v1_2 vs recipe_v1 | reported (no target) | recipe_v1_2 no clear difference: 0.0394 vs 0.0394 (gap +0.0000, combined spread 0.0116) |
| reported W-4: recipe_v1_2 vs none | reported (no target) | recipe_v1_2 clearly better: 0.0394 vs 0.0927 (gap +0.0533, combined spread 0.0086) |
| reported Toffoli-3: recipe_v1 vs none | reported (no target) | recipe_v1 clearly better: 0.0087 vs 0.0690 (gap +0.0603, combined spread 0.0070) |
| reported Toffoli-3: recipe_v1_2 vs recipe_v1 | reported (no target) | recipe_v1_2 no clear difference: 0.0087 vs 0.0087 (gap +0.0000, combined spread 0.0094) |
| reported Toffoli-3: recipe_v1_2 vs none | reported (no target) | recipe_v1_2 clearly better: 0.0087 vs 0.0690 (gap +0.0603, combined spread 0.0070) |
| reported CDKM-adder-3: recipe_v1 vs none | reported (no target) | recipe_v1 clearly better: 0.0658 vs 0.2856 (gap +0.2198, combined spread 0.0171) |
| reported CDKM-adder-3: recipe_v1_2 vs recipe_v1 | reported (no target) | recipe_v1_2 no clear difference: 0.0658 vs 0.0658 (gap +0.0000, combined spread 0.0235) |
| reported CDKM-adder-3: recipe_v1_2 vs none | reported (no target) | recipe_v1_2 clearly better: 0.0658 vs 0.2856 (gap +0.2198, combined spread 0.0171) |
| reported Draper-adder-4: recipe_v1 vs none | reported (no target) | recipe_v1 clearly better: 0.1949 vs 0.3560 (gap +0.1611, combined spread 0.0151) |
| reported Draper-adder-4: recipe_v1_2 vs recipe_v1 | reported (no target) | recipe_v1_2 no clear difference: 0.1949 vs 0.1949 (gap +0.0000, combined spread 0.0204) |
| reported Draper-adder-4: recipe_v1_2 vs none | reported (no target) | recipe_v1_2 clearly better: 0.1949 vs 0.3560 (gap +0.1611, combined spread 0.0151) |

Four circuits on one device and one day show a direction, not a proof.
