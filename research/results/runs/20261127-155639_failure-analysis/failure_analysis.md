# When does recipe v1 fail, and why did Draper under-correct? (0 RU)

Run `20261127-155639_failure-analysis`. Saved hardware counts and local simulation only; no IBM calls.

> **EXPLORATORY, POST HOC.** Asked for after hardware work ended. It re-reads rounds that are already reported and tests no pre-registered target. Thresholds below are descriptive, not tuned rules.

Files: `failure_analysis.py` SHA-256 `ab4f6480b9e64b48…`, `recipe.py` SHA-256 `0b08bb7e96d9046e…`, `folding.py` SHA-256 `2309126cb3bc1c61…`

Notation (sign-normalised so the noise-free d is positive): d(s) = readout-corrected value at fold scale s minus the fully mixed value; D0 = exact minus fully mixed. **r** = ln(d1/d3)/2, the decay per unit of fold scale (computable without the answer). **κ** = ln(D0/d1)/r, how much the base circuit loses in units of r; v1 assumes κ = 1. **shape** = ln(d5/d3)/ln(d3/d1), 1 for one clean exponential. **λ3, λ5** = ln(D0/d(s))/ln(D0/d1), the noise amplification the scale-3 and scale-5 circuits really achieved (v1 assumes 3 and 5). κ and λ use the exact answer, so they explain errors after the fact.

## A. Every hardware record: what kind of failure

46 observable × round records from 16 cases (5 rounds). e = |v1 − exact| / range width; signed < 0 means v1 is below the answer (under-corrected).

| Mode | Records | e > 0.10 | 0.04 < e ≤ 0.10 | Cases with e > 0.04 |
|---|---|---|---|---|
| M0 no signal (exact ≈ fully mixed) | 6 | 0 | 0 | – |
| M1 no clean decay (linear branch) | 8 | 1 | 2 | QFT-6 X0 (r1), QFT-6 X2 (r1), QPE-4 P(1011) (26N) |
| M2 exp fit left the range; guard switched to linear | 11 | 2 | 1 | Grover-4-3it P(0110) (r1), Grover-4-3it P(0110) (r2), QFT-6 Y0 (r1) |
| M3 folds amplify less than assumed (under) | 14 | 1 | 1 | CDKM-adder-3 P(1011) (v12), Draper-adder-4 P(0010) (v12) |
| M4 folds amplify more than assumed (over) | 7 | 1 | 1 | QFT-6 X3 (r1), QFT-6 X3 (r2) |

Modes: M0 |D0| < 0.1 × width. M1 v1 used its linear branch (d not same-sign and decreasing). M2 the exponential fit landed outside the physical range and v1's guard silently used the linear fit instead. M3/M4 exponential branch with a usable decay, split by the sign of the error: below the answer means the folds amplified the noise less than v1 assumed (κ > 1), above means more (κ < 1).

### A.1 Every record

