# Recipe v2 hardware round: FakeKingston (DRY RUN, local simulator)

Run `20261125-125318_hardware-v2-dryrun`. Circuits: the v2 held-out set (Heisenberg-4, QPE-4). Methods: no mitigation, recipe v1, recipe v2 (8 twirls, scales 1/2/3, clip), IBM resilience level 2; secondary (no target): v1 data + clip, and recipe v2 at 1/1.5/2.

> **DRY RUN, not evidence.** Sampler jobs ran locally on a fake backend; the IBM Estimator job was built and checked but not executed. Usage is an estimate.

## Jobs, in submission order

| Method | Job ID | Shots per PUB | Charged s | RUs |
|---|---|---|---|---|
| none | `e5591fe6-f859-4097-929f-bf3837d016cf` | 23486 | None | None |
| recipe_v1 | `eab60e8a-1d33-48a7-affe-adc9c501fee5` | 6155 | None | None |
| recipe_v1 | `61097665-19ce-4da5-9fbd-e53b74a699f6` | 2308 | None | None |
| recipe_v2 | `3b62bca5-099c-4325-945e-ee0d1917c62a` | 778 | None | None |
| recipe_v2 | `aada21f1-7b18-4117-94e0-abe0eb18f868` | 2334 | None | None |
| v2_s15 | `862d16db-8e76-4b6b-9789-62e368a4e649` | 781 | None | None |
| v2_s15 | `694d3df6-a9c9-4f67-b827-02cad3c32cc1` | 2343 | None | None |

| Method | Estimated s | Charged s | RUs |
|---|---|---|---|
| none | 12.0 | 0 | 0 |
| recipe_v1 | 12.0 | 0 | 0 |
| recipe_v2 | 12.0 | 0 | 0 |
| ibm_rl2 | 46.6 | None | None |
| v2_s15 | 12.0 | 0 | 0 |

## Error vs exact (± bootstrap std)

| Circuit | 2q | Exact | none | recipe_v1 | v1_clip | recipe_v2 | v2_s15 | ibm_rl2 |
|---|---|---|---|---|---|---|---|---|
| Heisenberg-4 | 44 | -0.646 | 0.0690 ± 0.0036 (-0.577, -) | 0.0013 ± 0.0063 (-0.645, exp) | 0.0013 ± 0.0070 (-0.645, exp) | 0.0040 ± 0.0080 (-0.642, exp) | 0.0160 ± 0.0135 (-0.630, exp) | not run |
| QPE-4 | 26 | +1.000 | 0.0851 ± 0.0018 (+0.915, -) | 0.0016 ± 0.0031 (+0.998, exp) | 0.0000 ± 0.0009 (+1.000, exp+clip) | 0.0141 ± 0.0075 (+0.986, exp) | 0.0285 ± 0.0100 (+0.972, exp) | not run |

Secondary methods (Part F), no target uses them: `v1_clip` = recipe v1's data with v2's rule; `v2_s15` = recipe v2 at nominal scales 1/1.5/2 (own jobs, same budget, submitted last).

## Pre-registered targets (PREREGISTRATION.md Part F)

| Target | Result | Detail |
|---|---|---|
| G1 Heisenberg-4: v2 clearly better than recipe v1 | n/a (dry run) | v2 no clear difference: 0.0040 vs 0.0013 (gap -0.0026, combined spread 0.0102) |
| G2 Heisenberg-4: v2 not clearly worse than IBM level 2 | n/a (dry run) | v2 no clear difference: 0.0040 vs nan (gap +nan, combined spread nan) |
| G3 Heisenberg-4: v2 clearly better than no mitigation | n/a (dry run) | v2 clearly better: 0.0040 vs 0.0690 (gap +0.0651, combined spread 0.0088) |
| G1 QPE-4: v2 clearly better than recipe v1 | n/a (dry run) | v2 clearly worse: 0.0141 vs 0.0016 (gap -0.0125, combined spread 0.0081) |
| G2 QPE-4: v2 not clearly worse than IBM level 2 | n/a (dry run) | v2 no clear difference: 0.0141 vs nan (gap +nan, combined spread nan) |
| G3 QPE-4: v2 clearly better than no mitigation | n/a (dry run) | v2 clearly better: 0.0141 vs 0.0851 (gap +0.0710, combined spread 0.0077) |
| G2-cost: v2 RUs <= 0.5 x IBM level 2 RUs (round total) | n/a (dry run) | v2 0.000 RU vs 0.5 x L2 = nan RU |
| secondary Heisenberg-4: v1_clip vs recipe v2 | reported (no target) | v1_clip no clear difference: 0.0013 vs 0.0040 (gap +0.0026, combined spread 0.0107) |
| secondary Heisenberg-4: v2_s15 vs recipe v2 | reported (no target) | v2_s15 no clear difference: 0.0160 vs 0.0040 (gap -0.0120, combined spread 0.0157) |
| secondary QPE-4: v1_clip vs recipe v2 | reported (no target) | v1_clip clearly better: 0.0000 vs 0.0141 (gap +0.0141, combined spread 0.0076) |
| secondary QPE-4: v2_s15 vs recipe v2 | reported (no target) | v2_s15 clearly worse: 0.0285 vs 0.0141 (gap -0.0144, combined spread 0.0125) |

Two circuits and one round can show a direction, not a proof (Part F6).