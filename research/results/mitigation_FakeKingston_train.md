# Mitigation: FakeKingston, train set (simulator)

Run `20261123-111818_mitigation-train` · budget **3.0 estimated quantum seconds per circuit per method** · 10 repeats · seed selection `gates` · pre-registration SHA-256 `042725112296…`. Raw counts, circuits and the full method are in this run's folder.

**These are our own implementations, not Qiskit Runtime resilience levels.**

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

| Circuit | 2q gates | Observable | None | Readout | Readout+ZNE (linear) | Readout+ZNE (expg) |
|---|---|---|---|---|---|---|
| Bell | 1 | <ZZ> | 0.0231 ± 0.0024 | 0.0049 ± 0.0031 | 0.0044 ± 0.0025 | **0.0044 ± 0.0025** |
| GHZ-3 | 2 | X-parity <X^3> | 0.0486 ± 0.0018 | 0.0062 ± 0.0048 | 0.0055 ± 0.0054 | **0.0055 ± 0.0054** |
| GHZ-5 | 4 | X-parity <X^5> | 0.0719 ± 0.0046 | 0.0135 ± 0.0063 | 0.0107 ± 0.0090 | 0.0104 ± 0.0091 |
| GHZ-7 | 6 | X-parity <X^7> | 0.1099 ± 0.0035 | 0.0204 ± 0.0077 | 0.0057 ± 0.0042 | **0.0052 ± 0.0040** |
| Grover-2 | 2 | P(11), 1 iteration(s) | 0.0152 ± 0.0014 | 0.0067 ± 0.0036 | 0.0036 ± 0.0034 | **0.0036 ± 0.0035** |
| Grover-3 | 37 | P(101), 2 iteration(s) | 0.0915 ± 0.0034 | 0.0733 ± 0.0057 | 0.0203 ± 0.0101 | 0.0084 ± 0.0079 |
| Grover-4 | 73 | P(1011), 2 iteration(s) | 0.1563 ± 0.0040 | 0.1359 ± 0.0047 | 0.0593 ± 0.0110 | 0.0109 ± 0.0093 |
| QFT-3 | 18 | input \|5> = \|101>, <X_j> and <Y_j> on every qubit | 0.0252 ± 0.0023 | **0.0169 ± 0.0026** | 0.0226 ± 0.0078 | 0.0609 ± 0.0936 |
| QFT-4 | 34 | input \|11> = \|1011>, <X_j> and <Y_j> on every qubit | 0.0341 ± 0.0020 | 0.0259 ± 0.0047 | **0.0214 ± 0.0053** | 0.0484 ± 0.0562 |
| QFT-5 | 56 | input \|21> = \|10101>, <X_j> and <Y_j> on every qubit | 0.0381 ± 0.0032 | 0.0280 ± 0.0026 | 0.0245 ± 0.0051 | 0.0310 ± 0.0132 |
| BV-4 | 3 | P(1011) | 0.0289 ± 0.0014 | 0.0069 ± 0.0039 | 0.0037 ± 0.0024 | **0.0037 ± 0.0024** |
| QAOA-3 | 7 | expected cut (triangle, p=1) | 0.0174 ± 0.0019 | 0.0072 ± 0.0038 | **0.0041 ± 0.0030** | 0.0042 ± 0.0031 |
| QAOA-4 | 11 | expected cut (4-ring, p=1) | 0.0492 ± 0.0106 | **0.0192 ± 0.0121** | 0.0260 ± 0.0161 | 0.0266 ± 0.0169 |
| QAOA-4-p2 | 25 | expected cut (4-ring, p=2) | 0.1716 ± 0.0043 | 0.1241 ± 0.0086 | 0.0324 ± 0.0155 | 0.0180 ± 0.0110 |

## Extrapolation comparison