| Round | Circuit | Obs | D0 | d(1) / d(3) / d(5) | kept at s=1 | r ± SE | κ ± SE | shape | λ3 / λ5 | v1 (branch) | exact | signed err | Mode |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ibm_fez 24 Nov r1 | Bell | ZZ | 1.000 | +0.989 / +0.969 / +0.977 | 0.99 | 0.010 ± 0.005 | 1.07 ± 58.97 | -0.39 | 2.87 / 2.14 | +0.987 (linear) | +1.000 | -0.006 | M1 |
| ibm_fez 24 Nov r1 | GHZ-5 | XXXXX | 1.000 | +0.967 / +0.948 / +0.908 | 0.97 | 0.010 ± 0.007 | 3.21 ± 21.10 | 2.07 | 1.62 / 2.91 | +0.986 (exp) | +1.000 | -0.007 | M3 |
| ibm_fez 24 Nov r1 | Ising-4 | M | 0.010 | +0.022 / -0.029 / -0.045 | 2.19 | – ± 0.128 | – ± – | – | – / – | -0.033 (linear) | -0.010 | +0.011 | M0 |
| ibm_fez 24 Nov r1 | Mirror-4 | P(0000) | 0.938 | +0.866 / +0.779 / +0.694 | 0.92 | 0.053 ± 0.006 | 1.49 ± 0.32 | 1.08 | 2.34 / 3.80 | +0.979 (exp) | +1.000 | -0.021 | M3 |
| ibm_fez 24 Nov r1 | Grover-4-3it | P(0110) | 0.899 | +0.482 / +0.140 / +0.015 | 0.54 | 0.618 ± 0.030 | 1.01 ± 0.07 | 1.81 | 2.98 / 6.57 | +0.625 (exp→linear) | +0.961 | -0.336 | M2 |
| ibm_fez 24 Nov r1 | QFT-6 | X0 | 0.471 | +0.266 / -0.094 / -0.235 | 0.56 | – ± – | – ± – | – | – / – | -0.354 (linear) | -0.471 | -0.059 | M1 |
| ibm_fez 24 Nov r1 | QFT-6 | X1 | 0.556 | +0.487 / +0.365 / +0.197 | 0.88 | 0.145 ± 0.029 | 0.91 ± 0.43 | 2.13 | 3.21 / 7.91 | -0.626 (exp) | -0.556 | +0.035 | M4 |
| ibm_fez 24 Nov r1 | QFT-6 | X2 | 0.383 | +0.269 / +0.269 / +0.212 | 0.70 | – ± 0.029 | – ± 260670920934062.66 | – | – / – | -0.293 (linear) | -0.383 | -0.045 | M1 |
| ibm_fez 24 Nov r1 | QFT-6 | X3 | 0.707 | +0.625 / +0.388 / +0.147 | 0.88 | 0.238 ± 0.026 | 0.52 ± 0.16 | 2.05 | 4.84 / 12.69 | -0.905 (exp) | -0.707 | +0.099 | M4 |
| ibm_fez 24 Nov r1 | QFT-6 | X4 | 0.000 | +0.012 / +0.158 / +0.277 | 6675648156562.97 | – ± – | – ± – | – | – / – | +0.050 (linear) | -0.000 | -0.025 | M0 |
| ibm_fez 24 Nov r1 | QFT-6 | X5 | 1.000 | +0.920 / +0.786 / +0.617 | 0.92 | 0.079 ± 0.010 | 1.06 ± 0.27 | 1.54 | 2.88 / 5.78 | -1.002 (exp→linear) | -1.000 | +0.001 | M2 |
| ibm_fez 24 Nov r1 | QFT-6 | Y0 | 0.882 | +0.836 / +0.632 / +0.326 | 0.95 | 0.140 ± 0.014 | 0.38 ± 0.14 | 2.37 | 6.24 / 18.65 | -0.981 (exp→linear) | -0.882 | +0.049 | M2 |
| ibm_fez 24 Nov r1 | QFT-6 | Y1 | 0.831 | +0.681 / +0.587 / +0.421 | 0.82 | 0.074 ± 0.017 | 2.69 ± 1.04 | 2.24 | 1.74 / 3.40 | +0.784 (exp) | +0.831 | -0.024 | M3 |
| ibm_fez 24 Nov r1 | QFT-6 | Y2 | 0.924 | +0.829 / +0.523 / +0.223 | 0.90 | 0.230 ± 0.018 | 0.47 ± 0.09 | 1.85 | 5.27 / 13.17 | -0.980 (exp→linear) | -0.924 | +0.028 | M2 |
| ibm_fez 24 Nov r1 | QFT-6 | Y3 | 0.707 | +0.626 / +0.601 / +0.539 | 0.89 | 0.021 ± 0.013 | 5.88 ± 85891785552710.02 | 2.63 | 1.34 / 2.23 | +0.657 (exp) | +0.707 | -0.025 | M3 |
| ibm_fez 24 Nov r1 | QFT-6 | Y4 | 1.000 | +0.900 / +0.728 / +0.551 | 0.90 | 0.106 ± 0.011 | 1.00 ± 0.18 | 1.31 | 3.01 / 5.64 | -0.988 (exp→linear) | -1.000 | -0.006 | M2 |
| ibm_fez 24 Nov r1 | QFT-6 | Y5 | 0.000 | -0.048 / -0.129 / -0.167 | -13281903966834.29 | – ± – | – ± – | – | – / – | -0.025 (linear) | +0.000 | -0.013 | M0 |
| ibm_fez 24 Nov r1 | QAOA-5-p2 | <cut> | 1.500 | +1.382 / +1.164 / +0.923 | 0.92 | 0.086 ± 0.008 | 0.95 ± 0.17 | 1.35 | 3.10 / 5.93 | +4.040 (exp) | +4.000 | +0.008 | M4 |
| ibm_fez 24 Nov r1 | QAOA-6 | <cut> | 1.422 | +1.276 / +1.160 / +1.064 | 0.90 | 0.048 ± 0.014 | 2.28 ± 2.09 | 0.91 | 1.88 / 2.68 | +5.833 (exp) | +5.922 | -0.010 | M3 |
| ibm_fez 24 Nov r2 | Bell | ZZ | 1.000 | +0.984 / +0.973 / +0.973 | 0.98 | 0.006 ± 0.004 | 2.71 ± 40.73 | -0.00 | 1.74 / 1.74 | +0.985 (linear) | +1.000 | -0.007 | M1 |
| ibm_fez 24 Nov r2 | GHZ-5 | XXXXX | 1.000 | +0.961 / +0.933 / +0.874 | 0.96 | 0.015 ± 0.008 | 2.65 ± 12.03 | 2.17 | 1.75 / 3.39 | +0.990 (exp) | +1.000 | -0.005 | M3 |
| ibm_fez 24 Nov r2 | Ising-4 | M | 0.010 | +0.009 / -0.026 / -0.059 | 0.90 | – ± 0.139 | – ± 1.08 | – | – / – | -0.026 (linear) | -0.010 | +0.008 | M0 |
| ibm_fez 24 Nov r2 | Mirror-4 | P(0000) | 0.938 | +0.860 / +0.787 / +0.710 | 0.92 | 0.044 ± 0.006 | 1.95 ± 0.42 | 1.17 | 2.03 / 3.23 | +0.967 (exp) | +1.000 | -0.033 | M3 |
| ibm_fez 24 Nov r2 | Grover-4-3it | P(0110) | 0.899 | +0.489 / +0.154 / +0.027 | 0.54 | 0.578 ± 0.027 | 1.05 ± 0.07 | 1.52 | 2.90 / 5.78 | +0.632 (exp→linear) | +0.961 | -0.329 | M2 |
| ibm_fez 24 Nov r2 | QFT-6 | X0 | 0.471 | +0.313 / +0.051 / -0.131 | 0.66 | 0.909 ± 0.243 | 0.45 ± 0.13 | – | 5.44 / – | -0.411 (linear) | -0.471 | -0.030 | M1 |
| ibm_fez 24 Nov r2 | QFT-6 | X1 | 0.556 | +0.496 / +0.360 / +0.202 | 0.89 | 0.160 ± 0.031 | 0.71 ± 0.39 | 1.80 | 3.83 / 8.94 | -0.632 (exp) | -0.556 | +0.038 | M4 |
| ibm_fez 24 Nov r2 | QFT-6 | X2 | 0.383 | +0.316 / +0.346 / +0.262 | 0.83 | – ± 0.013 | – ± 140910502413991.91 | – | – / – | -0.349 (linear) | -0.383 | -0.017 | M1 |
| ibm_fez 24 Nov r2 | QFT-6 | X3 | 0.707 | +0.609 / +0.349 / +0.093 | 0.86 | 0.279 ± 0.029 | 0.53 ± 0.14 | 2.37 | 4.74 / 13.62 | -0.955 (exp) | -0.707 | +0.124 | M4 |
| ibm_fez 24 Nov r2 | QFT-6 | X4 | 0.000 | +0.075 / +0.151 / +0.237 | 41694962855449.78 | – ± – | – ± – | – | – / – | -0.033 (linear) | -0.000 | +0.017 | M0 |
| ibm_fez 24 Nov r2 | QFT-6 | X5 | 1.000 | +0.915 / +0.779 / +0.578 | 0.92 | 0.080 ± 0.010 | 1.11 ± 0.28 | 1.86 | 2.81 / 6.17 | -1.010 (exp→linear) | -1.000 | +0.005 | M2 |
| ibm_fez 24 Nov r2 | QFT-6 | Y0 | 0.882 | +0.804 / +0.621 / +0.328 | 0.91 | 0.129 ± 0.014 | 0.71 ± 0.16 | 2.47 | 3.81 / 10.74 | -0.942 (exp→linear) | -0.882 | +0.030 | M2 |
| ibm_fez 24 Nov r2 | QFT-6 | Y1 | 0.831 | +0.673 / +0.613 / +0.461 | 0.81 | 0.047 ± 0.017 | 4.50 ± 6.04 | 3.03 | 1.44 / 2.79 | +0.758 (exp) | +0.831 | -0.037 | M3 |
| ibm_fez 24 Nov r2 | QFT-6 | Y2 | 0.924 | +0.793 / +0.517 / +0.212 | 0.86 | 0.214 ± 0.018 | 0.71 ± 0.12 | 2.09 | 3.81 / 9.66 | -0.943 (exp→linear) | -0.924 | +0.010 | M2 |
| ibm_fez 24 Nov r2 | QFT-6 | Y3 | 0.707 | +0.661 / +0.656 / +0.574 | 0.93 | 0.003 ± 0.010 | 19.84 ± 51964638575570.44 | 19.66 | 1.10 / 3.08 | +0.698 (exp) | +0.707 | -0.004 | M3 |
| ibm_fez 24 Nov r2 | QFT-6 | Y4 | 1.000 | +0.896 / +0.722 / +0.550 | 0.90 | 0.108 ± 0.010 | 1.01 ± 0.17 | 1.25 | 2.98 / 5.45 | -0.982 (exp→linear) | -1.000 | -0.009 | M2 |
| ibm_fez 24 Nov r2 | QFT-6 | Y5 | 0.000 | -0.007 / -0.088 / -0.169 | -1878772867158.58 | – ± – | – ± – | – | – / – | +0.034 (linear) | +0.000 | +0.017 | M0 |
| ibm_fez 24 Nov r2 | QAOA-5-p2 | <cut> | 1.500 | +1.395 / +1.141 / +0.902 | 0.93 | 0.100 ± 0.009 | 0.72 ± 0.13 | 1.17 | 3.76 / 7.01 | +4.062 (exp) | +4.000 | +0.012 | M4 |
| ibm_fez 24 Nov r2 | QAOA-6 | <cut> | 1.422 | +1.288 / +1.191 / +1.068 | 0.91 | 0.039 ± 0.013 | 2.50 ± 4.16 | 1.38 | 1.80 / 2.91 | +5.856 (exp) | +5.922 | -0.007 | M3 |
| ibm_marrakesh 25 Nov 25N | Heisenberg-4 | M_stag | 0.646 | +0.535 / +0.381 / +0.233 | 0.83 | 0.170 ± 0.012 | 1.11 ± 0.15 | 1.44 | 2.80 / 5.39 | -0.666 (exp) | -0.646 | +0.010 | M4 |
| ibm_marrakesh 25 Nov 25N | QPE-4 | P(1011) | 0.937 | +0.827 / +0.631 / +0.440 | 0.88 | 0.135 ± 0.006 | 0.93 ± 0.08 | 1.33 | 3.15 / 6.01 | +0.985 (exp→linear) | +1.000 | -0.015 | M2 |
| ibm_marrakesh 26 Nov 26N | Heisenberg-4 | M_stag | 0.646 | +0.543 / +0.113 / -0.041 | 0.84 | 0.784 ± 0.035 | 0.22 ± 0.02 | – | 10.05 / – | -0.644 (linear) | -0.646 | -0.001 | M1 |
| ibm_marrakesh 26 Nov 26N | QPE-4 | P(1011) | 0.937 | +0.660 / -0.008 / +0.158 | 0.70 | – ± – | – ± – | – | – / – | +0.709 (linear) | +1.000 | -0.291 | M1 |
| ibm_marrakesh 26 Nov 22:57 v12 | W-4 | P(1 exc.) | 0.750 | +0.678 / +0.620 / +0.563 | 0.90 | 0.044 ± 0.007 | 2.29 ± 0.50 | 1.09 | 1.87 / 2.83 | +0.961 (exp) | +1.000 | -0.039 | M3 |
| ibm_marrakesh 26 Nov 22:57 v12 | Toffoli-3 | P(111) | 0.875 | +0.825 / +0.752 / +0.681 | 0.94 | 0.047 ± 0.005 | 1.25 ± 0.27 | 1.04 | 2.60 / 4.28 | +0.991 (exp) | +1.000 | -0.009 | M3 |
| ibm_marrakesh 26 Nov 22:57 v12 | CDKM-adder-3 | P(1011) | 0.937 | +0.702 / +0.450 / +0.293 | 0.75 | 0.222 ± 0.013 | 1.31 ± 0.12 | 0.96 | 2.53 / 4.01 | +0.934 (exp) | +1.000 | -0.066 | M3 |
| ibm_marrakesh 26 Nov 22:57 v12 | Draper-adder-4 | P(0010) | 0.937 | +0.610 / +0.414 / +0.278 | 0.65 | 0.193 ± 0.013 | 2.23 ± 0.20 | 1.03 | 1.90 / 2.82 | +0.805 (exp) | +1.000 | -0.195 | M3 |

