# Mitigation: FakeKingston, test set, noise ×1.5 (simulator)

Run `20261123-161735_mitigation-test-noise1.5` · budget **3.0 estimated quantum seconds per circuit per method** · 10 repeats · seed selection `gates` · pre-registration SHA-256 `caceaa4bc588…`. Raw counts, circuits and the full method are in this run's folder.

**These are our own implementations, not Qiskit Runtime resilience levels.**

## Pre-registered targets (PREREGISTRATION.md A6)

Reference F = Readout+ZNE (linear). Deep circuits: Ising-4, Grover-4-3it, QFT-6, QAOA-5-p2, QAOA-6.

| Target | Result | Detail |
|---|---|---|
| T1 worst case | **PASS** | recipe worst 0.0282 vs 0.80 x F worst 0.2068 = 0.1654 |
| T2 deep circuits | **PASS** | mean over 5 deep: recipe 0.0206 vs 0.85 x F 0.0598 = 0.0508 |
| T3 no harm | **PASS** | recipe clearly worse than F on 0 circuit(s): none |
| O1 old (median -10%) | **PASS** | median change vs F -23.4% |

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
| Ising-4 | 36 | magnetization (1/4) sum <Z_j> | **0.0045 ± 0.0026** | 0.0062 ± 0.0046 | 0.0109 ± 0.0076 | 0.0120 ± 0.0075 | 0.0109 ± 0.0076 |
| Mirror-4 | 12 | P(0000) | 0.0940 ± 0.0017 | 0.0609 ± 0.0060 | 0.0095 ± 0.0076 | **0.0055 ± 0.0038** | 0.0055 ± 0.0038 |
| Grover-4-3it | 111 | P(0110), 3 iterations | 0.3129 ± 0.0052 | 0.2914 ± 0.0046 | 0.2068 ± 0.0113 | 0.0241 ± 0.0142 | 0.0241 ± 0.0142 |
| QFT-6 | 88 | input \|43> = \|101011>, <X_j> and <Y_j> on every qubit | 0.0696 ± 0.0025 | 0.0591 ± 0.0041 | 0.0294 ± 0.0070 | 0.1071 ± 0.1087 | **0.0282 ± 0.0067** |
| QAOA-5-p2 | 34 | expected cut (5-ring, p=2) | 0.1768 ± 0.0068 | 0.1075 ± 0.0084 | 0.0302 ± 0.0171 | 0.0172 ± 0.0131 | 0.0172 ± 0.0131 |
| QAOA-6 | 31 | expected cut (prism, p=1) | 0.1544 ± 0.0077 | 0.0936 ± 0.0098 | **0.0218 ± 0.0175** | 0.0229 ± 0.0128 | 0.0229 ± 0.0128 |

## Extrapolation comparison

| Circuit | 2q | ZNE (richardson) | ZNE (linear) | ZNE (exp) | ZNE (expg) | Readout+ZNE (richardson) | Readout+ZNE (linear) | Readout+ZNE (exp) | Readout+ZNE (expg) |
|---|---|---|---|---|---|---|---|---|---|
| Ising-4 | 36 | 0.0186 ± 0.0171 | 0.0115 ± 0.0101 | 0.0318 ± 0.0612 | 0.0318 ± 0.0612 | 0.0145 ± 0.0094 | 0.0109 ± 0.0076 | 0.0120 ± 0.0075 | 0.0120 ± 0.0075 |
| Mirror-4 | 12 | 0.0326 ± 0.0115 | 0.0497 ± 0.0033 | 0.0395 ± 0.0036 | 0.0395 ± 0.0036 | 0.0155 ± 0.0088 | 0.0095 ± 0.0076 | 0.0081 ± 0.0050 | **0.0055 ± 0.0038** |
| Grover-4-3it | 111 | 0.0979 ± 0.0211 | 0.2351 ± 0.0082 | 0.0547 ± 0.0159 | 0.0547 ± 0.0159 | 0.0624 ± 0.0182 | 0.2068 ± 0.0113 | **0.0241 ± 0.0142** | 0.0241 ± 0.0142 |
| QFT-6 | 88 | 0.0408 ± 0.0096 | 0.0356 ± 0.0063 | 0.0448 ± 0.0365 | 0.0448 ± 0.0365 | 0.0421 ± 0.0099 | 0.0294 ± 0.0070 | 0.1072 ± 0.1087 | 0.1071 ± 0.1087 |
| QAOA-5-p2 | 34 | 0.0822 ± 0.0199 | 0.1049 ± 0.0095 | 0.0855 ± 0.0113 | 0.0855 ± 0.0113 | 0.0307 ± 0.0248 | 0.0302 ± 0.0171 | **0.0172 ± 0.0131** | 0.0172 ± 0.0131 |
| QAOA-6 | 31 | 0.0437 ± 0.0355 | 0.0799 ± 0.0243 | 0.0626 ± 0.0264 | 0.0626 ± 0.0264 | 0.0515 ± 0.0396 | **0.0218 ± 0.0175** | 0.0229 ± 0.0128 | 0.0229 ± 0.0128 |

Guarded exponential (expg): how often the exponential result was kept vs replaced by linear (counted per observable and repeat).

