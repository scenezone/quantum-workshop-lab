# Recipe v1 replication round (Part G): fake_kingston (DRY RUN, local simulator)

Run `20261126-120029_hardware-v1-replication-dryrun`. Circuits: Heisenberg-4, QPE-4 (seen data since 25 Nov). Order: ibm_rl2 → recipe_v1 → none. Reference: `20261125-145032_hardware-v2`.

> **DRY RUN, not evidence.** Sampler jobs ran locally; the IBM Estimator job was built but not executed.

## Jobs, in submission order

| Method | Job ID | Charged s | RUs | Resubmitted |
|---|---|---|---|---|
| recipe_v1 | `8e25456b-ea63-4232-8704-aae7546a07d4` | None | None | - |
| recipe_v1 | `1ae75da5-7d1b-49f2-b7a2-d1cd49ece9ee` | None | None | - |
| none | `3f0379de-fd2c-4761-85e6-d9f9c95f37ec` | None | None | - |

| Method | Estimated s | Charged s | RUs |
|---|---|---|---|
| ibm_rl2 | 46.6 | None | None |
| recipe_v1 | 12.0 | 0 | 0 |
| none | 12.0 | 0 | 0 |

## Error vs exact (± bootstrap std)

| Circuit | 2q | Exact | none | recipe_v1 | v1_clip | ibm_rl2 |
|---|---|---|---|---|---|---|
| Heisenberg-4 | 44 | -0.646 | 0.0704 ± 0.0038 (-0.576, -) | 0.0084 ± 0.0081 (-0.655, exp) | 0.0084 ± 0.0080 (-0.655, exp) | not run |
| QPE-4 | 26 | +1.000 | 0.0812 ± 0.0019 (+0.919, -) | 0.0038 ± 0.0041 (+0.996, exp) | 0.0038 ± 0.0051 (+0.996, exp) | not run |

## Pre-registered targets (PREREGISTRATION.md Part G)

| Target | Result | Detail |
|---|---|---|
| R1 Heisenberg-4: v1 clearly better than no mitigation | n/a (dry run) | v1 clearly better: 0.0084 vs 0.0704 (gap +0.0621, combined spread 0.0090) |
| R2 Heisenberg-4: v1 not clearly worse than IBM level 2 | n/a (dry run) | v1 no clear difference: 0.0084 vs nan (gap +nan, combined spread nan) |
| R1 QPE-4: v1 clearly better than no mitigation | n/a (dry run) | v1 clearly better: 0.0038 vs 0.0812 (gap +0.0775, combined spread 0.0045) |
| R2 QPE-4: v1 not clearly worse than IBM level 2 | n/a (dry run) | v1 no clear difference: 0.0038 vs nan (gap +nan, combined spread nan) |
| R2-cost: v1 RUs <= 0.5 x IBM level 2 RUs (round total) | n/a (dry run) | v1 0.000 RU vs 0.5 x L2 = nan RU |

## Replication: verdicts on 25 Nov vs now

| Circuit | Comparison | 25 Nov | Now | Same verdict |
|---|---|---|---|---|
| Heisenberg-4 | recipe_v1 vs none | clearly better (0.0197 vs 0.1242 (gap +0.1045, combined spread 0.0125)) | clearly better (0.0084 vs 0.0704 (gap +0.0621, combined spread 0.0090)) | yes |
| Heisenberg-4 | recipe_v1 vs ibm_rl2 | no clear difference (0.0197 vs 0.0170 (gap -0.0027, combined spread 0.0133)) | no clear difference (0.0084 vs nan (gap +nan, combined spread nan)) | yes |
| Heisenberg-4 | v1_clip vs recipe_v1 | no clear difference (0.0197 vs 0.0197 (gap +0.0000, combined spread 0.0165)) | no clear difference (0.0084 vs 0.0084 (gap +0.0000, combined spread 0.0114)) | yes |
| QPE-4 | recipe_v1 vs none | clearly better (0.0151 vs 0.1601 (gap +0.1450, combined spread 0.0079)) | clearly better (0.0038 vs 0.0812 (gap +0.0775, combined spread 0.0045)) | yes |
| QPE-4 | recipe_v1 vs ibm_rl2 | clearly better (0.0151 vs 0.0616 (gap +0.0465, combined spread 0.0077)) | no clear difference (0.0038 vs nan (gap +nan, combined spread nan)) | **no** |
| QPE-4 | v1_clip vs recipe_v1 | clearly better (0.0000 vs 0.0151 (gap +0.0151, combined spread 0.0076)) | no clear difference (0.0038 vs 0.0038 (gap +0.0000, combined spread 0.0065)) | **no** |

`v1_clip` is reported, no target. Two circuits and two rounds show a direction, not a proof.