| Circuit | 2q | ZNE (richardson) | ZNE (linear) | ZNE (exp) | ZNE (expg) | Readout+ZNE (richardson) | Readout+ZNE (linear) | Readout+ZNE (exp) | Readout+ZNE (expg) |
|---|---|---|---|---|---|---|---|---|---|
| Bell | 1 | 0.0183 ± 0.0070 | 0.0184 ± 0.0059 | 0.0183 ± 0.0059 | 0.0183 ± 0.0059 | 0.0087 ± 0.0073 | 0.0044 ± 0.0025 | 0.0045 ± 0.0026 | **0.0044 ± 0.0025** |
| GHZ-3 | 2 | 0.0470 ± 0.0139 | 0.0460 ± 0.0063 | 0.0459 ± 0.0064 | 0.0459 ± 0.0064 | 0.0153 ± 0.0099 | 0.0055 ± 0.0054 | 0.0055 ± 0.0053 | **0.0055 ± 0.0054** |
| GHZ-5 | 4 | 0.0520 ± 0.0145 | 0.0587 ± 0.0086 | 0.0582 ± 0.0088 | 0.0582 ± 0.0088 | **0.0096 ± 0.0079** | 0.0107 ± 0.0090 | 0.0107 ± 0.0092 | 0.0104 ± 0.0091 |
| GHZ-7 | 6 | 0.0852 ± 0.0164 | 0.0869 ± 0.0082 | 0.0845 ± 0.0087 | 0.0845 ± 0.0087 | 0.0283 ± 0.0131 | 0.0057 ± 0.0042 | 0.0070 ± 0.0048 | **0.0052 ± 0.0040** |
| Grover-2 | 2 | 0.0109 ± 0.0051 | 0.0089 ± 0.0039 | 0.0088 ± 0.0040 | 0.0088 ± 0.0040 | 0.0069 ± 0.0044 | 0.0036 ± 0.0034 | 0.0036 ± 0.0035 | **0.0036 ± 0.0035** |
| Grover-3 | 37 | 0.0225 ± 0.0120 | 0.0409 ± 0.0083 | 0.0232 ± 0.0097 | 0.0232 ± 0.0097 | 0.0174 ± 0.0092 | 0.0203 ± 0.0101 | **0.0084 ± 0.0079** | 0.0084 ± 0.0079 |
| Grover-4 | 73 | 0.0273 ± 0.0170 | 0.0780 ± 0.0106 | 0.0225 ± 0.0114 | 0.0225 ± 0.0114 | 0.0228 ± 0.0176 | 0.0593 ± 0.0110 | **0.0109 ± 0.0093** | 0.0109 ± 0.0093 |
| QFT-3 | 18 | 0.0413 ± 0.0149 | 0.0224 ± 0.0039 | 0.1570 ± 0.1784 | 0.1198 ± 0.1008 | 0.0380 ± 0.0132 | 0.0226 ± 0.0078 | 0.0610 ± 0.0935 | 0.0609 ± 0.0936 |
| QFT-4 | 34 | 0.0403 ± 0.0158 | 0.0221 ± 0.0072 | 0.1689 ± 0.1706 | 0.0879 ± 0.1003 | 0.0421 ± 0.0141 | **0.0214 ± 0.0053** | 0.0963 ± 0.1540 | 0.0484 ± 0.0562 |
| QFT-5 | 56 | 0.0401 ± 0.0098 | **0.0238 ± 0.0061** | 0.0264 ± 0.0089 | 0.0264 ± 0.0089 | 0.0391 ± 0.0133 | 0.0245 ± 0.0051 | 0.0310 ± 0.0132 | 0.0310 ± 0.0132 |
| BV-4 | 3 | 0.0236 ± 0.0089 | 0.0222 ± 0.0033 | 0.0220 ± 0.0034 | 0.0220 ± 0.0034 | 0.0048 ± 0.0058 | 0.0037 ± 0.0024 | 0.0037 ± 0.0025 | **0.0037 ± 0.0024** |
| QAOA-3 | 7 | 0.0098 ± 0.0074 | 0.0105 ± 0.0050 | 0.0101 ± 0.0052 | 0.0101 ± 0.0052 | 0.0089 ± 0.0071 | **0.0041 ± 0.0030** | 0.0042 ± 0.0031 | 0.0042 ± 0.0031 |
| QAOA-4 | 11 | 0.0211 ± 0.0157 | 0.0300 ± 0.0158 | 0.0286 ± 0.0162 | 0.0286 ± 0.0162 | 0.0317 ± 0.0247 | 0.0260 ± 0.0161 | 0.0266 ± 0.0169 | 0.0266 ± 0.0169 |
| QAOA-4-p2 | 25 | 0.0638 ± 0.0237 | 0.0764 ± 0.0164 | 0.0558 ± 0.0182 | 0.0558 ± 0.0182 | **0.0141 ± 0.0077** | 0.0324 ± 0.0155 | 0.0164 ± 0.0120 | 0.0180 ± 0.0110 |

Guarded exponential (expg): how often the exponential result was kept vs replaced by linear (counted per observable and repeat).

| Method | Exponential kept | Fell back to linear |
|---|---|---|
| ZNE (expg) | 336 | 14 |
| Readout+ZNE (expg) | 287 | 63 |

## Summary

