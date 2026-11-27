# Recipe v2 vs v1: FakeKingston, test set, noise ×1 (simulator)

Run `20261125-124533_mitigation-v2-test` · budget **3.0 estimated quantum seconds per circuit per data group** · 10 repeats · 8 twirls per scale per repeat · recipe v2 frozen: True · pre-registration SHA-256 `ffe5e2637af7…`.

**Our own implementations, not Qiskit Runtime resilience levels.** The fake-backend noise model has no coherent errors, so twirling is expected to change little here (see `python twirl.py` for a coherent-noise check). The simulator also did not reproduce the hardware failure of v1 on deep circuits.

Secondary methods (v1 data + clip, v2 at 1/1.5/2 (secondary)) are reported only; no target uses them.

## Pre-registered simulator targets (PREREGISTRATION.md Part F)

| Target | Result | Detail |
|---|---|---|
| S1 Heisenberg-4: v2 clearly better than no mitigation (simulator) | **PASS** | v2 0.0143 vs none 0.0667 (gap +0.0524, combined spread 0.0083) |
| S1 QPE-4: v2 clearly better than no mitigation (simulator) | **PASS** | v2 0.0086 vs none 0.0827 (gap +0.0740, combined spread 0.0086) |
| E1 Heisenberg-4: expectation, v2 not better than v1 in the simulator | **reported (no target)** | v2 0.0143 vs v1 0.0108 (ratio 1.32) |
| E1 QPE-4: expectation, v2 not better than v1 in the simulator | **reported (no target)** | v2 0.0086 vs v1 0.0047 (ratio 1.84) |

## Method

- Our own implementations on Qiskit Aer with the fake backend's noise model; NOT Qiskit Runtime resilience levels.
- Compilation: level 2, best of 20 seeds (fewest 2q gates, then depth), identical to mitigation.py.
- Budget: every data group gets the same estimated quantum seconds per circuit (sum of shots x (duration + rep delay)), including 20% calibration shots for readout groups.
- v1 group: all-gate native folding at 1/3/5 (folding.py). v2 groups: two-qubit-only folding at nominal 1/2/3 (secondary: 1/1.5/2) with twirl.fold_2q_series; actual scales used in fits. recipe_v2 and the secondary: every CZ Pauli-twirled, 8 independent instances per scale per repeat, counts pooled over instances. v2 without twirling: the same folds as recipe_v2, untwirled.
- Readout correction (tensored, per-qubit) of every scale before extrapolation; extrapolation with mitiq 1.1.0 (linear; exponential with known asymptote).
- Metric: RMSE vs exact noise-free value per repeat; mean +- std over repeats.

## RMSE vs exact (mean ± std over repeats; bold = best)

| Circuit | 2q | None | F: readout+ZNE 1/3/5 linear | Recipe v1 | v1 data + clip | v2 without twirling | Recipe v2 (1/2/3) | v2 at 1/1.5/2 (secondary) |
|---|---|---|---|---|---|---|---|---|
| Heisenberg-4 | 44 | 0.0667 ± 0.0039 | 0.0166 ± 0.0103 | **0.0108 ± 0.0051** | 0.0108 ± 0.0051 | 0.0272 ± 0.0171 | 0.0143 ± 0.0073 | 0.0232 ± 0.0163 |
| QPE-4 | 26 | 0.0827 ± 0.0035 | 0.0086 ± 0.0058 | 0.0047 ± 0.0036 | **0.0017 ± 0.0024** | 0.0094 ± 0.0057 | 0.0086 ± 0.0079 | 0.0111 ± 0.0089 |

## Summary

| Method | Best (circuits) | Median RMSE | Mean RMSE (deep) | Worst RMSE |
|---|---|---|---|---|
| None | 0 of 2 | 0.0747 | 0.0747 | 0.0827 |
| F: readout+ZNE 1/3/5 linear | 0 of 2 | 0.0126 | 0.0126 | 0.0166 |
| Recipe v1 | 1 of 2 | 0.0078 | 0.0078 | 0.0108 |
| v1 data + clip | 1 of 2 | 0.0062 | 0.0062 | 0.0108 |
| v2 without twirling | 0 of 2 | 0.0183 | 0.0183 | 0.0272 |
| Recipe v2 (1/2/3) | 0 of 2 | 0.0114 | 0.0114 | 0.0143 |
| v2 at 1/1.5/2 (secondary) | 0 of 2 | 0.0172 | 0.0172 | 0.0232 |

Branches used (per observable and repeat): Recipe v1: exp 20; v1 data + clip: exp 14, exp+clip 6; v2 without twirling: exp 17, linear 2, exp+clip 1; Recipe v2 (1/2/3): exp 17, exp+clip 3; v2 at 1/1.5/2 (secondary): exp 15, linear 3, exp+clip 2.

## Observable estimates (mean ± std over repeats)

| Circuit | Observable | Exact | None | F: readout+ZNE 1/3/5 linear | Recipe v1 | v1 data + clip | v2 without twirling | Recipe v2 (1/2/3) | v2 at 1/1.5/2 (secondary) |
|---|---|---|---|---|---|---|---|---|---|
| Heisenberg-4 | M_stag | -0.646 | -0.580 ± 0.004 | -0.630 ± 0.010 | -0.641 ± 0.011 | -0.641 ± 0.011 | -0.619 ± 0.017 | -0.639 ± 0.015 | -0.632 ± 0.025 |
| QPE-4 | P(1011) | +1.000 | +0.917 ± 0.004 | +0.992 ± 0.006 | +0.995 ± 0.004 | +0.998 ± 0.002 | +0.991 ± 0.006 | +0.991 ± 0.008 | +0.989 ± 0.009 |
