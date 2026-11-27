# Recipe v1.1 design replay (0 RU)

Run `20261126-223700_v1-1-design-replay`. Saved hardware data only, no new jobs.

> **DESIGN DATA, NOT EVIDENCE.** These are the rounds that motivated v1.1. The rules (recipe_v1_1.py, k = 2) were fixed from physics before this replay and are not changed because of it.

Files: `recipe_v1_1.py` SHA-256 `4b9a2a84ff354876…`, `recipe.py` SHA-256 `0b08bb7e96d9046e…`, `v1_1_design_replay.py` SHA-256 `114a3416f83d91ec…`

## Headline

| Class | Cases | Flagged by v1.1 |
|---|---|---|
| failure | 4 | 4 |
| ambiguous | 0 | 0 |
| good | 8 | 3 |

- Failures flagged: **4/4**.
- Good cases flagged (false alarms): **3/8**.
- Ambiguous cases flagged: 0/0.
- v1.1 clearly worse than none (design analogue of T1): **1/12** (ibm_fez 24 Nov | QFT-6).

Class per observable and round: failure = v1 clearly worse than none or e > 0.10; good = v1 clearly better than none and e < 0.04; ambiguous = rest (e = |v1 - exact| / range width). A case takes its worst class and is flagged if any of its observables/rounds is flagged.

## Cases

| Case | Class | Flagged | Rules fired | Round / observable: err none / v1 / v1.1 (v1.1 vs none) |
|---|---|---|---|---|
| ibm_fez 24 Nov | Grover-4-3it | failure | yes | one_exp | r1 P(0110): 0.438 / 0.336 / 0.417 (clearly better)<br>r2 P(0110): 0.431 / 0.329 / 0.410 (clearly better) |
| ibm_fez 24 Nov | Ising-4 | failure | yes | decay | r1 M: 0.009 / 0.023 / 0.012 (no clear difference)<br>r2 M: 0.002 / 0.016 / 0.001 (no clear difference) |
| ibm_fez 24 Nov | QFT-6 | failure | yes | decay, one_exp | r1 X0: 0.219 / 0.117 / 0.206 (no clear difference)<br>r1 X1: 0.092 / 0.070 / 0.068 (clearly better)<br>r1 X2: 0.090 / 0.090 / 0.090 (no clear difference)<br>r1 X3: 0.164 / 0.197 / 0.082 (clearly better)<br>r1 X4: 0.050 / 0.050 / 0.012 (clearly better)<br>r1 X5: 0.114 / 0.002 / 0.080 (clearly better)<br>r1 Y0: 0.105 / 0.099 / 0.046 (clearly better)<br>r1 Y1: 0.139 / 0.047 / 0.150 (no clear difference)<br>r1 Y2: 0.149 / 0.056 / 0.095 (clearly better)<br>r1 Y3: 0.072 / 0.050 / 0.050 (clearly better)<br>r1 Y4: 0.131 / 0.012 / 0.012 (clearly better)<br>r1 Y5: 0.020 / 0.025 / 0.048 (clearly worse)<br>r2 X0: 0.195 / 0.061 / 0.159 (clearly better)<br>r2 X1: 0.052 / 0.077 / 0.077 (no clear difference)<br>r2 X2: 0.092 / 0.034 / 0.066 (clearly better)<br>r2 X3: 0.139 / 0.248 / 0.098 (clearly better)<br>r2 X4: 0.048 / 0.033 / 0.075 (clearly worse)<br>r2 X5: 0.139 / 0.010 / 0.085 (clearly better)<br>r2 Y0: 0.077 / 0.060 / 0.078 (no clear difference)<br>r2 Y1: 0.122 / 0.073 / 0.158 (clearly worse)<br>r2 Y2: 0.111 / 0.020 / 0.131 (clearly worse)<br>r2 Y3: 0.072 / 0.009 / 0.046 (clearly better)<br>r2 Y4: 0.124 / 0.018 / 0.018 (clearly better)<br>r2 Y5: 0.014 / 0.034 / 0.007 (no clear difference) |
| ibm_marrakesh 26 Nov | QPE-4 | failure | yes | decay | 26N P(1011): 0.307 / 0.291 / 0.277 (clearly better) |
| ibm_fez 24 Nov | Bell | good | no | - | r1 ZZ: 0.080 / 0.013 / 0.013 (clearly better)<br>r2 ZZ: 0.057 / 0.015 / 0.015 (clearly better) |
| ibm_fez 24 Nov | GHZ-5 | good | no | - | r1 XXXXX: 0.118 / 0.014 / 0.014 (clearly better)<br>r2 XXXXX: 0.132 / 0.010 / 0.010 (clearly better) |
| ibm_fez 24 Nov | Mirror-4 | good | no | - | r1 P(0000): 0.120 / 0.021 / 0.021 (clearly better)<br>r2 P(0000): 0.100 / 0.033 / 0.033 (clearly better) |
| ibm_fez 24 Nov | QAOA-5-p2 | good | no | - | r1 <cut>: 0.193 / 0.040 / 0.040 (clearly better)<br>r2 <cut>: 0.187 / 0.062 / 0.062 (clearly better) |
| ibm_fez 24 Nov | QAOA-6 | good | no | - | r1 <cut>: 0.160 / 0.088 / 0.088 (clearly better)<br>r2 <cut>: 0.167 / 0.065 / 0.065 (clearly better) |
| ibm_marrakesh 25 Nov | Heisenberg-4 | good | yes | one_exp | 25N M_stag: 0.124 / 0.020 / 0.111 (clearly better) |
| ibm_marrakesh 25 Nov | QPE-4 | good | yes | one_exp | 25N P(1011): 0.160 / 0.015 / 0.111 (clearly better) |
| ibm_marrakesh 26 Nov | Heisenberg-4 | good | yes | decay, one_exp | 26N M_stag: 0.124 / 0.003 / 0.103 (clearly better) |

