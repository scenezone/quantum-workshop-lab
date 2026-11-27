# Recipe v1 replication round (Part G): ibm_marrakesh

Run `20261126-120458_hardware-v1-replication`. Circuits: Heisenberg-4, QPE-4 (seen data since 25 Nov). Order: ibm_rl2 → recipe_v1 → none. Reference: `20261125-145032_hardware-v2`.

## Jobs, in submission order

| Method | Job ID | Charged s | RUs | Resubmitted |
|---|---|---|---|---|
| ibm_rl2 | `dc3t66anj2vs73divdug` | 49.0 | 0.800961 | - |
| recipe_v1 | `dc3t6mds2omc738e7n2g` | 12.0 | 0.196533 | - |
| recipe_v1 | `dc3t6r5hdvas73bohko0` | 5.0 | 0.068883 | - |
| none | `dc3t6tuq4uuc73a7keog` | 15.0 | 0.236997 | - |

| Method | Estimated s | Charged s | RUs |
|---|---|---|---|
| ibm_rl2 | 46.4 | 49.0 | 0.800961 |
| recipe_v1 | 12.0 | 17.0 | 0.265416 |
| none | 12.0 | 15.0 | 0.236997 |

## Error vs exact (± bootstrap std)

| Circuit | 2q | Exact | none | recipe_v1 | v1_clip | ibm_rl2 |
|---|---|---|---|---|---|---|
| Heisenberg-4 | 44 | -0.646 | 0.1238 ± 0.0038 (-0.522, -) | 0.0027 ± 0.0062 (-0.644, linear) | 0.0027 ± 0.0057 (-0.644, linear) | 0.0588 ± 0.0042 (-0.587, -) |
| QPE-4 | 26 | +1.000 | 0.3066 ± 0.0028 (+0.693, -) | 0.2908 ± 0.0077 (+0.709, linear) | 0.2908 ± 0.0084 (+0.709, linear) | 0.0765 ± 0.0049 (+0.923, -) |

## Pre-registered targets (PREREGISTRATION.md Part G)

| Target | Result | Detail |
|---|---|---|
| R1 Heisenberg-4: v1 clearly better than no mitigation | **PASS** | v1 clearly better: 0.0027 vs 0.1238 (gap +0.1211, combined spread 0.0073) |
| R2 Heisenberg-4: v1 not clearly worse than IBM level 2 | **PASS** | v1 clearly better: 0.0027 vs 0.0588 (gap +0.0561, combined spread 0.0075) |
| R1 QPE-4: v1 clearly better than no mitigation | **PASS** | v1 clearly better: 0.2908 vs 0.3066 (gap +0.0158, combined spread 0.0082) |
| R2 QPE-4: v1 not clearly worse than IBM level 2 | **FAIL** | v1 clearly worse: 0.2908 vs 0.0765 (gap -0.2143, combined spread 0.0092) |
| R2-cost: v1 RUs <= 0.5 x IBM level 2 RUs (round total) | **PASS** | v1 0.265 RU vs 0.5 x L2 = 0.400 RU |

## Replication: verdicts on 25 Nov vs now

| Circuit | Comparison | 25 Nov | Now | Same verdict |
|---|---|---|---|---|
| Heisenberg-4 | recipe_v1 vs none | clearly better (0.0197 vs 0.1242 (gap +0.1045, combined spread 0.0125)) | clearly better (0.0027 vs 0.1238 (gap +0.1211, combined spread 0.0073)) | yes |
| Heisenberg-4 | recipe_v1 vs ibm_rl2 | no clear difference (0.0197 vs 0.0170 (gap -0.0027, combined spread 0.0133)) | clearly better (0.0027 vs 0.0588 (gap +0.0561, combined spread 0.0075)) | **no** |
| Heisenberg-4 | v1_clip vs recipe_v1 | no clear difference (0.0197 vs 0.0197 (gap +0.0000, combined spread 0.0165)) | no clear difference (0.0027 vs 0.0027 (gap +0.0000, combined spread 0.0084)) | yes |
| QPE-4 | recipe_v1 vs none | clearly better (0.0151 vs 0.1601 (gap +0.1450, combined spread 0.0079)) | clearly better (0.2908 vs 0.3066 (gap +0.0158, combined spread 0.0082)) | yes |
| QPE-4 | recipe_v1 vs ibm_rl2 | clearly better (0.0151 vs 0.0616 (gap +0.0465, combined spread 0.0077)) | clearly worse (0.2908 vs 0.0765 (gap -0.2143, combined spread 0.0092)) | **no** |
| QPE-4 | v1_clip vs recipe_v1 | clearly better (0.0000 vs 0.0151 (gap +0.0151, combined spread 0.0076)) | no clear difference (0.2908 vs 0.2908 (gap +0.0000, combined spread 0.0114)) | **no** |

`v1_clip` is reported, no target. Two circuits and two rounds show a direction, not a proof.