| Method | Best (circuits) | Median RMSE | Median change vs none | Worst RMSE |
|---|---|---|---|---|
| None | 0 of 14 | 0.0434 | +0% | 0.1716 |
| Readout | 2 of 14 | 0.0181 | -57% | 0.1359 |
| ZNE (richardson) | 0 of 14 | 0.0337 | -25% | 0.0852 |
| ZNE (linear) | 1 of 14 | 0.0269 | -36% | 0.0869 |
| ZNE (exp) | 0 of 14 | 0.0275 | -27% | 0.1689 |
| ZNE (expg) | 0 of 14 | 0.0275 | -27% | 0.1198 |
| Readout+ZNE (richardson) | 2 of 14 | 0.0164 | -65% | 0.0421 |
| Readout+ZNE (linear) | 2 of 14 | 0.0155 | -77% | 0.0593 |
| Readout+ZNE (exp) | 2 of 14 | 0.0096 | -83% | 0.0963 |
| Readout+ZNE (expg) | 5 of 14 | 0.0094 | -83% | 0.0609 |

## Budget

Estimated quantum seconds per method per circuit (target 3.0 s; rep delay 250 µs per shot) and the shots that buys.

| Circuit | none shots / est. s | readout shots / est. s | zne shots / est. s | readout_zne shots / est. s |
|---|---|---|---|---|
| Bell | 11885 / 3.00 | 11885 / 3.00 | 11871 / 3.00 | 11875 / 3.00 |
| GHZ-3 | 11880 / 3.00 | 11882 / 3.00 | 11856 / 3.00 | 11864 / 3.00 |
| GHZ-5 | 11871 / 3.00 | 11874 / 3.00 | 11829 / 3.00 | 11842 / 3.00 |
| GHZ-7 | 11861 / 3.00 | 11866 / 3.00 | 11802 / 3.00 | 11820 / 3.00 |
| Grover-2 | 11880 / 3.00 | 11882 / 3.00 | 11856 / 3.00 | 11864 / 3.00 |
| Grover-3 | 11699 / 3.00 | 11735 / 3.00 | 11331 / 3.00 | 11436 / 3.00 |
| Grover-4 | 11475 / 3.00 | 11554 / 3.00 | 10722 / 3.00 | 10934 / 3.00 |
| QFT-3 | 11842 / 3.00 | 11848 / 3.00 | 11742 / 3.00 | 11772 / 3.00 |
| QFT-4 | 11808 / 3.00 | 11822 / 3.00 | 11646 / 3.00 | 11690 / 3.00 |
| QFT-5 | 11760 / 3.00 | 11784 / 3.00 | 11508 / 3.00 | 11580 / 3.00 |
| BV-4 | 11878 / 3.00 | 11881 / 3.00 | 11853 / 3.00 | 11858 / 3.00 |
| QAOA-3 | 11849 / 3.00 | 11856 / 3.00 | 11766 / 3.00 | 11790 / 3.00 |
| QAOA-4 | 11829 / 3.00 | 11841 / 3.00 | 11706 / 3.00 | 11741 / 3.00 |
| QAOA-4-p2 | 11760 / 3.00 | 11784 / 3.00 | 11505 / 3.00 | 11580 / 3.00 |

## Observable estimates (mean ± std over repeats)