| Method | Exponential kept | Fell back to linear |
|---|---|---|
| ZNE (expg) | 167 | 3 |
| Readout+ZNE (expg) | 156 | 14 |

Recipe choices (per observable and repeat): exp 136, linear 34.

## Summary

| Method | Best (circuits) | Median RMSE | Median change vs none | Worst RMSE |
|---|---|---|---|---|
| None | 1 of 6 | 0.1242 | +0% | 0.3129 |
| Readout | 0 of 6 | 0.0773 | -25% | 0.2914 |
| ZNE (richardson) | 0 of 6 | 0.0422 | -59% | 0.0979 |
| ZNE (linear) | 0 of 6 | 0.0648 | -44% | 0.2351 |
| ZNE (exp) | 0 of 6 | 0.0498 | -55% | 0.0855 |
| ZNE (expg) | 0 of 6 | 0.0498 | -55% | 0.0855 |
| Readout+ZNE (richardson) | 0 of 6 | 0.0364 | -73% | 0.0624 |
| Readout+ZNE (linear) | 1 of 6 | 0.0256 | -70% | 0.2068 |
| Readout+ZNE (exp) | 2 of 6 | 0.0200 | -88% | 0.1072 |
| Readout+ZNE (expg) | 1 of 6 | 0.0200 | -88% | 0.1071 |
| Recipe | 1 of 6 | 0.0200 | -88% | 0.0282 |

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
| Ising-4 | M | -0.010 | -0.011 ± 0.005 | -0.015 ± 0.007 | -0.008 ± 0.014 | -0.009 ± 0.015 | -0.008 ± 0.014 |
| Mirror-4 | P(0000) | +1.000 | +0.906 ± 0.002 | +0.939 ± 0.006 | +0.991 ± 0.009 | +0.995 ± 0.005 | +0.995 ± 0.005 |
| Grover-4-3it | P(0110) | +0.961 | +0.648 ± 0.005 | +0.670 ± 0.005 | +0.755 ± 0.011 | +0.944 ± 0.023 | +0.944 ± 0.023 |
| QFT-6 | X0 | -0.471 | -0.439 ± 0.012 | -0.436 ± 0.013 | -0.474 ± 0.023 | -0.483 ± 0.028 | -0.483 ± 0.028 |
| QFT-6 | X1 | -0.556 | -0.492 ± 0.012 | -0.502 ± 0.014 | -0.528 ± 0.025 | -0.536 ± 0.028 | -0.535 ± 0.029 |
| QFT-6 | X2 | -0.383 | -0.348 ± 0.012 | -0.365 ± 0.016 | -0.374 ± 0.032 | -0.378 ± 0.035 | -0.378 ± 0.035 |
| QFT-6 | X3 | -0.707 | -0.606 ± 0.010 | -0.611 ± 0.012 | -0.679 ± 0.029 | -0.710 ± 0.038 | -0.710 ± 0.038 |
| QFT-6 | X4 | -0.000 | -0.023 ± 0.015 | -0.031 ± 0.010 | -0.004 ± 0.036 | +0.080 ± 0.308 | -0.004 ± 0.036 |
| QFT-6 | X5 | -1.000 | -0.922 ± 0.007 | -0.931 ± 0.009 | -0.983 ± 0.016 | -0.991 ± 0.012 | -0.991 ± 0.012 |
| QFT-6 | Y0 | -0.882 | -0.819 ± 0.006 | -0.820 ± 0.014 | -0.872 ± 0.030 | -0.885 ± 0.034 | -0.885 ± 0.034 |
| QFT-6 | Y1 | +0.831 | +0.751 ± 0.008 | +0.774 ± 0.012 | +0.809 ± 0.025 | +0.819 ± 0.027 | +0.819 ± 0.027 |
| QFT-6 | Y2 | -0.924 | -0.834 ± 0.005 | -0.849 ± 0.009 | -0.917 ± 0.013 | -0.934 ± 0.014 | -0.934 ± 0.014 |
| QFT-6 | Y3 | +0.707 | +0.660 ± 0.009 | +0.682 ± 0.012 | +0.712 ± 0.018 | +0.718 ± 0.020 | +0.718 ± 0.020 |
| QFT-6 | Y4 | -1.000 | -0.885 ± 0.006 | -0.912 ± 0.013 | -0.973 ± 0.027 | -0.984 ± 0.020 | -0.984 ± 0.020 |
| QFT-6 | Y5 | +0.000 | -0.001 ± 0.008 | -0.003 ± 0.017 | +0.003 ± 0.032 | +0.051 ± 0.426 | +0.003 ± 0.032 |
| QAOA-5-p2 | <cut> | +4.000 | +3.823 ± 0.007 | +3.892 ± 0.008 | +3.970 ± 0.017 | +3.989 ± 0.019 | +3.989 ± 0.019 |
| QAOA-6 | <cut> | +5.922 | +5.767 ± 0.008 | +5.828 ± 0.010 | +5.906 ± 0.024 | +5.925 ± 0.027 | +5.925 ± 0.027 |

Readout-corrected and extrapolated values can leave the physical range; only expg (and the recipe, if it uses it) guards against that.
