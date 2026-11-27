# Recipe v1.2 round on new circuits (Part H): fake_marrakesh (DRY RUN, local simulator)

Run `20261126-224957_hardware-v1-2-dryrun`. Methods: none, recipe v1; v1.2 computed from v1's counts. No IBM resilience levels and no comparison with them.

> **DRY RUN, not evidence.** Sampler jobs ran locally on a fake backend; seconds are estimates.

## Jobs

| Method | Job ID | Charged s | RUs | Resubmitted |
|---|---|---|---|---|
| none | `af1bbe26-1451-4669-803b-7513adbe603e` | None | None | - |
| recipe_v1 | `ada56bd0-3595-45b5-9580-e6ed8b31437e` | None | None | - |
| recipe_v1 | `0fde0b27-7eea-45f9-939e-d55e9aafc595` | None | None | - |

| Method | Estimated s | Charged s | RUs |
|---|---|---|---|
| none | 12.0 | 0 | 0 |
| recipe_v1 | 12.0 | 0 | 0 |

## Error vs exact (± bootstrap std)

| Circuit | Type | 2q | Exact | none | v1 (branch) | v1.2 (branch) | v1 class |
|---|---|---|---|---|---|---|---|
| W-4 | shallow | 6 | +1.000 | 0.0278 ± 0.0015 (+0.972) | 0.0017 ± 0.0034 (+0.998, exp) | 0.0017 ± 0.0034 (+0.998, exp) | good |
| Toffoli-3 | shallow | 7 | +1.000 | 0.0290 ± 0.0015 (+0.971) | 0.0027 ± 0.0041 (+1.003, exp) | 0.0027 ± 0.0041 (+1.003, exp) | good |
| CDKM-adder-3 | deep | 70 | +1.000 | 0.1396 ± 0.0031 (+0.860) | 0.0396 ± 0.0135 (+0.960, exp) | 0.0396 ± 0.0135 (+0.960, exp) | good |
| Draper-adder-4 | deep | 70 | +1.000 | 0.2206 ± 0.0039 (+0.779) | 0.0891 ± 0.0345 (+0.911, exp) | 0.0891 ± 0.0345 (+0.911, exp) | ambiguous |

## Flag rules

d(s) = readout-corrected value at scale s minus the fully mixed value. v1.2 uses decay and alive; one_exp (v1.1 only) is shown for information.

| Circuit | d(1) / d(3) / d(5) | SE(d5) | decay | alive | one_exp (not used) | v1.2 flagged |
|---|---|---|---|---|---|---|
| W-4 | +0.744 / +0.732 / +0.725 | 0.005 | pass | pass | pass | no |
| Toffoli-3 | +0.861 / +0.834 / +0.799 | 0.006 | pass | pass | pass | no |
| CDKM-adder-3 | +0.825 / +0.619 / +0.484 | 0.010 | pass | pass | pass | no |
| Draper-adder-4 | +0.746 / +0.491 / +0.297 | 0.009 | pass | pass | pass | no |

## Pre-registered target and reported comparisons (PREREGISTRATION.md Part H)

| Item | Result | Detail |
|---|---|---|
| T1 W-4: v1.2 not clearly worse than no mitigation | n/a (dry run) | v1.2 clearly better: 0.0017 vs 0.0278 (gap +0.0261, combined spread 0.0037) |
| T1 Toffoli-3: v1.2 not clearly worse than no mitigation | n/a (dry run) | v1.2 clearly better: 0.0027 vs 0.0290 (gap +0.0263, combined spread 0.0043) |
| T1 CDKM-adder-3: v1.2 not clearly worse than no mitigation | n/a (dry run) | v1.2 clearly better: 0.0396 vs 0.1396 (gap +0.1000, combined spread 0.0138) |
| T1 Draper-adder-4: v1.2 not clearly worse than no mitigation | n/a (dry run) | v1.2 clearly better: 0.0891 vs 0.2206 (gap +0.1315, combined spread 0.0347) |
| reported W-4: recipe_v1 vs none | reported (no target) | recipe_v1 clearly better: 0.0017 vs 0.0278 (gap +0.0261, combined spread 0.0037) |
| reported W-4: recipe_v1_2 vs recipe_v1 | reported (no target) | recipe_v1_2 no clear difference: 0.0017 vs 0.0017 (gap +0.0000, combined spread 0.0048) |
| reported W-4: recipe_v1_2 vs none | reported (no target) | recipe_v1_2 clearly better: 0.0017 vs 0.0278 (gap +0.0261, combined spread 0.0037) |
| reported Toffoli-3: recipe_v1 vs none | reported (no target) | recipe_v1 clearly better: 0.0027 vs 0.0290 (gap +0.0263, combined spread 0.0043) |
| reported Toffoli-3: recipe_v1_2 vs recipe_v1 | reported (no target) | recipe_v1_2 no clear difference: 0.0027 vs 0.0027 (gap +0.0000, combined spread 0.0058) |
| reported Toffoli-3: recipe_v1_2 vs none | reported (no target) | recipe_v1_2 clearly better: 0.0027 vs 0.0290 (gap +0.0263, combined spread 0.0043) |
| reported CDKM-adder-3: recipe_v1 vs none | reported (no target) | recipe_v1 clearly better: 0.0396 vs 0.1396 (gap +0.1000, combined spread 0.0138) |
| reported CDKM-adder-3: recipe_v1_2 vs recipe_v1 | reported (no target) | recipe_v1_2 no clear difference: 0.0396 vs 0.0396 (gap +0.0000, combined spread 0.0191) |
| reported CDKM-adder-3: recipe_v1_2 vs none | reported (no target) | recipe_v1_2 clearly better: 0.0396 vs 0.1396 (gap +0.1000, combined spread 0.0138) |
| reported Draper-adder-4: recipe_v1 vs none | reported (no target) | recipe_v1 clearly better: 0.0891 vs 0.2206 (gap +0.1315, combined spread 0.0347) |
| reported Draper-adder-4: recipe_v1_2 vs recipe_v1 | reported (no target) | recipe_v1_2 no clear difference: 0.0891 vs 0.0891 (gap +0.0000, combined spread 0.0487) |
| reported Draper-adder-4: recipe_v1_2 vs none | reported (no target) | recipe_v1_2 clearly better: 0.0891 vs 0.2206 (gap +0.1315, combined spread 0.0347) |

Four circuits on one device and one day show a direction, not a proof.
