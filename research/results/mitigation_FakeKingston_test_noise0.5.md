# Mitigation: FakeKingston, test set, noise ×0.5 (simulator)

Run `20261123-161435_mitigation-test-noise0.5` · budget **3.0 estimated quantum seconds per circuit per method** · 10 repeats · seed selection `gates` · pre-registration SHA-256 `caceaa4bc588…`. Raw counts, circuits and the full method are in this run's folder.

**These are our own implementations, not Qiskit Runtime resilience levels.**

## Pre-registered targets (PREREGISTRATION.md A6)

Reference F = Readout+ZNE (linear). Deep circuits: Ising-4, Grover-4-3it, QFT-6, QAOA-5-p2, QAOA-6.

| Target | Result | Detail |
|---|---|---|
| T1 worst case | **PASS** | recipe worst 0.0259 vs 0.80 x F worst 0.0373 = 0.0298 |
| T2 deep circuits | **PASS** | mean over 5 deep: recipe 0.0134 vs 0.85 x F 0.0187 = 0.0159 |
| T3 no harm | **PASS** | recipe clearly worse than F on 0 circuit(s): none |
| O1 old (median -10%) | **FAIL** | median change vs F +1.7% |

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
| Ising-4 | 36 | magnetization (1/4) sum <Z_j> | **0.0045 ± 0.0050** | 0.0050 ± 0.0038 | 0.0120 ± 0.0077 | 0.0100 ± 0.0053 | 0.0120 ± 0.0077 |
| Mirror-4 | 12 | P(0000) | 0.0311 ± 0.0011 | 0.0181 ± 0.0042 | 0.0036 ± 0.0026 | **0.0031 ± 0.0028** | 0.0031 ± 0.0028 |
| Grover-4-3it | 111 | P(0110), 3 iterations | 0.1213 ± 0.0035 | 0.1104 ± 0.0058 | 0.0373 ± 0.0086 | 0.0087 ± 0.0054 | 0.0087 ± 0.0054 |
| QFT-6 | 88 | input \|43> = \|101011>, <X_j> and <Y_j> on every qubit | 0.0248 ± 0.0019 | **0.0224 ± 0.0036** | 0.0251 ± 0.0085 | 0.0643 ± 0.0546 | 0.0259 ± 0.0083 |
| QAOA-5-p2 | 34 | expected cut (5-ring, p=2) | 0.0625 ± 0.0032 | 0.0362 ± 0.0055 | **0.0050 ± 0.0070** | 0.0056 ± 0.0057 | 0.0056 ± 0.0057 |
| QAOA-6 | 31 | expected cut (prism, p=1) | 0.0585 ± 0.0111 | 0.0288 ± 0.0100 | **0.0143 ± 0.0135** | 0.0147 ± 0.0123 | 0.0149 ± 0.0125 |

## Extrapolation comparison

| Circuit | 2q | ZNE (richardson) | ZNE (linear) | ZNE (exp) | ZNE (expg) | Readout+ZNE (richardson) | Readout+ZNE (linear) | Readout+ZNE (exp) | Readout+ZNE (expg) |
|---|---|---|---|---|---|---|---|---|---|
| Ising-4 | 36 | 0.0244 ± 0.0135 | 0.0082 ± 0.0052 | 0.0172 ± 0.0135 | 0.0172 ± 0.0135 | 0.0087 ± 0.0088 | 0.0120 ± 0.0077 | 0.0100 ± 0.0053 | 0.0100 ± 0.0053 |
| Mirror-4 | 12 | 0.0098 ± 0.0049 | 0.0143 ± 0.0038 | 0.0130 ± 0.0040 | 0.0130 ± 0.0040 | 0.0051 ± 0.0059 | 0.0036 ± 0.0026 | 0.0042 ± 0.0033 | **0.0031 ± 0.0028** |
| Grover-4-3it | 111 | 0.0236 ± 0.0173 | 0.0522 ± 0.0083 | 0.0179 ± 0.0099 | 0.0179 ± 0.0099 | 0.0124 ± 0.0049 | 0.0373 ± 0.0086 | **0.0087 ± 0.0054** | 0.0087 ± 0.0054 |
| QFT-6 | 88 | 0.0418 ± 0.0068 | 0.0224 ± 0.0030 | 0.1001 ± 0.1089 | 0.0710 ± 0.0790 | 0.0446 ± 0.0097 | 0.0251 ± 0.0085 | 0.0644 ± 0.0546 | 0.0643 ± 0.0546 |
| QAOA-5-p2 | 34 | 0.0332 ± 0.0189 | 0.0274 ± 0.0052 | 0.0248 ± 0.0054 | 0.0248 ± 0.0054 | 0.0169 ± 0.0088 | **0.0050 ± 0.0070** | 0.0056 ± 0.0057 | 0.0056 ± 0.0057 |
| QAOA-6 | 31 | 0.0374 ± 0.0308 | 0.0357 ± 0.0205 | 0.0343 ± 0.0204 | 0.0343 ± 0.0204 | 0.0408 ± 0.0304 | **0.0143 ± 0.0135** | 0.0147 ± 0.0123 | 0.0147 ± 0.0123 |