| Circuit | Observable | Exact | None | Readout | Readout+ZNE (linear) | Readout+ZNE (expg) |
|---|---|---|---|---|---|---|
| Bell | ZZ | +1.000 | +0.977 ± 0.002 | +0.995 ± 0.003 | +1.001 ± 0.005 | +1.001 ± 0.005 |
| GHZ-3 | XXX | +1.000 | +0.951 ± 0.002 | +0.996 ± 0.007 | +0.996 ± 0.007 | +0.997 ± 0.007 |
| GHZ-5 | XXXXX | +1.000 | +0.928 ± 0.005 | +0.987 ± 0.006 | +0.999 ± 0.014 | +0.999 ± 0.014 |
| GHZ-7 | XXXXXXX | +1.000 | +0.890 ± 0.004 | +0.980 ± 0.008 | +1.002 ± 0.007 | +1.003 ± 0.006 |
| Grover-2 | P(11) | +1.000 | +0.985 ± 0.001 | +0.994 ± 0.004 | +1.001 ± 0.005 | +1.001 ± 0.005 |
| Grover-3 | P(101) | +0.945 | +0.854 ± 0.003 | +0.872 ± 0.006 | +0.925 ± 0.010 | +0.943 ± 0.012 |
| Grover-4 | P(1011) | +0.908 | +0.752 ± 0.004 | +0.773 ± 0.005 | +0.849 ± 0.011 | +0.906 ± 0.015 |
| QFT-3 | X0 | -0.707 | -0.691 ± 0.012 | -0.698 ± 0.015 | -0.696 ± 0.027 | -0.697 ± 0.028 |
| QFT-3 | X1 | +0.000 | -0.005 ± 0.014 | -0.001 ± 0.017 | -0.011 ± 0.029 | -0.030 ± 0.094 |
| QFT-3 | X2 | -1.000 | -0.972 ± 0.003 | -0.990 ± 0.006 | -0.999 ± 0.009 | -0.999 ± 0.009 |
| QFT-3 | Y0 | -0.707 | -0.670 ± 0.011 | -0.692 ± 0.013 | -0.716 ± 0.028 | -0.717 ± 0.029 |
| QFT-3 | Y1 | +1.000 | +0.972 ± 0.004 | +0.977 ± 0.004 | +0.997 ± 0.012 | +0.997 ± 0.011 |
| QFT-3 | Y2 | +0.000 | -0.005 ± 0.014 | -0.001 ± 0.012 | -0.001 ± 0.029 | -0.072 ± 0.244 |
| QFT-4 | X0 | -0.383 | -0.365 ± 0.008 | -0.366 ± 0.015 | -0.397 ± 0.021 | -0.401 ± 0.023 |
| QFT-4 | X1 | -0.707 | -0.666 ± 0.010 | -0.672 ± 0.009 | -0.698 ± 0.028 | -0.703 ± 0.031 |
| QFT-4 | X2 | -0.000 | -0.012 ± 0.016 | -0.002 ± 0.014 | -0.004 ± 0.023 | -0.033 ± 0.203 |
| QFT-4 | X3 | -1.000 | -0.958 ± 0.004 | -0.977 ± 0.006 | -0.997 ± 0.013 | -0.998 ± 0.012 |
| QFT-4 | Y0 | -0.924 | -0.884 ± 0.008 | -0.896 ± 0.013 | -0.924 ± 0.014 | -0.926 ± 0.014 |
| QFT-4 | Y1 | +0.707 | +0.687 ± 0.011 | +0.696 ± 0.012 | +0.710 ± 0.014 | +0.710 ± 0.014 |
| QFT-4 | Y2 | -1.000 | -0.947 ± 0.003 | -0.963 ± 0.011 | -0.996 ± 0.019 | -0.998 ± 0.018 |
| QFT-4 | Y3 | +0.000 | -0.009 ± 0.010 | -0.005 ± 0.017 | +0.002 ± 0.035 | -0.006 ± 0.027 |
| QFT-5 | X0 | -0.556 | -0.526 ± 0.010 | -0.538 ± 0.011 | -0.565 ± 0.030 | -0.568 ± 0.032 |
| QFT-5 | X1 | -0.383 | -0.360 ± 0.015 | -0.370 ± 0.011 | -0.372 ± 0.029 | -0.376 ± 0.032 |
| QFT-5 | X2 | -0.707 | -0.673 ± 0.010 | -0.682 ± 0.013 | -0.696 ± 0.030 | -0.699 ± 0.032 |
| QFT-5 | X3 | -0.000 | +0.007 ± 0.018 | +0.012 ± 0.019 | +0.003 ± 0.021 | -0.010 ± 0.074 |
| QFT-5 | X4 | -1.000 | -0.959 ± 0.004 | -0.968 ± 0.004 | -0.996 ± 0.010 | -0.998 ± 0.009 |
| QFT-5 | Y0 | -0.831 | -0.782 ± 0.007 | -0.805 ± 0.014 | -0.827 ± 0.018 | -0.831 ± 0.020 |
| QFT-5 | Y1 | +0.924 | +0.869 ± 0.005 | +0.887 ± 0.007 | +0.924 ± 0.013 | +0.930 ± 0.013 |
| QFT-5 | Y2 | -0.707 | -0.666 ± 0.010 | -0.680 ± 0.016 | -0.697 ± 0.017 | -0.700 ± 0.018 |
| QFT-5 | Y3 | +1.000 | +0.954 ± 0.003 | +0.963 ± 0.008 | +0.994 ± 0.012 | +0.996 ± 0.011 |
| QFT-5 | Y4 | +0.000 | +0.005 ± 0.013 | +0.004 ± 0.014 | -0.006 ± 0.047 | -0.005 ± 0.048 |
| BV-4 | P(1011) | +1.000 | +0.971 ± 0.001 | +0.994 ± 0.005 | +0.999 ± 0.005 | +1.000 ± 0.005 |
| QAOA-3 | <cut> | +1.988 | +1.971 ± 0.002 | +1.981 ± 0.004 | +1.988 ± 0.005 | +1.988 ± 0.005 |
| QAOA-4 | <cut> | +3.000 | +2.951 ± 0.011 | +2.981 ± 0.012 | +2.989 ± 0.030 | +2.990 ± 0.031 |
| QAOA-4-p2 | <cut> | +4.000 | +3.828 ± 0.004 | +3.876 ± 0.009 | +3.968 ± 0.015 | +3.982 ± 0.011 |

Readout-corrected and extrapolated values can leave the physical range; only expg (and the recipe, if it uses it) guards against that.