### A.2 The guard's switch to linear (mode M2)

Post hoc what-if, not a recipe change: the same exponential fit clipped to the physical range instead of replaced by the linear fit.

| Round | Circuit | Obs | Exp. fit | Linear (what v1 reported) | Exp. clipped | Exact | e v1 | e clipped |
|---|---|---|---|---|---|---|---|---|
| ibm_fez 24 Nov r1 | Grover-4-3it | P(0110) | +1.055 | +0.625 | +1.000 | +0.961 | 0.336 | 0.039 |
| ibm_fez 24 Nov r1 | QFT-6 | X5 | -1.027 | -1.002 | -1.000 | -1.000 | 0.001 | 0.000 |
| ibm_fez 24 Nov r1 | QFT-6 | Y0 | -1.087 | -0.981 | -1.000 | -0.882 | 0.049 | 0.059 |
| ibm_fez 24 Nov r1 | QFT-6 | Y2 | -1.165 | -0.980 | -1.000 | -0.924 | 0.028 | 0.038 |
| ibm_fez 24 Nov r1 | QFT-6 | Y4 | -1.025 | -0.988 | -1.000 | -1.000 | 0.006 | 0.000 |
| ibm_fez 24 Nov r2 | Grover-4-3it | P(0110) | +1.013 | +0.632 | +1.000 | +0.961 | 0.329 | 0.039 |
| ibm_fez 24 Nov r2 | QFT-6 | X5 | -1.043 | -1.010 | -1.000 | -1.000 | 0.005 | 0.000 |
| ibm_fez 24 Nov r2 | QFT-6 | Y0 | -1.035 | -0.942 | -1.000 | -0.882 | 0.030 | 0.059 |
| ibm_fez 24 Nov r2 | QFT-6 | Y2 | -1.118 | -0.943 | -1.000 | -0.924 | 0.010 | 0.038 |
| ibm_fez 24 Nov r2 | QFT-6 | Y4 | -1.019 | -0.982 | -1.000 | -1.000 | 0.009 | 0.000 |
| ibm_marrakesh 25 Nov 25N | QPE-4 | P(1011) | +1.039 | +0.985 | +1.000 | +1.000 | 0.015 | 0.000 |