## Per observable and round

d(s) = readout-corrected value minus fully mixed value; SE = bootstrap std. Rules: decay / alive / one_exp (✓ pass, ✗ fail).

| Case | Rd | Obs | exact | d(1) / d(3) / d(5) | SE(d5) | Rules | v1 (branch) | v1.1 | none | e | v1 vs none | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Bell (ibm_fez 24 Nov) | r1 | ZZ | +1.000 | +0.989 / +0.969 / +0.977 | 0.012 | ✓ ✓ ✓ | +0.987 (linear) | +0.987 | +0.920 | 0.006 | clearly better | good |
| Bell (ibm_fez 24 Nov) | r2 | ZZ | +1.000 | +0.984 / +0.973 / +0.973 | 0.009 | ✓ ✓ ✓ | +0.985 (linear) | +0.985 | +0.943 | 0.007 | clearly better | good |
| GHZ-5 (ibm_fez 24 Nov) | r1 | XXXXX | +1.000 | +0.967 / +0.948 / +0.908 | 0.016 | ✓ ✓ ✓ | +0.986 (exp) | +0.986 | +0.882 | 0.007 | clearly better | good |
| GHZ-5 (ibm_fez 24 Nov) | r2 | XXXXX | +1.000 | +0.961 / +0.933 / +0.874 | 0.015 | ✓ ✓ ✓ | +0.990 (exp) | +0.990 | +0.868 | 0.005 | clearly better | good |
| Grover-4-3it (ibm_fez 24 Nov) | r1 | P(0110) | +0.961 | +0.482 / +0.140 / +0.015 | 0.005 | ✓ ✓ ✗ | +0.625 (exp) | +0.544 | +0.523 | 0.336 | clearly better | failure |
| Grover-4-3it (ibm_fez 24 Nov) | r2 | P(0110) | +0.961 | +0.489 / +0.154 / +0.027 | 0.006 | ✓ ✓ ✗ | +0.632 (exp) | +0.551 | +0.531 | 0.329 | no clear difference | failure |
| Ising-4 (ibm_fez 24 Nov) | r1 | M | -0.010 | -0.022 / +0.029 / +0.045 | 0.012 | ✗ ✓ ✓ | -0.033 (linear) | -0.022 | -0.001 | 0.011 | no clear difference | ambiguous |
| Ising-4 (ibm_fez 24 Nov) | r2 | M | -0.010 | -0.009 / +0.026 / +0.059 | 0.012 | ✗ ✓ ✓ | -0.026 (linear) | -0.009 | -0.012 | 0.008 | clearly worse | failure |
| Mirror-4 (ibm_fez 24 Nov) | r1 | P(0000) | +1.000 | +0.866 / +0.779 / +0.694 | 0.010 | ✓ ✓ ✓ | +0.979 (exp) | +0.979 | +0.880 | 0.021 | clearly better | good |
| Mirror-4 (ibm_fez 24 Nov) | r2 | P(0000) | +1.000 | +0.860 / +0.787 / +0.710 | 0.009 | ✓ ✓ ✓ | +0.967 (exp) | +0.967 | +0.900 | 0.033 | clearly better | good |
| QAOA-5-p2 (ibm_fez 24 Nov) | r1 | <cut> | +4.000 | +1.382 / +1.164 / +0.923 | 0.019 | ✓ ✓ ✓ | +4.040 (exp) | +4.040 | +3.807 | 0.008 | clearly better | good |
| QAOA-5-p2 (ibm_fez 24 Nov) | r2 | <cut> | +4.000 | +1.395 / +1.141 / +0.902 | 0.020 | ✓ ✓ ✓ | +4.062 (exp) | +4.062 | +3.813 | 0.012 | clearly better | good |
| QAOA-6 (ibm_fez 24 Nov) | r1 | <cut> | +5.922 | +1.276 / +1.160 / +1.064 | 0.026 | ✓ ✓ ✓ | +5.833 (exp) | +5.833 | +5.761 | 0.010 | clearly better | good |
| QAOA-6 (ibm_fez 24 Nov) | r2 | <cut> | +5.922 | +1.288 / +1.191 / +1.068 | 0.027 | ✓ ✓ ✓ | +5.856 (exp) | +5.856 | +5.755 | 0.007 | clearly better | good |
| QFT-6 (ibm_fez 24 Nov) | r1 | X0 | -0.471 | -0.266 / +0.094 / +0.235 | 0.018 | ✗ ✓ ✗ | -0.354 (linear) | -0.266 | -0.253 | 0.059 | clearly better | ambiguous |
| QFT-6 (ibm_fez 24 Nov) | r1 | X1 | -0.556 | -0.487 / -0.365 / -0.197 | 0.018 | ✓ ✓ ✗ | -0.626 (exp) | -0.487 | -0.464 | 0.035 | no clear difference | ambiguous |
| QFT-6 (ibm_fez 24 Nov) | r1 | X2 | -0.383 | -0.269 / -0.269 / -0.212 | 0.019 | ✓ ✓ ✓ | -0.293 (linear) | -0.293 | -0.292 | 0.045 | no clear difference | ambiguous |
| QFT-6 (ibm_fez 24 Nov) | r1 | X3 | -0.707 | -0.625 / -0.388 / -0.147 | 0.019 | ✓ ✓ ✗ | -0.905 (exp) | -0.625 | -0.544 | 0.099 | no clear difference | ambiguous |
| QFT-6 (ibm_fez 24 Nov) | r1 | X4 | -0.000 | -0.012 / -0.158 / -0.277 | 0.019 | ✗ ✓ ✓ | +0.050 (linear) | -0.012 | -0.050 | 0.025 | no clear difference | ambiguous |
| QFT-6 (ibm_fez 24 Nov) | r1 | X5 | -1.000 | -0.920 / -0.786 / -0.617 | 0.017 | ✓ ✓ ✗ | -1.002 (exp) | -0.920 | -0.886 | 0.001 | clearly better | good |
| QFT-6 (ibm_fez 24 Nov) | r1 | Y0 | -0.882 | -0.836 / -0.632 / -0.326 | 0.018 | ✓ ✓ ✗ | -0.981 (exp) | -0.836 | -0.776 | 0.049 | no clear difference | ambiguous |
| QFT-6 (ibm_fez 24 Nov) | r1 | Y1 | +0.831 | +0.681 / +0.587 / +0.421 | 0.016 | ✓ ✓ ✗ | +0.784 (exp) | +0.681 | +0.692 | 0.024 | clearly better | good |
| QFT-6 (ibm_fez 24 Nov) | r1 | Y2 | -0.924 | -0.829 / -0.523 / -0.223 | 0.019 | ✓ ✓ ✗ | -0.980 (exp) | -0.829 | -0.775 | 0.028 | clearly better | good |
| QFT-6 (ibm_fez 24 Nov) | r1 | Y3 | +0.707 | +0.626 / +0.601 / +0.539 | 0.017 | ✓ ✓ ✓ | +0.657 (exp) | +0.657 | +0.635 | 0.025 | clearly better | good |
| QFT-6 (ibm_fez 24 Nov) | r1 | Y4 | -1.000 | -0.900 / -0.728 / -0.551 | 0.017 | ✓ ✓ ✓ | -0.988 (exp) | -0.988 | -0.869 | 0.006 | clearly better | good |
| QFT-6 (ibm_fez 24 Nov) | r1 | Y5 | +0.000 | -0.048 / -0.129 / -0.167 | 0.022 | ✗ ✓ ✓ | -0.025 (linear) | -0.048 | -0.020 | 0.013 | no clear difference | ambiguous |
| QFT-6 (ibm_fez 24 Nov) | r2 | X0 | -0.471 | -0.313 / -0.051 / +0.131 | 0.019 | ✗ ✓ ✓ | -0.411 (linear) | -0.313 | -0.276 | 0.030 | clearly better | good |
| QFT-6 (ibm_fez 24 Nov) | r2 | X1 | -0.556 | -0.496 / -0.360 / -0.202 | 0.020 | ✓ ✓ ✓ | -0.632 (exp) | -0.632 | -0.504 | 0.038 | no clear difference | ambiguous |
| QFT-6 (ibm_fez 24 Nov) | r2 | X2 | -0.383 | -0.316 / -0.346 / -0.262 | 0.018 | ✓ ✓ ✗ | -0.349 (linear) | -0.316 | -0.290 | 0.017 | clearly better | good |
| QFT-6 (ibm_fez 24 Nov) | r2 | X3 | -0.707 | -0.609 / -0.349 / -0.093 | 0.021 | ✓ ✓ ✗ | -0.955 (exp) | -0.609 | -0.568 | 0.124 | clearly worse | failure |
| QFT-6 (ibm_fez 24 Nov) | r2 | X4 | -0.000 | -0.075 / -0.151 / -0.237 | 0.019 | ✗ ✓ ✓ | -0.033 (linear) | -0.075 | -0.048 | 0.017 | no clear difference | ambiguous |
| QFT-6 (ibm_fez 24 Nov) | r2 | X5 | -1.000 | -0.915 / -0.779 / -0.578 | 0.019 | ✓ ✓ ✗ | -1.010 (exp) | -0.915 | -0.861 | 0.005 | clearly better | good |
| QFT-6 (ibm_fez 24 Nov) | r2 | Y0 | -0.882 | -0.804 / -0.621 / -0.328 | 0.019 | ✓ ✓ ✗ | -0.942 (exp) | -0.804 | -0.805 | 0.030 | no clear difference | ambiguous |
| QFT-6 (ibm_fez 24 Nov) | r2 | Y1 | +0.831 | +0.673 / +0.613 / +0.461 | 0.017 | ✓ ✓ ✗ | +0.758 (exp) | +0.673 | +0.710 | 0.037 | clearly better | good |
| QFT-6 (ibm_fez 24 Nov) | r2 | Y2 | -0.924 | -0.793 / -0.517 / -0.212 | 0.020 | ✓ ✓ ✗ | -0.943 (exp) | -0.793 | -0.813 | 0.010 | clearly better | good |
| QFT-6 (ibm_fez 24 Nov) | r2 | Y3 | +0.707 | +0.661 / +0.656 / +0.574 | 0.017 | ✓ ✓ ✗ | +0.698 (exp) | +0.661 | +0.635 | 0.004 | clearly better | good |
| QFT-6 (ibm_fez 24 Nov) | r2 | Y4 | -1.000 | -0.896 / -0.722 / -0.550 | 0.018 | ✓ ✓ ✓ | -0.982 (exp) | -0.982 | -0.876 | 0.009 | clearly better | good |
| QFT-6 (ibm_fez 24 Nov) | r2 | Y5 | +0.000 | -0.007 / -0.088 / -0.169 | 0.020 | ✗ ✓ ✓ | +0.034 (linear) | -0.007 | -0.014 | 0.017 | no clear difference | ambiguous |
| Heisenberg-4 (ibm_marrakesh 25 Nov) | 25N | M_stag | -0.646 | -0.535 / -0.381 / -0.233 | 0.008 | ✓ ✓ ✗ | -0.666 (exp) | -0.535 | -0.522 | 0.010 | clearly better | good |
| QPE-4 (ibm_marrakesh 25 Nov) | 25N | P(1011) | +1.000 | +0.827 / +0.631 / +0.440 | 0.008 | ✓ ✓ ✗ | +0.985 (exp) | +0.889 | +0.840 | 0.015 | clearly better | good |
| Heisenberg-4 (ibm_marrakesh 26 Nov) | 26N | M_stag | -0.646 | -0.543 / -0.113 / +0.041 | 0.008 | ✗ ✓ ✗ | -0.644 (linear) | -0.543 | -0.522 | 0.001 | clearly better | good |
| QPE-4 (ibm_marrakesh 26 Nov) | 26N | P(1011) | +1.000 | +0.660 / -0.008 / +0.158 | 0.006 | ✗ ✓ ✓ | +0.709 (linear) | +0.723 | +0.693 | 0.291 | clearly better | failure |
