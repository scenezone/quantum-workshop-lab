# Mitigation: FakeKingston, test set (simulator)

Run `20261123-112303_mitigation-test` · budget **3.0 estimated quantum seconds per circuit per method** · 10 repeats · seed selection `gates` · pre-registration SHA-256 `15bb2568d7fe…`. Raw counts, circuits and the full method are in this run's folder.

**These are our own implementations, not Qiskit Runtime resilience levels.**

## Pre-registered targets (PREREGISTRATION.md A6)

Reference F = Readout+ZNE (linear). Deep circuits: Ising-4, Grover-4-3it, QFT-6, QAOA-5-p2, QAOA-6.

| Target | Result | Detail |
|---|---|---|
| T1 worst case | **PASS** | recipe worst 0.0231 vs 0.80 x F worst 0.1201 = 0.0961 |
| T2 deep circuits | **PASS** | mean over 5 deep: recipe 0.0163 vs 0.85 x F 0.0367 = 0.0312 |
| T3 no harm | **PASS** | recipe clearly worse than F on 0 circuit(s): none |
| O1 old (median -10%) | **FAIL** | median change vs F -3.7% |

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
| Ising-4 | 36 | magnetization (1/4) sum <Z_j> | **0.0045 ± 0.0040** | 0.0051 ± 0.0035 | 0.0088 ± 0.0091 | 0.0307 ± 0.0693 | 0.0088 ± 0.0091 |
| Mirror-4 | 12 | P(0000) | 0.0646 ± 0.0015 | 0.0400 ± 0.0044 | 0.0072 ± 0.0047 | **0.0048 ± 0.0027** | 0.0048 ± 0.0027 |
| Grover-4-3it | 111 | P(0110), 3 iterations | 0.2246 ± 0.0033 | 0.2028 ± 0.0057 | 0.1201 ± 0.0141 | 0.0186 ± 0.0122 | 0.0186 ± 0.0122 |
| QFT-6 | 88 | input \|43> = \|101011>, <X_j> and <Y_j> on every qubit | 0.0485 ± 0.0036 | 0.0407 ± 0.0026 | **0.0231 ± 0.0050** | 0.0261 ± 0.0109 | 0.0231 ± 0.0058 |
| QAOA-5-p2 | 34 | expected cut (5-ring, p=2) | 0.1185 ± 0.0048 | 0.0692 ± 0.0060 | **0.0140 ± 0.0121** | 0.0146 ± 0.0091 | 0.0146 ± 0.0091 |
| QAOA-6 | 31 | expected cut (prism, p=1) | 0.1045 ± 0.0075 | 0.0584 ± 0.0098 | 0.0176 ± 0.0150 | 0.0163 ± 0.0152 | 0.0163 ± 0.0152 |

## Extrapolation comparison

| Circuit | 2q | ZNE (richardson) | ZNE (linear) | ZNE (exp) | ZNE (expg) | Readout+ZNE (richardson) | Readout+ZNE (linear) | Readout+ZNE (exp) | Readout+ZNE (expg) |
|---|---|---|---|---|---|---|---|---|---|
| Ising-4 | 36 | 0.0152 ± 0.0074 | 0.0108 ± 0.0116 | 0.0181 ± 0.0246 | 0.0181 ± 0.0246 | 0.0273 ± 0.0197 | 0.0088 ± 0.0091 | 0.1729 ± 0.4473 | 0.0307 ± 0.0693 |
| Mirror-4 | 12 | 0.0240 ± 0.0109 | 0.0275 ± 0.0047 | 0.0223 ± 0.0051 | 0.0223 ± 0.0051 | 0.0097 ± 0.0063 | 0.0072 ± 0.0047 | 0.0049 ± 0.0031 | **0.0048 ± 0.0027** |
| Grover-4-3it | 111 | 0.0551 ± 0.0161 | 0.1336 ± 0.0109 | 0.0242 ± 0.0168 | 0.0242 ± 0.0168 | 0.0290 ± 0.0120 | 0.1201 ± 0.0141 | **0.0186 ± 0.0122** | 0.0186 ± 0.0122 |
| QFT-6 | 88 | 0.0370 ± 0.0075 | 0.0274 ± 0.0051 | 0.0760 ± 0.0852 | 0.0760 ± 0.0852 | 0.0447 ± 0.0077 | **0.0231 ± 0.0050** | 0.0576 ± 0.0998 | 0.0261 ± 0.0109 |
| QAOA-5-p2 | 34 | 0.0423 ± 0.0186 | 0.0613 ± 0.0077 | 0.0517 ± 0.0083 | 0.0517 ± 0.0083 | 0.0211 ± 0.0183 | **0.0140 ± 0.0121** | 0.0146 ± 0.0091 | 0.0146 ± 0.0091 |
| QAOA-6 | 31 | 0.0441 ± 0.0349 | 0.0513 ± 0.0193 | 0.0427 ± 0.0212 | 0.0427 ± 0.0212 | 0.0171 ± 0.0186 | 0.0176 ± 0.0150 | **0.0163 ± 0.0152** | 0.0163 ± 0.0152 |

Guarded exponential (expg): how often the exponential result was kept vs replaced by linear (counted per observable and repeat).

