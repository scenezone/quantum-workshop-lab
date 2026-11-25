# Recipe v2 vs v1: FakeKingston, train set, noise ×1 (simulator)

Run `20261125-120531_mitigation-v2-train-partial` · budget **3.0 estimated quantum seconds per circuit per data group** · 3 repeats · 8 twirls per scale per repeat · recipe v2 frozen: True · pre-registration SHA-256 `8b1b6812f120…`.

**Our own implementations, not Qiskit Runtime resilience levels.** The fake-backend noise model has no coherent errors, so twirling is expected to change little here (see `python twirl.py` for a coherent-noise check). The simulator also did not reproduce the hardware failure of v1 on deep circuits.

Secondary methods (v1 data + clip, v2 at 1/1.5/2 (secondary)) are reported only; no target uses them.

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
| Bell | 1 | 0.0231 ± 0.0018 | 0.0090 ± 0.0044 | 0.0089 ± 0.0044 | 0.0072 ± 0.0069 | **0.0006 ± 0.0010** | 0.0020 ± 0.0024 | 0.0074 ± 0.0045 |
| GHZ-3 | 2 | 0.0498 ± 0.0019 | 0.0023 ± 0.0031 | 0.0023 ± 0.0031 | 0.0001 ± 0.0002 | **0.0000 ± 0.0000** | 0.0000 ± 0.0000 | 0.0057 ± 0.0041 |
| QFT-3 | 18 | 0.0248 ± 0.0038 | 0.0251 ± 0.0043 | 0.0253 ± 0.0047 | 0.0247 ± 0.0046 | 0.0209 ± 0.0056 | **0.0173 ± 0.0046** | 0.0569 ± 0.0246 |

## Summary

| Method | Best (circuits) | Median RMSE | Mean RMSE (deep) | Worst RMSE |
|---|---|---|---|---|
| None | 0 of 3 | 0.0248 | 0.0248 | 0.0498 |
| F: readout+ZNE 1/3/5 linear | 0 of 3 | 0.0090 | 0.0251 | 0.0251 |
| Recipe v1 | 0 of 3 | 0.0089 | 0.0253 | 0.0253 |
| v1 data + clip | 0 of 3 | 0.0072 | 0.0247 | 0.0247 |
| v2 without twirling | 2 of 3 | 0.0006 | 0.0209 | 0.0209 |
| Recipe v2 (1/2/3) | 1 of 3 | 0.0020 | 0.0173 | 0.0173 |
| v2 at 1/1.5/2 (secondary) | 0 of 3 | 0.0074 | 0.0569 | 0.0569 |

Branches used (per observable and repeat): Recipe v1: exp 12, linear 12; v1 data + clip: linear 11, exp 8, exp+clip 4, linear+clip 1; v2 without twirling: linear 11, exp+clip 5, exp 4, linear+clip 4; Recipe v2 (1/2/3): linear 12, exp 6, exp+clip 5, linear+clip 1; v2 at 1/1.5/2 (secondary): linear 15, exp 7, exp+clip 2.

## Observable estimates (mean ± std over repeats)

| Circuit | Observable | Exact | None | F: readout+ZNE 1/3/5 linear | Recipe v1 | v1 data + clip | v2 without twirling | Recipe v2 (1/2/3) | v2 at 1/1.5/2 (secondary) |
|---|---|---|---|---|---|---|---|---|---|
| Bell | ZZ | +1.000 | +0.977 ± 0.002 | +0.994 ± 0.010 | +0.995 ± 0.010 | +0.993 ± 0.007 | +0.999 ± 0.001 | +0.998 ± 0.002 | +0.993 ± 0.004 |
| GHZ-3 | XXX | +1.000 | +0.950 ± 0.002 | +1.002 ± 0.003 | +1.002 ± 0.003 | +1.000 ± 0.000 | +1.000 ± 0.000 | +1.000 ± 0.000 | +0.994 ± 0.004 |
| QFT-3 | X0 | -0.707 | -0.682 ± 0.014 | -0.705 ± 0.025 | -0.706 ± 0.026 | -0.706 ± 0.026 | -0.731 ± 0.028 | -0.707 ± 0.015 | -0.685 ± 0.040 |
| QFT-3 | X1 | +0.000 | +0.002 ± 0.004 | -0.017 ± 0.048 | -0.017 ± 0.048 | -0.017 ± 0.048 | +0.010 ± 0.036 | -0.006 ± 0.037 | +0.043 ± 0.135 |
| QFT-3 | X2 | -1.000 | -0.975 ± 0.001 | -0.993 ± 0.007 | -0.993 ± 0.007 | -0.993 ± 0.007 | -1.000 ± 0.000 | -0.991 ± 0.010 | -0.986 ± 0.013 |
| QFT-3 | Y0 | -0.707 | -0.676 ± 0.008 | -0.701 ± 0.041 | -0.701 ± 0.043 | -0.701 ± 0.043 | -0.690 ± 0.008 | -0.698 ± 0.007 | -0.741 ± 0.042 |
| QFT-3 | Y1 | +1.000 | +0.968 ± 0.005 | +1.005 ± 0.020 | +1.005 ± 0.019 | +0.994 ± 0.010 | +0.989 ± 0.009 | +0.991 ± 0.008 | +0.997 ± 0.003 |
| QFT-3 | Y2 | +0.000 | -0.003 ± 0.022 | +0.006 ± 0.003 | +0.006 ± 0.003 | +0.006 ± 0.003 | -0.007 ± 0.013 | -0.019 ± 0.007 | -0.022 ± 0.068 |