Guarded exponential (expg): how often the exponential result was kept vs replaced by linear (counted per observable and repeat).

| Method | Exponential kept | Fell back to linear |
|---|---|---|
| ZNE (expg) | 162 | 8 |
| Readout+ZNE (expg) | 152 | 18 |

Recipe choices (per observable and repeat): exp 116, linear 54.

## Summary

| Method | Best (circuits) | Median RMSE | Median change vs none | Worst RMSE |
|---|---|---|---|---|
| None | 1 of 6 | 0.0448 | +0% | 0.1213 |
| Readout | 1 of 6 | 0.0256 | -26% | 0.1104 |
| ZNE (richardson) | 0 of 6 | 0.0288 | -41% | 0.0418 |
| ZNE (linear) | 0 of 6 | 0.0249 | -47% | 0.0522 |
| ZNE (exp) | 0 of 6 | 0.0213 | -50% | 0.1001 |
| ZNE (expg) | 0 of 6 | 0.0213 | -50% | 0.0710 |
| Readout+ZNE (richardson) | 0 of 6 | 0.0147 | -52% | 0.0446 |
| Readout+ZNE (linear) | 2 of 6 | 0.0131 | -72% | 0.0373 |
| Readout+ZNE (exp) | 1 of 6 | 0.0094 | -81% | 0.0644 |
| Readout+ZNE (expg) | 1 of 6 | 0.0094 | -82% | 0.0643 |
| Recipe | 0 of 6 | 0.0103 | -82% | 0.0259 |

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
| Ising-4 | M | -0.010 | -0.013 ± 0.006 | -0.006 ± 0.005 | -0.006 ± 0.014 | -0.009 ± 0.012 | -0.006 ± 0.014 |
| Mirror-4 | P(0000) | +1.000 | +0.969 ± 0.001 | +0.982 ± 0.004 | +1.001 ± 0.004 | +1.002 ± 0.004 | +1.002 ± 0.004 |
| Grover-4-3it | P(0110) | +0.961 | +0.840 ± 0.004 | +0.851 ± 0.006 | +0.924 ± 0.009 | +0.960 ± 0.011 | +0.960 ± 0.011 |
| QFT-6 | X0 | -0.471 | -0.463 ± 0.010 | -0.465 ± 0.008 | -0.469 ± 0.026 | -0.470 ± 0.027 | -0.470 ± 0.027 |
| QFT-6 | X1 | -0.556 | -0.535 ± 0.010 | -0.539 ± 0.011 | -0.546 ± 0.022 | -0.547 ± 0.023 | -0.547 ± 0.023 |
| QFT-6 | X2 | -0.383 | -0.374 ± 0.016 | -0.374 ± 0.008 | -0.371 ± 0.049 | -0.373 ± 0.050 | -0.372 ± 0.051 |
| QFT-6 | X3 | -0.707 | -0.670 ± 0.012 | -0.675 ± 0.018 | -0.716 ± 0.020 | -0.722 ± 0.021 | -0.722 ± 0.022 |
| QFT-6 | X4 | -0.000 | -0.010 ± 0.009 | -0.003 ± 0.013 | +0.019 ± 0.038 | +0.055 ± 0.110 | +0.019 ± 0.038 |
| QFT-6 | X5 | -1.000 | -0.972 ± 0.002 | -0.977 ± 0.006 | -1.000 ± 0.007 | -1.000 ± 0.007 | -1.000 ± 0.007 |
| QFT-6 | Y0 | -0.882 | -0.864 ± 0.007 | -0.861 ± 0.007 | -0.875 ± 0.014 | -0.877 ± 0.015 | -0.877 ± 0.015 |
| QFT-6 | Y1 | +0.831 | +0.804 ± 0.009 | +0.810 ± 0.016 | +0.831 ± 0.016 | +0.832 ± 0.016 | +0.832 ± 0.016 |
| QFT-6 | Y2 | -0.924 | -0.893 ± 0.005 | -0.902 ± 0.008 | -0.924 ± 0.018 | -0.926 ± 0.019 | -0.926 ± 0.019 |
| QFT-6 | Y3 | +0.707 | +0.694 ± 0.009 | +0.689 ± 0.014 | +0.697 ± 0.025 | +0.698 ± 0.025 | +0.698 ± 0.025 |
| QFT-6 | Y4 | -1.000 | -0.962 ± 0.003 | -0.968 ± 0.008 | -1.000 ± 0.009 | -1.002 ± 0.008 | -1.002 ± 0.008 |
| QFT-6 | Y5 | +0.000 | -0.002 ± 0.012 | +0.007 ± 0.014 | -0.008 ± 0.037 | +0.095 ± 0.243 | -0.008 ± 0.037 |
| QAOA-5-p2 | <cut> | +4.000 | +3.938 ± 0.003 | +3.964 ± 0.005 | +3.997 ± 0.008 | +3.999 ± 0.008 | +3.999 ± 0.008 |
| QAOA-6 | <cut> | +5.922 | +5.863 ± 0.011 | +5.893 ± 0.010 | +5.913 ± 0.018 | +5.915 ± 0.019 | +5.915 ± 0.019 |

Readout-corrected and extrapolated values can leave the physical range; only expg (and the recipe, if it uses it) guards against that.
