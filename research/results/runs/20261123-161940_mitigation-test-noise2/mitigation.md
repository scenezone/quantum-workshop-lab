# Mitigation: FakeKingston, test set, noise ×2 (simulator)

Run `20261123-161940_mitigation-test-noise2` · budget **3.0 estimated quantum seconds per circuit per method** · 10 repeats · seed selection `gates` · pre-registration SHA-256 `caceaa4bc588…`. Raw counts, circuits and the full method are in this run's folder.

**These are our own implementations, not Qiskit Runtime resilience levels.**

## Pre-registered targets (PREREGISTRATION.md A6)

Reference F = Readout+ZNE (linear). Deep circuits: Ising-4, Grover-4-3it, QFT-6, QAOA-5-p2, QAOA-6.

| Target | Result | Detail |
|---|---|---|
| T1 worst case | **PASS** | recipe worst 0.0325 vs 0.80 x F worst 0.2863 = 0.2291 |
| T2 deep circuits | **PASS** | mean over 5 deep: recipe 0.0256 vs 0.85 x F 0.0817 = 0.0695 |
| T3 no harm | **PASS** | recipe clearly worse than F on 0 circuit(s): none |
| O1 old (median -10%) | **PASS** | median change vs F -27.6% |

## Method

- Our own implementations on Qiskit Aer with the fake backend's noise model; NOT Qiskit Runtime resilience levels (those have no effect on fake backends).
- Compilation: optimization level 2, best of 20 transpiler seeds under the chosen selection strategy (compile-time information only, never measured error).
- Budget: every method gets the same estimated quantum seconds per circuit, including calibration and all ZNE scale factors. Estimated QPU time = sum of shots x (circuit duration from backend gate durations + default repetition delay). Shots per circuit are derived from the budget.
- readout: per-qubit (tensored) confusion matrices from all-0 and all-1 calibration circuits on the circuit's physical qubits (20% of the method's shots). Not clipped.
- zne: native unitary folding of the transpiled circuit (G -> G (G^-1 G)^k, no re-optimization) at scale factors [1, 3, 5]; two-qubit count verified to scale exactly. Equal shots per scale factor. Extrapolation with mitiq 1.1.0: Richardson, linear least squares, exponential with a known asymptote (the observable's value on the fully mixed state), or guarded exponential (expg): exponential, falling back to linear when the result is outside the observable's physical range.
- readout_zne: calibration as in readout; every folded circuit's distribution is readout-corrected, then extrapolated as in zne.
- Repeats: every distinct circuit is simulated once with all shots it needs (memory=True); the shot record is split into disjoint chunks, one per repeat and method, in a fixed order.
- Metric: RMSE of fixed observables vs exact values from the noise-free statevector, per repeat; mean +- std over repeats.

## Main methods

RMSE vs exact, mean ± std over repeats; lower is better. Bold = best of all methods for that circuit.

| Circuit | 2q gates | Observable | None | Readout | Readout+ZNE (linear) | Readout+ZNE (expg) | Recipe |
|---|---|---|---|---|---|---|---|
| Ising-4 | 36 | magnetization (1/4) sum <Z_j> | **0.0034 ± 0.0020** | 0.0074 ± 0.0059 | 0.0122 ± 0.0080 | 0.0147 ± 0.0112 | 0.0122 ± 0.0080 |
| Mirror-4 | 12 | P(0000) | 0.1223 ± 0.0033 | 0.0814 ± 0.0046 | 0.0202 ± 0.0083 | 0.0089 ± 0.0061 | 0.0089 ± 0.0061 |
| Grover-4-3it | 111 | P(0110), 3 iterations | 0.3913 ± 0.0049 | 0.3655 ± 0.0092 | 0.2863 ± 0.0139 | 0.0264 ± 0.0220 | 0.0264 ± 0.0220 |
| QFT-6 | 88 | input \|43> = \|101011>, <X_j> and <Y_j> on every qubit | 0.0907 ± 0.0019 | 0.0785 ± 0.0029 | 0.0339 ± 0.0097 | 0.0630 ± 0.0560 | **0.0302 ± 0.0096** |
| QAOA-5-p2 | 34 | expected cut (5-ring, p=2) | 0.2306 ± 0.0050 | 0.1348 ± 0.0121 | 0.0476 ± 0.0240 | 0.0266 ± 0.0192 | 0.0266 ± 0.0192 |
| QAOA-6 | 31 | expected cut (prism, p=1) | 0.1966 ± 0.0087 | 0.1355 ± 0.0141 | **0.0286 ± 0.0278** | 0.0325 ± 0.0222 | 0.0325 ± 0.0222 |

## Extrapolation comparison

| Circuit | 2q | ZNE (richardson) | ZNE (linear) | ZNE (exp) | ZNE (expg) | Readout+ZNE (richardson) | Readout+ZNE (linear) | Readout+ZNE (exp) | Readout+ZNE (expg) |
|---|---|---|---|---|---|---|---|---|---|
| Ising-4 | 36 | 0.0127 ± 0.0064 | 0.0088 ± 0.0086 | 0.0219 ± 0.0370 | 0.0219 ± 0.0370 | 0.0167 ± 0.0134 | 0.0122 ± 0.0080 | 0.0147 ± 0.0112 | 0.0147 ± 0.0112 |
| Mirror-4 | 12 | 0.0455 ± 0.0142 | 0.0668 ± 0.0075 | 0.0493 ± 0.0088 | 0.0493 ± 0.0088 | 0.0134 ± 0.0093 | 0.0202 ± 0.0083 | **0.0068 ± 0.0051** | 0.0089 ± 0.0061 |
| Grover-4-3it | 111 | 0.1483 ± 0.0179 | 0.3144 ± 0.0083 | 0.0522 ± 0.0275 | 0.0522 ± 0.0275 | 0.1119 ± 0.0232 | 0.2863 ± 0.0139 | **0.0264 ± 0.0220** | 0.0264 ± 0.0220 |
| QFT-6 | 88 | 0.0430 ± 0.0112 | 0.0478 ± 0.0077 | 0.0424 ± 0.0208 | 0.0425 ± 0.0208 | 0.0515 ± 0.0137 | 0.0339 ± 0.0097 | 0.0895 ± 0.0899 | 0.0630 ± 0.0560 |
| QAOA-5-p2 | 34 | 0.1147 ± 0.0215 | 0.1319 ± 0.0155 | 0.0969 ± 0.0192 | 0.0969 ± 0.0192 | **0.0231 ± 0.0156** | 0.0476 ± 0.0240 | 0.0266 ± 0.0192 | 0.0266 ± 0.0192 |
| QAOA-6 | 31 | 0.0892 ± 0.0486 | 0.1176 ± 0.0152 | 0.0883 ± 0.0168 | 0.0883 ± 0.0168 | 0.0569 ± 0.0416 | **0.0286 ± 0.0278** | 0.0325 ± 0.0222 | 0.0325 ± 0.0222 |

Guarded exponential (expg): how often the exponential result was kept vs replaced by linear (counted per observable and repeat).

| Method | Exponential kept | Fell back to linear |
|---|---|---|
| ZNE (expg) | 168 | 2 |
| Readout+ZNE (expg) | 151 | 19 |

Recipe choices (per observable and repeat): exp 137, linear 33.

## Summary

| Method | Best (circuits) | Median RMSE | Median change vs none | Worst RMSE |
|---|---|---|---|---|
| None | 1 of 6 | 0.1594 | +0% | 0.3913 |
| Readout | 0 of 6 | 0.1081 | -22% | 0.3655 |
| ZNE (richardson) | 0 of 6 | 0.0674 | -54% | 0.1483 |
| ZNE (linear) | 0 of 6 | 0.0922 | -42% | 0.3144 |
| ZNE (exp) | 0 of 6 | 0.0507 | -57% | 0.0969 |
| ZNE (expg) | 0 of 6 | 0.0507 | -57% | 0.0969 |
| Readout+ZNE (richardson) | 1 of 6 | 0.0373 | -71% | 0.1119 |
| Readout+ZNE (linear) | 1 of 6 | 0.0313 | -71% | 0.2863 |
| Readout+ZNE (exp) | 2 of 6 | 0.0265 | -86% | 0.0895 |
| Readout+ZNE (expg) | 0 of 6 | 0.0265 | -86% | 0.0630 |
| Recipe | 1 of 6 | 0.0265 | -86% | 0.0325 |

## Budget

Estimated quantum seconds per method per circuit (target 3.0 s; rep delay 250 µs per shot) and the shots that buys.

| Circuit | none shots / est. s | readout shots / est. s | zne shots / est. s | readout_zne shots / est. s |
|---|---|---|---|---|
| Ising-4 | 11742 / 3.00 | 11771 / 3.00 | 11454 / 3.00 | 11537 / 3.00 |
| Mirror-4 | 11841 / 3.00 | 11851 / 3.00 | 11742 / 3.00 | 11771 / 3.00 |
| Grover-4-3it | 11267 / 3.00 | 11385 / 3.00 | 10197 / 3.00 | 10495 / 3.00 |
| QFT-6 | 11710 / 3.00 | 11744 / 3.00 | 11364 / 3.00 | 11466 / 3.00 |
| QAOA-5-p2 | 11755 / 3.00 | 11781 / 3.00 | 11493 / 3.00 | 11569 / 3.00 |
| QAOA-6 | 11803 / 3.00 | 11820 / 3.00 | 11628 / 3.00 | 11678 / 3.00 |

## Observable estimates (mean ± std over repeats)

| Circuit | Observable | Exact | None | Readout | Readout+ZNE (linear) | Readout+ZNE (expg) | Recipe |
|---|---|---|---|---|---|---|---|
| Ising-4 | M | -0.010 | -0.012 ± 0.004 | -0.013 ± 0.009 | -0.010 ± 0.015 | -0.010 ± 0.019 | -0.010 ± 0.015 |
| Mirror-4 | P(0000) | +1.000 | +0.878 ± 0.003 | +0.919 ± 0.005 | +0.980 ± 0.008 | +0.991 ± 0.006 | +0.991 ± 0.006 |
| Grover-4-3it | P(0110) | +0.961 | +0.570 ± 0.005 | +0.596 ± 0.009 | +0.675 ± 0.014 | +0.942 ± 0.029 | +0.942 ± 0.029 |
| QFT-6 | X0 | -0.471 | -0.421 ± 0.010 | -0.416 ± 0.012 | -0.458 ± 0.024 | -0.471 ± 0.027 | -0.468 ± 0.027 |
| QFT-6 | X1 | -0.556 | -0.472 ± 0.010 | -0.495 ± 0.022 | -0.536 ± 0.031 | -0.556 ± 0.037 | -0.556 ± 0.037 |
| QFT-6 | X2 | -0.383 | -0.345 ± 0.011 | -0.359 ± 0.015 | -0.392 ± 0.021 | -0.401 ± 0.026 | -0.400 ± 0.026 |
| QFT-6 | X3 | -0.707 | -0.570 ± 0.011 | -0.580 ± 0.012 | -0.649 ± 0.032 | -0.706 ± 0.050 | -0.706 ± 0.050 |
| QFT-6 | X4 | -0.000 | -0.026 ± 0.013 | -0.039 ± 0.011 | -0.034 ± 0.028 | -0.042 ± 0.025 | -0.034 ± 0.028 |
| QFT-6 | X5 | -1.000 | -0.894 ± 0.006 | -0.914 ± 0.005 | -0.986 ± 0.022 | -0.991 ± 0.017 | -0.991 ± 0.017 |
| QFT-6 | Y0 | -0.882 | -0.795 ± 0.009 | -0.798 ± 0.008 | -0.873 ± 0.015 | -0.897 ± 0.018 | -0.897 ± 0.018 |
| QFT-6 | Y1 | +0.831 | +0.734 ± 0.004 | +0.761 ± 0.017 | +0.822 ± 0.023 | +0.842 ± 0.028 | +0.842 ± 0.028 |
| QFT-6 | Y2 | -0.924 | -0.809 ± 0.004 | -0.826 ± 0.011 | -0.892 ± 0.019 | -0.918 ± 0.023 | -0.918 ± 0.023 |
| QFT-6 | Y3 | +0.707 | +0.649 ± 0.008 | +0.660 ± 0.016 | +0.706 ± 0.034 | +0.714 ± 0.036 | +0.714 ± 0.036 |
| QFT-6 | Y4 | -1.000 | -0.850 ± 0.006 | -0.875 ± 0.010 | -0.968 ± 0.027 | -0.979 ± 0.019 | -0.979 ± 0.019 |
| QFT-6 | Y5 | +0.000 | -0.007 ± 0.014 | +0.002 ± 0.018 | -0.005 ± 0.030 | -0.035 ± 0.277 | -0.005 ± 0.030 |
| QAOA-5-p2 | <cut> | +4.000 | +3.769 ± 0.005 | +3.865 ± 0.012 | +3.954 ± 0.026 | +3.986 ± 0.031 | +3.986 ± 0.031 |
| QAOA-6 | <cut> | +5.922 | +5.725 ± 0.009 | +5.786 ± 0.014 | +5.899 ± 0.034 | +5.930 ± 0.040 | +5.930 ± 0.040 |

Readout-corrected and extrapolated values can leave the physical range; only expg (and the recipe, if it uses it) guards against that.