| Method | Exponential kept | Fell back to linear |
|---|---|---|
| ZNE (expg) | 167 | 3 |
| Readout+ZNE (expg) | 156 | 14 |

Recipe choices (per observable and repeat): exp 130, linear 40.

## Summary

| Method | Best (circuits) | Median RMSE | Median change vs none | Worst RMSE |
|---|---|---|---|---|
| None | 1 of 6 | 0.0845 | +0% | 0.2246 |
| Readout | 0 of 6 | 0.0496 | -27% | 0.2028 |
| ZNE (richardson) | 0 of 6 | 0.0396 | -60% | 0.0551 |
| ZNE (linear) | 0 of 6 | 0.0394 | -46% | 0.1336 |
| ZNE (exp) | 0 of 6 | 0.0335 | -58% | 0.0760 |
| ZNE (expg) | 0 of 6 | 0.0335 | -58% | 0.0760 |
| Readout+ZNE (richardson) | 0 of 6 | 0.0242 | -83% | 0.0447 |
| Readout+ZNE (linear) | 2 of 6 | 0.0158 | -68% | 0.1201 |
| Readout+ZNE (exp) | 2 of 6 | 0.0175 | -86% | 0.1729 |
| Readout+ZNE (expg) | 1 of 6 | 0.0175 | -86% | 0.0307 |
| Recipe | 0 of 6 | 0.0155 | -86% | 0.0231 |

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
| Ising-4 | M | -0.010 | -0.010 ± 0.006 | -0.014 ± 0.005 | -0.009 ± 0.013 | +0.007 ± 0.074 | -0.009 ± 0.013 |
| Mirror-4 | P(0000) | +1.000 | +0.935 ± 0.001 | +0.960 ± 0.004 | +0.993 ± 0.005 | +0.996 ± 0.003 | +0.996 ± 0.003 |
| Grover-4-3it | P(0110) | +0.961 | +0.737 ± 0.003 | +0.759 ± 0.006 | +0.841 ± 0.014 | +0.949 ± 0.019 | +0.949 ± 0.019 |
| QFT-6 | X0 | -0.471 | -0.440 ± 0.012 | -0.444 ± 0.015 | -0.468 ± 0.022 | -0.473 ± 0.024 | -0.472 ± 0.024 |
| QFT-6 | X1 | -0.556 | -0.518 ± 0.007 | -0.527 ± 0.014 | -0.545 ± 0.016 | -0.549 ± 0.018 | -0.549 ± 0.018 |
| QFT-6 | X2 | -0.383 | -0.364 ± 0.016 | -0.368 ± 0.016 | -0.387 ± 0.027 | -0.390 ± 0.029 | -0.390 ± 0.029 |
| QFT-6 | X3 | -0.707 | -0.638 ± 0.012 | -0.646 ± 0.009 | -0.695 ± 0.023 | -0.711 ± 0.026 | -0.711 ± 0.026 |
| QFT-6 | X4 | -0.000 | -0.020 ± 0.012 | -0.025 ± 0.012 | -0.005 ± 0.045 | -0.009 ± 0.052 | -0.005 ± 0.045 |
| QFT-6 | X5 | -1.000 | -0.949 ± 0.005 | -0.954 ± 0.010 | -0.994 ± 0.009 | -0.998 ± 0.007 | -0.998 ± 0.007 |
| QFT-6 | Y0 | -0.882 | -0.838 ± 0.007 | -0.838 ± 0.008 | -0.888 ± 0.017 | -0.895 ± 0.019 | -0.895 ± 0.019 |
| QFT-6 | Y1 | +0.831 | +0.779 ± 0.009 | +0.794 ± 0.009 | +0.827 ± 0.020 | +0.833 ± 0.021 | +0.833 ± 0.021 |
| QFT-6 | Y2 | -0.924 | -0.858 ± 0.006 | -0.882 ± 0.010 | -0.912 ± 0.016 | -0.919 ± 0.017 | -0.919 ± 0.017 |
| QFT-6 | Y3 | +0.707 | +0.665 ± 0.010 | +0.684 ± 0.019 | +0.697 ± 0.024 | +0.699 ± 0.025 | +0.699 ± 0.025 |
| QFT-6 | Y4 | -1.000 | -0.923 ± 0.008 | -0.933 ± 0.007 | -0.986 ± 0.014 | -0.992 ± 0.011 | -0.992 ± 0.011 |
| QFT-6 | Y5 | +0.000 | -0.003 ± 0.009 | -0.003 ± 0.013 | +0.007 ± 0.025 | +0.018 ± 0.050 | +0.007 ± 0.025 |
| QAOA-5-p2 | <cut> | +4.000 | +3.882 ± 0.005 | +3.931 ± 0.006 | +3.991 ± 0.017 | +4.001 ± 0.018 | +4.001 ± 0.018 |
| QAOA-6 | <cut> | +5.922 | +5.817 ± 0.007 | +5.863 ± 0.010 | +5.912 ± 0.022 | +5.920 ± 0.023 | +5.920 ± 0.023 |

Readout-corrected and extrapolated values can leave the physical range; only expg (and the recipe, if it uses it) guards against that.