### A.3 A warning sign you can see without the answer: r

Records where v1 took its exponential branch, including M2 (n = 32). Spearman correlation of r with the relative error |v1 − exact| / D0: **0.58** (p = 0.0005; records are not independent: QFT-6 contributes 20 observables from 2 rounds).

| r (decay per unit scale) | Records | Median e | Max e | e > 0.04 | e > 0.10 | Worst |
|---|---|---|---|---|---|---|
| 0.0 – 0.1 | 15 | 0.009 | 0.039 | 0 | 0 | W-4 |
| 0.1 – 0.2 | 10 | 0.023 | 0.195 | 2 | 1 | Draper-adder-4 |
| 0.2 – ∞ | 7 | 0.099 | 0.336 | 5 | 3 | Grover-4-3it |

κ over the same records: median 1.08, interquartile range 0.86 – 2.28. Because the error is about 1 − exp(−(κ − 1) r), the same κ spread hurts little when r is small and a lot when r is large.

## B. Why Draper-adder-4 under-corrected (0.805 vs 1.0)

### B.1 What the hardware counts rule out

Draper and CDKM ran in the same round (26 Nov 22:57, `ibm_marrakesh`), both with 70 CZ.

| | Draper-adder-4 | CDKM-adder-3 |
|---|---|---|
| Readout-corrected P at scales 1 / 3 / 5 | 0.672 / 0.477 / 0.341 | 0.764 / 0.513 / 0.356 |
| No mitigation (the round's `none` job) | 0.644 | 0.714 |
| Recipe v1 | **0.805** | 0.934 |
| shape (1 = clean exponential) | 1.03 | 0.96 |
| Free-asymptote fit a + B·q^s: f(0) (asymptote a) | 0.800 (0.027) | 0.942 (0.096) |
| Each Z-string component extrapolated alone, then recombined | 0.818 | 0.948 |
| r per unit scale | 0.193 | 0.222 |
| κ (base-circuit loss / fold loss per unit) | **2.23** | 1.31 |
| Effective amplification of scale 3 / scale 5 (assumed 3 / 5) | **1.90 / 2.82** | 2.53 / 4.01 |

Per Z-string component (Draper; z = sign-normalised ⟨Z_S⟩, 1 when noise-free):

| Bits S | Weight | z(1) / z(3) / z(5) | shape | κ | Exp. extrapolation to s = 0 |
|---|---|---|---|---|---|
| (0,) | 1 | 0.842 / 0.711 / 0.543 | 1.59 | 2.03 | 0.956 |
| (1,) | 1 | 0.799 / 0.628 / 0.449 | 1.38 | 1.85 | 0.937 |
| (2,) | 1 | 0.752 / 0.564 / 0.451 | 0.78 | 1.97 | 0.846 |
| (3,) | 1 | 0.605 / 0.375 / 0.235 | 0.98 | 2.10 | 0.765 |
| (0, 1) | 2 | 0.810 / 0.636 / 0.483 | 1.14 | 1.75 | 0.926 |
| (0, 2) | 2 | 0.679 / 0.459 / 0.281 | 1.26 | 1.98 | 0.861 |
| (0, 3) | 2 | 0.549 / 0.323 / 0.179 | 1.12 | 2.27 | 0.734 |
| (1, 2) | 2 | 0.680 / 0.490 / 0.316 | 1.35 | 2.36 | 0.839 |
| (1, 3) | 2 | 0.528 / 0.258 / 0.113 | 1.15 | 1.78 | 0.790 |
| (2, 3) | 2 | 0.604 / 0.398 / 0.312 | 0.58 | 2.42 | 0.692 |
| (0, 1, 2) | 3 | 0.698 / 0.529 / 0.325 | 1.75 | 2.58 | 0.875 |
| (0, 1, 3) | 3 | 0.558 / 0.274 / 0.137 | 0.98 | 1.64 | 0.790 |
| (0, 2, 3) | 3 | 0.538 / 0.295 / 0.204 | 0.62 | 2.07 | 0.659 |
| (1, 2, 3) | 3 | 0.545 / 0.354 / 0.208 | 1.24 | 2.82 | 0.706 |
| (0, 1, 2, 3) | 4 | 0.569 / 0.335 / 0.215 | 0.83 | 2.13 | 0.715 |

Error rate per measured bit (readout-corrected; clbit 0 = least significant bit of the sum):

| Scale | clbit 0 | clbit 1 | clbit 2 | clbit 3 |
|---|---|---|---|---|
| 1 | 0.079 | 0.100 | 0.124 | 0.197 |
| 3 | 0.144 | 0.186 | 0.218 | 0.312 |
| 5 | 0.229 | 0.275 | 0.274 | 0.382 |

### B.2 Which kind of noise produces this signature (simulation, FakeMarrakesh)

Same compilation as the hardware round (level 2, best of 20 seeds on FakeMarrakesh; the hardware layout was not saved, so the qubits may differ). Readout errors off (v1 corrects them). 200000 shots per circuit, density-matrix simulator.

**Draper-adder-4** (sx 145, rz 99, cz 70, x 14)

| Noise model | P at 1 / 3 / 5 | v1 (branch) | Exp. fit | κ | shape | λ3 / λ5 |
|---|---|---|---|---|---|---|
| Markovian | 0.805 / 0.538 / 0.370 | 0.987 (exp) | 0.987 | 1.05 | 0.97 | 2.91 / 4.77 |
| Markovian + idle | 0.688 / 0.357 / 0.210 | 0.959 (exp) | 0.959 | 1.08 | 0.93 | 2.85 / 4.57 |
| + idle + slow detuning 10 kHz | 0.680 / 0.331 / 0.179 | 0.773 (exp→linear) | 1.000 | 1.00 | 1.00 | 3.00 / 5.00 |
| + idle + slow detuning 25 kHz | 0.645 / 0.234 / 0.103 | 0.734 (exp→linear) | 1.178 | 0.78 | 1.19 | 3.57 / 6.62 |
| + sx over-rotation 0.05 | 0.754 / 0.505 / 0.351 | 0.922 (exp) | 0.922 | 1.37 | 0.97 | 2.46 / 3.87 |
| + sx over-rotation 0.10 | 0.604 / 0.413 / 0.293 | 0.732 (exp) | 0.732 | 2.52 | 0.96 | 1.79 / 2.56 |
| + CZ phase error 0.05 | 0.750 / 0.322 / 0.141 | 0.861 (exp→linear) | 1.234 | 0.64 | 1.23 | 4.15 / 8.00 |
| + CZ local-Z error 0.05 | 0.639 / 0.127 / 0.060 | 0.710 (linear) | 1.786 | 0.44 | – | 5.51 / – |

**CDKM-adder-3** (sx 136, rz 93, cz 70, x 6)

| Noise model | P at 1 / 3 / 5 | v1 (branch) | Exp. fit | κ | shape | λ3 / λ5 |
|---|---|---|---|---|---|---|
| Markovian | 0.880 / 0.688 / 0.548 | 0.992 (exp) | 0.992 | 1.03 | 0.95 | 2.94 / 4.78 |
| Markovian + idle | 0.776 / 0.471 / 0.296 | 0.875 (exp→linear) | 1.007 | 0.98 | 1.00 | 3.05 / 5.11 |
| + idle + slow detuning 10 kHz | 0.754 / 0.366 / 0.167 | 0.869 (exp→linear) | 1.165 | 0.74 | 1.30 | 3.70 / 7.20 |
| + idle + slow detuning 25 kHz | 0.640 / 0.146 / 0.063 | 0.715 (exp→linear) | 1.627 | 0.50 | 2.46 | 5.00 / 14.82 |
| + sx over-rotation 0.05 | 0.852 / 0.668 / 0.534 | 0.959 (exp) | 0.959 | 1.30 | 0.95 | 2.54 / 4.00 |
| + sx over-rotation 0.10 | 0.779 / 0.615 / 0.494 | 0.874 (exp) | 0.874 | 2.08 | 0.95 | 1.96 / 2.88 |
| + CZ phase error 0.05 | 0.854 / 0.543 / 0.314 | 0.975 (exp→linear) | 1.124 | 0.68 | 1.30 | 3.94 / 7.77 |
| + CZ local-Z error 0.05 | 0.824 / 0.403 / 0.177 | 0.953 (exp→linear) | 1.276 | 0.52 | 1.36 | 4.86 / 10.09 |

**W-4** (rz 21, sx 17, cz 6, x 1)

| Noise model | P at 1 / 3 / 5 | v1 (branch) | Exp. fit | κ | shape | λ3 / λ5 |
|---|---|---|---|---|---|---|
| Markovian | 0.992 / 0.978 / 0.963 | 1.000 (exp) | 1.000 | 1.04 | 1.04 | 2.92 / 4.91 |
| Markovian + idle | 0.988 / 0.965 / 0.943 | 1.000 (exp) | 1.000 | 1.00 | 0.99 | 3.00 / 4.99 |
| + idle + slow detuning 10 kHz | 0.988 / 0.964 / 0.938 | 1.001 (exp→linear) | 1.002 | 0.95 | 1.10 | 3.11 / 5.43 |
| + idle + slow detuning 25 kHz | 0.987 / 0.953 / 0.910 | 1.008 (exp→linear) | 1.010 | 0.75 | 1.36 | 3.66 / 7.29 |
| + sx over-rotation 0.05 | 0.984 / 0.969 / 0.954 | 0.992 (exp) | 0.992 | 2.07 | 1.02 | 1.97 / 2.95 |
| + sx over-rotation 0.10 | 0.959 / 0.946 / 0.931 | 0.967 (exp) | 0.967 | 5.65 | 1.09 | 1.35 / 1.74 |
| + CZ phase error 0.05 | 0.990 / 0.959 / 0.914 | 1.011 (exp→linear) | 1.013 | 0.62 | 1.54 | 4.22 / 9.16 |
| + CZ local-Z error 0.05 | 0.986 / 0.926 / 0.834 | 1.029 (exp→linear) | 1.037 | 0.43 | 1.70 | 5.64 / 13.54 |

**Toffoli-3** (sx 16, rz 14, cz 7, x 2)

| Noise model | P at 1 / 3 / 5 | v1 (branch) | Exp. fit | κ | shape | λ3 / λ5 |
|---|---|---|---|---|---|---|
| Markovian | 0.984 / 0.953 / 0.922 | 0.999 (exp→linear) | 1.000 | 1.03 | 1.05 | 2.94 / 4.97 |
| Markovian + idle | 0.979 / 0.938 / 0.898 | 0.999 (exp→linear) | 1.001 | 1.01 | 1.05 | 2.98 / 5.05 |
| + idle + slow detuning 10 kHz | 0.979 / 0.937 / 0.897 | 0.999 (exp→linear) | 1.001 | 0.99 | 1.04 | 3.01 / 5.10 |
| + idle + slow detuning 25 kHz | 0.978 / 0.932 / 0.881 | 1.003 (exp→linear) | 1.005 | 0.91 | 1.15 | 3.21 / 5.75 |
| + sx over-rotation 0.05 | 0.981 / 0.951 / 0.920 | 0.998 (exp) | 0.998 | 1.18 | 1.05 | 2.69 / 4.46 |
| + sx over-rotation 0.10 | 0.975 / 0.944 / 0.914 | 0.991 (exp) | 0.991 | 1.60 | 1.05 | 2.25 / 3.56 |
| + CZ phase error 0.05 | 0.980 / 0.921 / 0.838 | 1.019 (exp→linear) | 1.025 | 0.65 | 1.55 | 4.07 / 8.82 |
| + CZ local-Z error 0.05 | 0.980 / 0.917 / 0.828 | 1.022 (exp→linear) | 1.028 | 0.62 | 1.58 | 4.20 / 9.26 |

Noise models:

- **Markovian**: FakeMarrakesh gate errors + T1/T2 during gates (the standard Aer model)
- **Markovian + idle**: as above, plus T1/T2 on every idle period (circuits scheduled ALAP)
- **+ idle + slow detuning 10 kHz**: plus a random static frequency offset per qubit (σ = 10 kHz, 16 draws averaged): low-frequency dephasing
- **+ idle + slow detuning 25 kHz**: same, σ = 25 kHz
- **+ sx over-rotation 0.05**: Markovian plus a coherent RX(0.05) after every physical sx pulse: cancels inside each folded sx·sx†·sx
- **+ sx over-rotation 0.10**: same, RX(0.10)
- **+ CZ phase error 0.05**: Markovian plus a coherent CPhase(0.05) after every CZ: adds up inside each folded CZ·CZ·CZ
- **+ CZ local-Z error 0.05**: Markovian plus RZ(0.05) on both qubits after every CZ: adds up inside folds
