# Seed selection: gates vs ESP (FakeSherbrooke, no mitigation)

Run `20261121-142309_selection` · 20 transpiler seeds · 4000 shots × 10 repeats. Raw counts and the method are in the run folder.

- **A (gates):** fewest two-qubit gates, then lowest depth.
- **B (ESP):** highest estimated success probability from calibration data.

Metric: TVD (lower is better) or, for QAOA, approximation ratio (higher is better); mean ± std over repeats. "Within spread" means the gap is smaller than the combined std.

> **Caveat:** on a fake backend the noise model is built from the same calibration data as ESP, so ESP picking better layouts here is partly circular. It shows the formula is consistent, not that it predicts real-hardware error. That has to be confirmed on hardware.

| Circuit | Opt | A: 2q / depth / ESP | B: 2q / depth / ESP | A metric | B metric | Verdict |
|---|---|---|---|---|---|---|
| Bell | 1 | 1 / 8 / 0.956 | 1 / 8 / 0.956 | 0.041 ± 0.004 | 0.041 ± 0.004 | same circuit |
| Bell | 2 | 1 / 6 / 0.982 | 1 / 6 / 0.982 | 0.018 ± 0.003 | 0.018 ± 0.003 | same circuit |
| Bell | 3 | 1 / 6 / 0.982 | 1 / 6 / 0.982 | 0.016 ± 0.002 | 0.016 ± 0.002 | same circuit |
| GHZ-3 | 1 | 2 / 9 / 0.927 | 2 / 9 / 0.927 | 0.069 ± 0.005 | 0.069 ± 0.005 | same circuit |
| GHZ-3 | 2 | 2 / 10 / 0.970 | 2 / 10 / 0.970 | 0.030 ± 0.003 | 0.030 ± 0.003 | same circuit |
| GHZ-3 | 3 | 2 / 9 / 0.970 | 2 / 9 / 0.970 | 0.029 ± 0.002 | 0.029 ± 0.002 | same circuit |
| GHZ-5 | 1 | 4 / 17 / 0.881 | 4 / 17 / 0.881 | 0.114 ± 0.005 | 0.114 ± 0.005 | same circuit |
| GHZ-5 | 2 | 4 / 24 / 0.931 | 4 / 24 / 0.931 | 0.070 ± 0.003 | 0.070 ± 0.003 | same circuit |
| GHZ-5 | 3 | 4 / 23 / 0.931 | 4 / 23 / 0.931 | 0.070 ± 0.005 | 0.070 ± 0.005 | same circuit |
| Grover-2 | 1 | 2 / 12 / 0.949 | 2 / 12 / 0.949 | 0.052 ± 0.003 | 0.052 ± 0.003 | same circuit |
| Grover-2 | 2 | 2 / 16 / 0.976 | 2 / 16 / 0.976 | 0.026 ± 0.002 | 0.026 ± 0.002 | same circuit |
| Grover-2 | 3 | 2 / 16 / 0.977 | 2 / 16 / 0.977 | 0.025 ± 0.003 | 0.025 ± 0.003 | same circuit |
| Grover-3 | 1 | 45 / 158 / 0.748 | 45 / 158 / 0.748 | 0.236 ± 0.007 | 0.236 ± 0.007 | same circuit |
| Grover-3 | 2 | 37 / 173 / 0.782 | 37 / 173 / 0.782 | 0.210 ± 0.007 | 0.210 ± 0.007 | same circuit |
| Grover-3 | 3 | 37 / 173 / 0.796 | 37 / 173 / 0.796 | 0.197 ± 0.006 | 0.197 ± 0.006 | same circuit |
| QFT-3 | 1 | 12 / 51 / 0.918 | 12 / 51 / 0.918 | 0.083 ± 0.005 | 0.083 ± 0.005 | same circuit |
| QFT-3 | 2 | 9 / 49 / 0.931 | 9 / 51 / 0.932 | 0.071 ± 0.005 | 0.069 ± 0.004 | no difference (within spread) |
| QFT-3 | 3 | 9 / 49 / 0.931 | 9 / 51 / 0.932 | 0.070 ± 0.007 | 0.068 ± 0.005 | no difference (within spread) |
| QFT-4 | 1 | 27 / 89 / 0.828 | 27 / 89 / 0.828 | 0.181 ± 0.006 | 0.181 ± 0.006 | same circuit |
| QFT-4 | 2 | 17 / 80 / 0.876 | 17 / 80 / 0.876 | 0.126 ± 0.003 | 0.126 ± 0.003 | same circuit |
| QFT-4 | 3 | 17 / 79 / 0.877 | 17 / 79 / 0.877 | 0.126 ± 0.006 | 0.126 ± 0.006 | same circuit |
| BV-4 | 1 | 3 / 16 / 0.947 | 3 / 16 / 0.947 | 0.049 ± 0.004 | 0.049 ± 0.004 | same circuit |
| BV-4 | 2 | 3 / 18 / 0.947 | 3 / 18 / 0.947 | 0.048 ± 0.006 | 0.048 ± 0.006 | same circuit |
| BV-4 | 3 | 3 / 18 / 0.947 | 3 / 18 / 0.947 | 0.050 ± 0.004 | 0.050 ± 0.004 | same circuit |
| QAOA-3 | 1 | 9 / 38 / 0.932 | 9 / 39 / 0.933 | 0.979 ± 0.002 | 0.977 ± 0.002 | no difference (within spread) |
| QAOA-3 | 2 | 7 / 36 / 0.941 | 7 / 36 / 0.941 | 0.977 ± 0.002 | 0.977 ± 0.002 | same circuit |
| QAOA-3 | 3 | 7 / 36 / 0.941 | 7 / 36 / 0.941 | 0.980 ± 0.002 | 0.980 ± 0.002 | same circuit |
| QAOA-4 | 1 | 11 / 44 / 0.884 | 14 / 47 / 0.894 | 0.717 ± 0.003 | 0.730 ± 0.004 | B (ESP) better |
| QAOA-4 | 2 | 11 / 68 / 0.884 | 12 / 50 / 0.905 | 0.717 ± 0.005 | 0.732 ± 0.005 | B (ESP) better |
| QAOA-4 | 3 | 11 / 68 / 0.884 | 12 / 50 / 0.905 | 0.719 ± 0.004 | 0.731 ± 0.006 | B (ESP) better |
| GHZ-7 | 1 | 6 / 23 / 0.000 | 6 / 23 / 0.000 | 0.811 ± 0.008 | 0.811 ± 0.008 | same circuit |
| GHZ-7 | 2 | 6 / 36 / 0.891 | 6 / 36 / 0.891 | 0.107 ± 0.005 | 0.107 ± 0.005 | same circuit |
| GHZ-7 | 3 | 6 / 36 / 0.891 | 6 / 36 / 0.891 | 0.109 ± 0.006 | 0.109 ± 0.006 | same circuit |
| Grover-4 | 1 | 89 / 345 / 0.487 | 89 / 345 / 0.489 | 0.548 ± 0.008 | 0.546 ± 0.006 | no difference (within spread) |
| Grover-4 | 2 | 73 / 389 / 0.562 | 73 / 389 / 0.562 | 0.506 ± 0.005 | 0.506 ± 0.005 | same circuit |
| Grover-4 | 3 | 73 / 389 / 0.650 | 73 / 389 / 0.650 | 0.331 ± 0.009 | 0.331 ± 0.009 | same circuit |
| QFT-5 | 1 | 41 / 135 / 0.698 | 41 / 139 / 0.713 | 0.307 ± 0.006 | 0.347 ± 0.005 | A (gates) better |
| QFT-5 | 2 | 30 / 142 / 0.750 | 30 / 162 / 0.750 | 0.246 ± 0.007 | 0.236 ± 0.010 | no difference (within spread) |
| QFT-5 | 3 | 30 / 142 / 0.784 | 30 / 158 / 0.785 | 0.219 ± 0.009 | 0.217 ± 0.007 | no difference (within spread) |
| QAOA-4-p2 | 1 | 25 / 96 / 0.797 | 25 / 96 / 0.797 | 0.888 ± 0.004 | 0.888 ± 0.004 | same circuit |
| QAOA-4-p2 | 2 | 25 / 131 / 0.795 | 28 / 106 / 0.820 | 0.879 ± 0.004 | 0.905 ± 0.004 | B (ESP) better |
| QAOA-4-p2 | 3 | 25 / 131 / 0.796 | 28 / 106 / 0.820 | 0.880 ± 0.004 | 0.906 ± 0.004 | B (ESP) better |

## Tally

| Verdict | Circuits |
|---|---|
| same circuit | 30 |
| no difference (within spread) | 6 |
| B (ESP) better | 5 |
| A (gates) better | 1 |
