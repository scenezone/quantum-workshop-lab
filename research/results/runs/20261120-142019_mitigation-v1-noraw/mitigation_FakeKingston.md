# Mitigation baselines: FakeKingston (simulator)

**These are our own implementations, not Qiskit Runtime resilience levels**, which have no effect on fake backends.

- Budget: **12000 shots per circuit per method**, mitigation overhead included.
- Readout mitigation: tensored per-qubit confusion matrices; 20% of the budget goes to calibration.
- ZNE: native folding after transpilation at scale factors [1, 3, 5] (two-qubit gate count verified to scale exactly), equal shots per factor, Richardson extrapolation with mitiq 1.1.0.
- Compilation: level 2, best of 20 transpiler seeds (fewest two-qubit gates, then depth).
- Repeats: 10, with fresh simulator seeds per repeat. Values are RMSE vs exact (mean ± std over repeats); lower is better.

## RMSE vs exact

| Circuit | Observable | 2q gates | None | Readout | ZNE | Best | Best clearly ahead of none? |
|---|---|---|---|---|---|---|---|
| Bell | <ZZ> | 1 | 0.0234 ± 0.0025 | **0.0046 ± 0.0026** | 0.0191 ± 0.0071 | readout | yes |
| GHZ-3 | X-parity <X^3> | 2 | 0.0495 ± 0.0020 | **0.0062 ± 0.0043** | 0.0483 ± 0.0109 | readout | yes |
| GHZ-5 | X-parity <X^5> | 4 | 0.0706 ± 0.0026 | **0.0113 ± 0.0086** | 0.0599 ± 0.0139 | readout | yes |
| Grover-2 | P(11) | 2 | 0.0152 ± 0.0017 | **0.0061 ± 0.0028** | 0.0066 ± 0.0037 | readout | yes |
| Grover-3 | P(101) | 37 | 0.0950 ± 0.0035 | 0.0716 ± 0.0046 | **0.0233 ± 0.0097** | zne | yes |
| QFT-3 | input \|5> = \|101>, <X_j> and <Y_j> on every qubit | 18 | 0.0249 ± 0.0035 | **0.0172 ± 0.0033** | 0.0432 ± 0.0137 | readout | yes |
| QFT-4 | input \|11> = \|1011>, <X_j> and <Y_j> on every qubit | 34 | 0.0342 ± 0.0020 | **0.0258 ± 0.0030** | 0.0421 ± 0.0090 | readout | yes |
| BV-4 | P(1011) | 3 | 0.0287 ± 0.0018 | **0.0076 ± 0.0030** | 0.0216 ± 0.0047 | readout | yes |
| QAOA-3 | expected cut (triangle) | 7 | 0.0175 ± 0.0023 | **0.0068 ± 0.0032** | 0.0109 ± 0.0071 | readout | yes |
| QAOA-4 | expected cut (4-ring) | 11 | 0.0532 ± 0.0144 | **0.0229 ± 0.0092** | 0.0478 ± 0.0304 | readout | yes |

## Summary

| Method | Circuits where best | Median RMSE | Median change vs none |
|---|---|---|---|
| none | 0 of 10 | 0.0315 | +0% |
| readout | 9 of 10 | 0.0094 | -61% |
| zne | 1 of 10 | 0.0327 | -17% |

## Cost

