# Recipe v2 hardware round: ibm_marrakesh

Run `20261125-145032_hardware-v2`. Circuits: the v2 held-out set (Heisenberg-4, QPE-4). Methods: no mitigation, recipe v1, recipe v2 (8 twirls, scales 1/2/3, clip), IBM resilience level 2; secondary (no target): v1 data + clip, and recipe v2 at 1/1.5/2.

## Jobs, in submission order

| Method | Job ID | Shots per PUB | Charged s | RUs |
|---|---|---|---|---|
| none | `dc3agols2omc738d7nlg` | 23422 | 15.0 | 0.236991 |
| recipe_v1 | `dc3agumq4uuc73a6jheg` | 6129 | 12.0 | 0.196557 |
| recipe_v1 | `dc3ah42nj2vs73dhvhhg` | 2298 | 5.0 | 0.068865 |
| recipe_v2 | `dc3ah75hdvas73bngh8g` | 776 | 12.0 | 0.197535 |
| recipe_v2 | `dc3ahdanj2vs73dhvht0` | 2328 | 5.0 | 0.069393 |
| ibm_rl2 | `dc3ahi2nj2vs73dhvi80` | n/a | 48.0 | 0.799537 |
| v2_s15 | `dc3ai4qnj2vs73dhvj2g` | 779 | 12.0 | 0.197381 |
| v2_s15 | `dc3aib6q4uuc73a6jjk0` | 2337 | 5.0 | 0.069551 |

| Method | Estimated s | Charged s | RUs |
|---|---|---|---|
| none | 12.0 | 15.0 | 0.236991 |
| recipe_v1 | 12.0 | 17.0 | 0.265422 |
| recipe_v2 | 12.0 | 17.0 | 0.266928 |
| ibm_rl2 | 46.4 | 48.0 | 0.799537 |
| v2_s15 | 12.0 | 17.0 | 0.266932 |

## Error vs exact (± bootstrap std)

| Circuit | 2q | Exact | none | recipe_v1 | v1_clip | recipe_v2 | v2_s15 | ibm_rl2 |
|---|---|---|---|---|---|---|---|---|
| Heisenberg-4 | 44 | -0.646 | 0.1242 ± 0.0037 (-0.522, -) | 0.0197 ± 0.0119 (-0.666, exp) | 0.0197 ± 0.0115 (-0.666, exp) | 0.0466 ± 0.0134 (-0.600, exp) | 0.0292 ± 0.0180 (-0.617, exp) | 0.0170 ± 0.0060 (-0.629, -) |
| QPE-4 | 26 | +1.000 | 0.1601 ± 0.0022 (+0.840, -) | 0.0151 ± 0.0076 (+0.985, exp) | 0.0000 ± 0.0000 (+1.000, exp+clip) | 0.0399 ± 0.0098 (+0.960, exp) | 0.0618 ± 0.0122 (+0.938, exp) | 0.0616 ± 0.0012 (+0.938, -) |

Secondary methods (Part F), no target uses them: `v1_clip` = recipe v1's data with v2's rule; `v2_s15` = recipe v2 at nominal scales 1/1.5/2 (own jobs, same budget, submitted last).

## Pre-registered targets (PREREGISTRATION.md Part F)

| Target | Result | Detail |
|---|---|---|
| G1 Heisenberg-4: v2 clearly better than recipe v1 | **FAIL** | v2 clearly worse: 0.0466 vs 0.0197 (gap -0.0270, combined spread 0.0179) |
| G2 Heisenberg-4: v2 not clearly worse than IBM level 2 | **FAIL** | v2 clearly worse: 0.0466 vs 0.0170 (gap -0.0297, combined spread 0.0146) |
| G3 Heisenberg-4: v2 clearly better than no mitigation | **PASS** | v2 clearly better: 0.0466 vs 0.1242 (gap +0.0775, combined spread 0.0139) |
| G1 QPE-4: v2 clearly better than recipe v1 | **FAIL** | v2 clearly worse: 0.0399 vs 0.0151 (gap -0.0248, combined spread 0.0123) |
| G2 QPE-4: v2 not clearly worse than IBM level 2 | **PASS** | v2 clearly better: 0.0399 vs 0.0616 (gap +0.0217, combined spread 0.0098) |
| G3 QPE-4: v2 clearly better than no mitigation | **PASS** | v2 clearly better: 0.0399 vs 0.1601 (gap +0.1202, combined spread 0.0100) |
| G2-cost: v2 RUs <= 0.5 x IBM level 2 RUs (round total) | **PASS** | v2 0.267 RU vs 0.5 x L2 = 0.400 RU |
| secondary Heisenberg-4: v1_clip vs recipe v2 | reported (no target) | v1_clip clearly better: 0.0197 vs 0.0466 (gap +0.0270, combined spread 0.0176) |
| secondary Heisenberg-4: v2_s15 vs recipe v2 | reported (no target) | v2_s15 no clear difference: 0.0292 vs 0.0466 (gap +0.0175, combined spread 0.0224) |
| secondary QPE-4: v1_clip vs recipe v2 | reported (no target) | v1_clip clearly better: 0.0000 vs 0.0399 (gap +0.0399, combined spread 0.0098) |
| secondary QPE-4: v2_s15 vs recipe v2 | reported (no target) | v2_s15 clearly worse: 0.0618 vs 0.0399 (gap -0.0219, combined spread 0.0157) |

Two circuits and one round can show a direction, not a proof (Part F6).