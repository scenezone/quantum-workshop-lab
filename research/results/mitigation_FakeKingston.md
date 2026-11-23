# Mitigation baselines: FakeKingston (simulator)

Run `20261121-141214_mitigation` · 12000 shots per circuit per method · 10 repeats · seed selection: `gates`. Raw counts, circuits and the full method are in this run's folder.

**These are our own implementations, not Qiskit Runtime resilience levels.**

## Method

- Our own implementations on Qiskit Aer with the fake backend's noise model; NOT Qiskit Runtime resilience levels (those have no effect on fake backends).
- Compilation: optimization level 2, best of 20 transpiler seeds under the chosen selection strategy (compile-time information only, never measured error).
- Equal budget: every method spends the same total shots per circuit, including calibration and all ZNE scale factors.
- readout: per-qubit (tensored) confusion matrices measured on the circuit's physical qubits with two calibration circuits (all-0 and all-1); 20% of the budget. The inverse is applied to the measured distribution; results are not clipped.
- zne: native unitary folding of the transpiled circuit (G -> G (G^-1 G)^k, no re-optimization) at scale factors [1, 3, 5]; two-qubit gate count verified to scale exactly. Shots split equally over the scale factors. Extrapolation with mitiq 1.1.0: Richardson, linear least squares, or exponential with a known asymptote (the observable's value on the fully mixed state).
- readout_zne: calibration as in readout, every folded circuit's distribution is readout-corrected, then extrapolated as in zne. Remaining budget split equally over the scale factors.
- Repeats: every distinct circuit is simulated once with all shots it needs (memory=True); the shot record is split into disjoint chunks, one per repeat and method, in a fixed order.
- Metric: RMSE of fixed observables against exact values from the noise-free statevector, per repeat; reported as mean +- std over repeats.

## Main methods (Richardson extrapolation)

RMSE vs exact, mean ± std over repeats; lower is better. Bold = best of these four. "Clear" = the best method's gap to no mitigation is larger than the combined std.

| Circuit | Set | Observable | 2q gates | None | Readout | ZNE | Readout+ZNE | Clear? |
|---|---|---|---|---|---|---|---|---|
| Bell | core | <ZZ> | 1 | 0.0228 ± 0.0022 | 0.0051 ± 0.0028 | 0.0195 ± 0.0097 | **0.0044 ± 0.0039** | yes |
| GHZ-3 | core | X-parity <X^3> | 2 | 0.0500 ± 0.0033 | **0.0089 ± 0.0055** | 0.0489 ± 0.0123 | 0.0183 ± 0.0135 | yes |
| GHZ-5 | core | X-parity <X^5> | 4 | 0.0722 ± 0.0043 | 0.0150 ± 0.0063 | 0.0554 ± 0.0088 | **0.0137 ± 0.0098** | yes |
| GHZ-7 | deep | X-parity <X^7> | 6 | 0.1104 ± 0.0031 | 0.0258 ± 0.0136 | 0.0753 ± 0.0094 | **0.0168 ± 0.0141** | yes |
| Grover-2 | core | P(11), 1 iteration(s) | 2 | 0.0151 ± 0.0014 | **0.0074 ± 0.0041** | 0.0117 ± 0.0062 | 0.0077 ± 0.0053 | yes |
| Grover-3 | core | P(101), 2 iteration(s) | 37 | 0.0931 ± 0.0032 | 0.0723 ± 0.0060 | 0.0273 ± 0.0145 | **0.0189 ± 0.0126** | yes |
| Grover-4 | deep | P(1011), 2 iteration(s) | 73 | 0.1574 ± 0.0034 | 0.1365 ± 0.0061 | 0.0270 ± 0.0128 | **0.0184 ± 0.0155** | yes |
| QFT-3 | core | input \|5> = \|101>, <X_j> and <Y_j> on every qubit | 18 | 0.0242 ± 0.0028 | **0.0166 ± 0.0039** | 0.0463 ± 0.0114 | 0.0387 ± 0.0073 | yes |
| QFT-4 | core | input \|11> = \|1011>, <X_j> and <Y_j> on every qubit | 34 | 0.0346 ± 0.0017 | **0.0256 ± 0.0023** | 0.0396 ± 0.0129 | 0.0408 ± 0.0112 | yes |
| QFT-5 | deep | input \|21> = \|10101>, <X_j> and <Y_j> on every qubit | 56 | 0.0386 ± 0.0023 | **0.0266 ± 0.0027** | 0.0437 ± 0.0110 | 0.0433 ± 0.0135 | yes |
| BV-4 | core | P(1011) | 3 | 0.0284 ± 0.0010 | **0.0073 ± 0.0046** | 0.0226 ± 0.0079 | 0.0091 ± 0.0062 | yes |
| QAOA-3 | core | expected cut (triangle, p=1) | 7 | 0.0187 ± 0.0024 | 0.0074 ± 0.0041 | 0.0087 ± 0.0078 | **0.0061 ± 0.0068** | yes |
| QAOA-4 | core | expected cut (4-ring, p=1) | 11 | 0.0514 ± 0.0101 | **0.0174 ± 0.0095** | 0.0290 ± 0.0189 | 0.0236 ± 0.0178 | yes |
| QAOA-4-p2 | deep | expected cut (4-ring, p=2) | 25 | 0.1743 ± 0.0068 | 0.1199 ± 0.0085 | 0.0643 ± 0.0314 | **0.0201 ± 0.0162** | yes |

## Extrapolation comparison

Same counts, different fits. Bold = best of all eight methods for that circuit.

| Circuit | 2q gates | ZNE (Richardson) | ZNE (linear) | ZNE (exp) | Readout+ZNE (Richardson) | Readout+ZNE (linear) | Readout+ZNE (exp) |
|---|---|---|---|---|---|---|---|
| Bell | 1 | 0.0195 ± 0.0097 | 0.0201 ± 0.0060 | 0.0200 ± 0.0060 | 0.0044 ± 0.0039 | **0.0027 ± 0.0026** | 0.0027 ± 0.0026 |
| GHZ-3 | 2 | 0.0489 ± 0.0123 | 0.0435 ± 0.0064 | 0.0434 ± 0.0065 | 0.0183 ± 0.0135 | **0.0079 ± 0.0063** | 0.0080 ± 0.0063 |
| GHZ-5 | 4 | 0.0554 ± 0.0088 | 0.0596 ± 0.0062 | 0.0592 ± 0.0063 | 0.0137 ± 0.0098 | **0.0108 ± 0.0065** | 0.0110 ± 0.0067 |
| GHZ-7 | 6 | 0.0753 ± 0.0094 | 0.0850 ± 0.0086 | 0.0825 ± 0.0091 | 0.0168 ± 0.0141 | **0.0088 ± 0.0055** | 0.0106 ± 0.0054 |
| Grover-2 | 2 | 0.0117 ± 0.0062 | 0.0093 ± 0.0024 | 0.0091 ± 0.0024 | 0.0077 ± 0.0053 | **0.0048 ± 0.0028** | 0.0049 ± 0.0029 |
| Grover-3 | 37 | 0.0273 ± 0.0145 | 0.0446 ± 0.0086 | 0.0275 ± 0.0101 | 0.0189 ± 0.0126 | 0.0112 ± 0.0075 | **0.0107 ± 0.0048** |
| Grover-4 | 73 | 0.0270 ± 0.0128 | 0.0808 ± 0.0055 | 0.0251 ± 0.0073 | 0.0184 ± 0.0155 | 0.0563 ± 0.0130 | **0.0108 ± 0.0141** |
| QFT-3 | 18 | 0.0463 ± 0.0114 | 0.0246 ± 0.0088 | 0.2181 ± 0.2193 | 0.0387 ± 0.0073 | 0.0207 ± 0.0073 | 1.0489 ± 3.1490 |
| QFT-4 | 34 | 0.0396 ± 0.0129 | **0.0227 ± 0.0039** | 0.1063 ± 0.0997 | 0.0408 ± 0.0112 | 0.0238 ± 0.0094 | 0.1233 ± 0.1871 |
| QFT-5 | 56 | 0.0437 ± 0.0110 | 0.0242 ± 0.0055 | 0.0595 ± 0.0713 | 0.0433 ± 0.0135 | **0.0238 ± 0.0045** | 0.0884 ± 0.0760 |
| BV-4 | 3 | 0.0226 ± 0.0079 | 0.0221 ± 0.0046 | 0.0219 ± 0.0047 | 0.0091 ± 0.0062 | **0.0034 ± 0.0042** | 0.0034 ± 0.0042 |
| QAOA-3 | 7 | 0.0087 ± 0.0078 | 0.0113 ± 0.0035 | 0.0110 ± 0.0035 | 0.0061 ± 0.0068 | **0.0039 ± 0.0028** | 0.0043 ± 0.0029 |
| QAOA-4 | 11 | 0.0290 ± 0.0189 | 0.0312 ± 0.0179 | 0.0297 ± 0.0184 | 0.0236 ± 0.0178 | 0.0212 ± 0.0087 | 0.0223 ± 0.0099 |
| QAOA-4-p2 | 25 | 0.0643 ± 0.0314 | 0.0781 ± 0.0116 | 0.0569 ± 0.0126 | 0.0201 ± 0.0162 | 0.0311 ± 0.0181 | **0.0170 ± 0.0155** |

## Summary

| Method | Best of 8 (circuits) | Best of main 4 | Median RMSE | Median change vs none |
|---|---|---|---|---|
| None | 0 of 14 | 0 | 0.0443 | +0% |
| Readout | 2 of 14 | 7 | 0.0170 | -56% |
| ZNE (Richardson) | 0 of 14 | 0 | 0.0343 | -23% |
| ZNE (linear) | 1 of 14 | - | 0.0279 | -36% |
| ZNE (exp) | 0 of 14 | - | 0.0366 | -24% |
| Readout+ZNE (Richardson) | 0 of 14 | 7 | 0.0183 | -68% |
| Readout+ZNE (linear) | 8 of 14 | - | 0.0110 | -81% |
| Readout+ZNE (exp) | 3 of 14 | - | 0.0107 | -84% |

## When does ZNE help?

Circuits sorted by two-qubit gate count. Compares readout mitigation alone with the best method that uses ZNE (any fit, with or without readout correction).

| Circuit | 2q gates | ESP | Readout | Best ZNE method | Its RMSE | ZNE family better? |
|---|---|---|---|---|---|---|
| Bell | 1 | 0.988 | 0.0051 | Readout+ZNE (linear) | 0.0027 | slightly (within spread) |
| GHZ-3 | 2 | 0.973 | 0.0089 | Readout+ZNE (linear) | 0.0079 | slightly (within spread) |
| Grover-2 | 2 | 0.986 | 0.0074 | Readout+ZNE (linear) | 0.0048 | slightly (within spread) |
| BV-4 | 3 | 0.971 | 0.0073 | Readout+ZNE (linear) | 0.0034 | slightly (within spread) |
| GHZ-5 | 4 | 0.961 | 0.0150 | Readout+ZNE (linear) | 0.0108 | slightly (within spread) |
| GHZ-7 | 6 | 0.939 | 0.0258 | Readout+ZNE (linear) | 0.0088 | yes |
| QAOA-3 | 7 | 0.970 | 0.0074 | Readout+ZNE (linear) | 0.0039 | slightly (within spread) |
| QAOA-4 | 11 | 0.947 | 0.0174 | Readout+ZNE (linear) | 0.0212 | no (within spread) |
| QFT-3 | 18 | 0.961 | 0.0166 | Readout+ZNE (linear) | 0.0207 | no (within spread) |
| QAOA-4-p2 | 25 | 0.921 | 0.1199 | Readout+ZNE (exp) | 0.0170 | yes |
| QFT-4 | 34 | 0.937 | 0.0256 | ZNE (linear) | 0.0227 | slightly (within spread) |
| Grover-3 | 37 | 0.907 | 0.0723 | Readout+ZNE (exp) | 0.0107 | yes |
| QFT-5 | 56 | 0.909 | 0.0266 | Readout+ZNE (linear) | 0.0238 | slightly (within spread) |
| Grover-4 | 73 | 0.839 | 0.1365 | Readout+ZNE (exp) | 0.0108 | yes |

## Cost

Shots are equal by construction. Gate time = Σ shots × circuit duration (backend gate durations). Estimated QPU time adds the default repetition delay of 250 µs per shot. Ratios are relative to no mitigation. "Full budget" = ZNE if every scale factor got all the shots. All are estimates; real `quantum_seconds` must be measured on hardware.

| Circuit | Shots | Readout QPU | ZNE gate | ZNE QPU | Readout+ZNE gate | Readout+ZNE QPU | ZNE full-budget gate | ZNE full-budget QPU |
|---|---|---|---|---|---|---|---|---|
| Bell | 12000 | ×1.00 | ×1.11 | ×1.00 | ×1.08 | ×1.00 | ×3.33 | ×3.00 |
| GHZ-3 | 12000 | ×1.00 | ×1.18 | ×1.00 | ×1.13 | ×1.00 | ×3.55 | ×3.01 |
| GHZ-5 | 12000 | ×1.00 | ×1.32 | ×1.00 | ×1.22 | ×1.00 | ×3.96 | ×3.01 |
| GHZ-7 | 12000 | ×1.00 | ×1.43 | ×1.00 | ×1.30 | ×1.00 | ×4.30 | ×3.01 |
| Grover-2 | 12000 | ×1.00 | ×1.18 | ×1.00 | ×1.13 | ×1.00 | ×3.55 | ×3.01 |
| Grover-3 | 12000 | ×1.00 | ×2.29 | ×1.03 | ×1.90 | ×1.02 | ×6.87 | ×3.10 |
| Grover-4 | 12000 | ×0.99 | ×2.60 | ×1.07 | ×2.12 | ×1.05 | ×7.80 | ×3.21 |
| QFT-3 | 12000 | ×1.00 | ×1.62 | ×1.01 | ×1.44 | ×1.01 | ×4.87 | ×3.02 |
| QFT-4 | 12000 | ×1.00 | ×1.87 | ×1.01 | ×1.61 | ×1.01 | ×5.62 | ×3.04 |
| QFT-5 | 12000 | ×1.00 | ×2.10 | ×1.02 | ×1.77 | ×1.02 | ×6.30 | ×3.07 |
| BV-4 | 12000 | ×1.00 | ×1.21 | ×1.00 | ×1.15 | ×1.00 | ×3.63 | ×3.01 |
| QAOA-3 | 12000 | ×1.00 | ×1.56 | ×1.01 | ×1.39 | ×1.00 | ×4.69 | ×3.02 |
| QAOA-4 | 12000 | ×1.00 | ×1.73 | ×1.01 | ×1.52 | ×1.01 | ×5.20 | ×3.03 |
| QAOA-4-p2 | 12000 | ×1.00 | ×2.11 | ×1.02 | ×1.77 | ×1.02 | ×6.32 | ×3.07 |

## Observable estimates (mean ± std over repeats)

| Circuit | Observable | Exact | None | Readout | ZNE (Richardson) | Readout+ZNE (Richardson) |
|---|---|---|---|---|---|---|
| Bell | ZZ | +1.000 | +0.977 ± 0.002 | +0.995 ± 0.003 | +0.981 ± 0.010 | +1.000 ± 0.006 |
| GHZ-3 | XXX | +1.000 | +0.950 ± 0.003 | +0.993 ± 0.008 | +0.951 ± 0.012 | +0.997 ± 0.023 |
| GHZ-5 | XXXXX | +1.000 | +0.928 ± 0.004 | +0.985 ± 0.006 | +0.945 ± 0.009 | +1.001 ± 0.017 |
| GHZ-7 | XXXXXXX | +1.000 | +0.890 ± 0.003 | +0.974 ± 0.014 | +0.925 ± 0.009 | +0.999 ± 0.023 |
| Grover-2 | P(11) | +1.000 | +0.985 ± 0.001 | +0.993 ± 0.004 | +0.988 ± 0.006 | +1.004 ± 0.009 |
| Grover-3 | P(101) | +0.945 | +0.852 ± 0.003 | +0.873 ± 0.006 | +0.918 ± 0.014 | +0.960 ± 0.018 |
| Grover-4 | P(1011) | +0.908 | +0.751 ± 0.003 | +0.772 ± 0.006 | +0.881 ± 0.013 | +0.896 ± 0.021 |
| QFT-3 | X0 | -0.707 | -0.688 ± 0.012 | -0.695 ± 0.012 | -0.703 ± 0.041 | -0.701 ± 0.032 |
| QFT-3 | X1 | +0.000 | -0.005 ± 0.014 | -0.002 ± 0.010 | -0.032 ± 0.053 | +0.009 ± 0.042 |
| QFT-3 | X2 | -1.000 | -0.972 ± 0.003 | -0.987 ± 0.009 | -0.979 ± 0.013 | -0.988 ± 0.018 |
| QFT-3 | Y0 | -0.707 | -0.676 ± 0.014 | -0.690 ± 0.012 | -0.693 ± 0.035 | -0.705 ± 0.047 |
| QFT-3 | Y1 | +1.000 | +0.973 ± 0.004 | +0.979 ± 0.006 | +0.993 ± 0.016 | +1.002 ± 0.023 |
| QFT-3 | Y2 | +0.000 | -0.008 ± 0.012 | +0.003 ± 0.015 | -0.022 ± 0.080 | -0.022 ± 0.060 |
| QFT-4 | X0 | -0.383 | -0.365 ± 0.009 | -0.372 ± 0.016 | -0.385 ± 0.046 | -0.389 ± 0.031 |
| QFT-4 | X1 | -0.707 | -0.666 ± 0.009 | -0.669 ± 0.012 | -0.721 ± 0.050 | -0.715 ± 0.045 |
| QFT-4 | X2 | -0.000 | -0.009 ± 0.019 | -0.010 ± 0.012 | +0.031 ± 0.046 | +0.031 ± 0.076 |
| QFT-4 | X3 | -1.000 | -0.957 ± 0.003 | -0.984 ± 0.012 | -0.983 ± 0.023 | -0.999 ± 0.023 |
| QFT-4 | Y0 | -0.924 | -0.883 ± 0.006 | -0.901 ± 0.011 | -0.902 ± 0.024 | -0.932 ± 0.018 |
| QFT-4 | Y1 | +0.707 | +0.687 ± 0.012 | +0.699 ± 0.013 | +0.697 ± 0.041 | +0.695 ± 0.043 |
| QFT-4 | Y2 | -1.000 | -0.947 ± 0.003 | -0.961 ± 0.008 | -0.986 ± 0.019 | -0.996 ± 0.025 |
| QFT-4 | Y3 | +0.000 | -0.008 ± 0.009 | -0.010 ± 0.014 | +0.004 ± 0.054 | +0.017 ± 0.044 |
| QFT-5 | X0 | -0.556 | -0.526 ± 0.009 | -0.540 ± 0.012 | -0.535 ± 0.066 | -0.582 ± 0.031 |
| QFT-5 | X1 | -0.383 | -0.356 ± 0.007 | -0.369 ± 0.015 | -0.374 ± 0.039 | -0.370 ± 0.060 |
| QFT-5 | X2 | -0.707 | -0.672 ± 0.008 | -0.682 ± 0.010 | -0.673 ± 0.044 | -0.680 ± 0.039 |
| QFT-5 | X3 | -0.000 | +0.011 ± 0.016 | +0.007 ± 0.014 | +0.003 ± 0.056 | -0.027 ± 0.066 |
| QFT-5 | X4 | -1.000 | -0.959 ± 0.004 | -0.969 ± 0.004 | -0.985 ± 0.012 | -1.001 ± 0.016 |
| QFT-5 | Y0 | -0.831 | -0.782 ± 0.009 | -0.805 ± 0.011 | -0.829 ± 0.026 | -0.808 ± 0.034 |
| QFT-5 | Y1 | +0.924 | +0.870 ± 0.006 | +0.888 ± 0.012 | +0.899 ± 0.027 | +0.925 ± 0.030 |
| QFT-5 | Y2 | -0.707 | -0.663 ± 0.007 | -0.682 ± 0.017 | -0.680 ± 0.047 | -0.701 ± 0.041 |
| QFT-5 | Y3 | +1.000 | +0.951 ± 0.003 | +0.967 ± 0.007 | +0.974 ± 0.017 | +0.995 ± 0.021 |
| QFT-5 | Y4 | +0.000 | -0.002 ± 0.012 | +0.007 ± 0.013 | +0.014 ± 0.053 | +0.030 ± 0.059 |
| BV-4 | P(1011) | +1.000 | +0.972 ± 0.001 | +0.993 ± 0.005 | +0.977 ± 0.008 | +1.001 ± 0.011 |
| QAOA-3 | <cut> | +1.988 | +1.970 ± 0.002 | +1.981 ± 0.004 | +1.982 ± 0.010 | +1.992 ± 0.009 |
| QAOA-4 | <cut> | +3.000 | +2.949 ± 0.010 | +2.983 ± 0.009 | +2.984 ± 0.032 | +3.007 ± 0.030 |
| QAOA-4-p2 | <cut> | +4.000 | +3.826 ± 0.007 | +3.880 ± 0.009 | +3.936 ± 0.031 | +3.993 ± 0.026 |

Notes: GHZ uses X-parity because the Z-parity of an odd-size GHZ state is 0 whatever the noise. Readout-corrected and extrapolated probabilities can leave [0, 1]; they are not clipped. Exponential fits use the observable's fully-mixed value as the asymptote; a failed fit is reported, not hidden.