Shots are equal by construction. Gate time = Σ shots × circuit duration (from the backend's gate durations). Estimated QPU time also adds the default repetition delay of 250 µs per shot, which dominates for circuits this short. Ratios are relative to no mitigation. The last two columns show ZNE if every scale factor got the full budget instead of a third.

| Circuit | Shots (each method) | Readout gate time | Readout QPU time | ZNE gate time | ZNE QPU time | ZNE full-budget gate time | ZNE full-budget QPU time |
|---|---|---|---|---|---|---|---|
| Bell | 12000 | ×0.99 | ×1.00 | ×1.11 | ×1.00 | ×3.33 | ×3.00 |
| GHZ-3 | 12000 | ×0.98 | ×1.00 | ×1.18 | ×1.00 | ×3.55 | ×3.01 |
| GHZ-5 | 12000 | ×0.97 | ×1.00 | ×1.32 | ×1.00 | ×3.96 | ×3.01 |
| Grover-2 | 12000 | ×0.98 | ×1.00 | ×1.18 | ×1.00 | ×3.55 | ×3.01 |
| Grover-3 | 12000 | ×0.87 | ×1.00 | ×2.29 | ×1.03 | ×6.87 | ×3.10 |
| QFT-3 | 12000 | ×0.94 | ×1.00 | ×1.62 | ×1.01 | ×4.87 | ×3.02 |
| QFT-4 | 12000 | ×0.91 | ×1.00 | ×1.87 | ×1.01 | ×5.62 | ×3.04 |
| BV-4 | 12000 | ×0.98 | ×1.00 | ×1.21 | ×1.00 | ×3.63 | ×3.01 |
| QAOA-3 | 12000 | ×0.94 | ×1.00 | ×1.56 | ×1.01 | ×4.69 | ×3.02 |
| QAOA-4 | 12000 | ×0.93 | ×1.00 | ×1.73 | ×1.01 | ×5.20 | ×3.03 |

## Observable estimates (mean ± std over repeats)

| Circuit | Observable | Exact | None | Readout | ZNE |
|---|---|---|---|---|---|
| Bell | ZZ | +1.000 | +0.977 ± 0.003 | +0.997 ± 0.004 | +0.981 ± 0.007 |
| GHZ-3 | XXX | +1.000 | +0.951 ± 0.002 | +0.997 ± 0.007 | +0.952 ± 0.011 |
| GHZ-5 | XXXXX | +1.000 | +0.929 ± 0.003 | +0.990 ± 0.010 | +0.940 ± 0.014 |
| Grover-2 | P(11) | +1.000 | +0.985 ± 0.002 | +0.994 ± 0.003 | +0.993 ± 0.004 |
| Grover-3 | P(101) | +0.945 | +0.850 ± 0.004 | +0.874 ± 0.005 | +0.922 ± 0.010 |
| QFT-3 | X0 | -0.707 | -0.683 ± 0.005 | -0.699 ± 0.018 | -0.706 ± 0.027 |
| QFT-3 | X1 | +0.000 | +0.003 ± 0.018 | +0.008 ± 0.014 | -0.011 ± 0.070 |
| QFT-3 | X2 | -1.000 | -0.973 ± 0.003 | -0.986 ± 0.005 | -0.987 ± 0.016 |
| QFT-3 | Y0 | -0.707 | -0.678 ± 0.011 | -0.699 ± 0.009 | -0.674 ± 0.045 |
| QFT-3 | Y1 | +1.000 | +0.971 ± 0.002 | +0.978 ± 0.003 | +0.994 ± 0.013 |
| QFT-3 | Y2 | +0.000 | +0.001 ± 0.019 | +0.003 ± 0.020 | -0.027 ± 0.057 |
| QFT-4 | X0 | -0.383 | -0.360 ± 0.009 | -0.368 ± 0.014 | -0.384 ± 0.047 |
| QFT-4 | X1 | -0.707 | -0.662 ± 0.004 | -0.668 ± 0.011 | -0.691 ± 0.028 |
| QFT-4 | X2 | -0.000 | -0.008 ± 0.007 | -0.006 ± 0.010 | -0.007 ± 0.043 |
| QFT-4 | X3 | -1.000 | -0.956 ± 0.003 | -0.979 ± 0.008 | -0.974 ± 0.015 |
| QFT-4 | Y0 | -0.924 | -0.886 ± 0.007 | -0.903 ± 0.010 | -0.907 ± 0.021 |
| QFT-4 | Y1 | +0.707 | +0.689 ± 0.010 | +0.701 ± 0.005 | +0.691 ± 0.034 |
| QFT-4 | Y2 | -1.000 | -0.949 ± 0.003 | -0.958 ± 0.007 | -0.986 ± 0.022 |
| QFT-4 | Y3 | +0.000 | -0.000 ± 0.014 | -0.003 ± 0.020 | +0.011 ± 0.085 |
| BV-4 | P(1011) | +1.000 | +0.971 ± 0.002 | +0.992 ± 0.003 | +0.978 ± 0.005 |
| QAOA-3 | <cut> | +1.988 | +1.971 ± 0.002 | +1.982 ± 0.003 | +1.981 ± 0.011 |
| QAOA-4 | <cut> | +3.000 | +2.947 ± 0.014 | +2.977 ± 0.009 | +2.965 ± 0.046 |

Notes: GHZ uses X-parity because the Z-parity of an odd-size GHZ state is 0 whatever the noise. Readout-corrected and ZNE probabilities can leave [0, 1]; they are not clipped, so the RMSE shows it.
