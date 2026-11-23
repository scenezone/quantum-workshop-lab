# Seed selection: gates vs ESP (FakeKingston, no mitigation)

Run `20261121-142309_selection` · 20 transpiler seeds · 4000 shots × 10 repeats. Raw counts and the method are in the run folder.

- **A (gates):** fewest two-qubit gates, then lowest depth.
- **B (ESP):** highest estimated success probability from calibration data.

Metric: TVD (lower is better) or, for QAOA, approximation ratio (higher is better); mean ± std over repeats. "Within spread" means the gap is smaller than the combined std.

> **Caveat:** on a fake backend the noise model is built from the same calibration data as ESP, so ESP picking better layouts here is partly circular. It shows the formula is consistent, not that it predicts real-hardware error. That has to be confirmed on hardware.

| Circuit | Opt | A: 2q / depth / ESP | B: 2q / depth / ESP | A metric | B metric | Verdict |
|---|---|---|---|---|---|---|
| Bell | 1 | 1 / 8 / 0.823 | 1 / 8 / 0.823 | 0.176 ± 0.009 | 0.176 ± 0.009 | same circuit |
| Bell | 2 | 1 / 7 / 0.988 | 1 / 7 / 0.988 | 0.013 ± 0.004 | 0.013 ± 0.004 | same circuit |
| Bell | 3 | 1 / 7 / 0.988 | 1 / 7 / 0.988 | 0.013 ± 0.003 | 0.013 ± 0.003 | same circuit |
| GHZ-3 | 1 | 2 / 12 / 0.815 | 2 / 12 / 0.815 | 0.184 ± 0.008 | 0.184 ± 0.008 | same circuit |
| GHZ-3 | 2 | 2 / 10 / 0.973 | 2 / 10 / 0.973 | 0.026 ± 0.003 | 0.026 ± 0.003 | same circuit |
| GHZ-3 | 3 | 2 / 10 / 0.981 | 2 / 10 / 0.981 | 0.020 ± 0.005 | 0.020 ± 0.005 | same circuit |
| GHZ-5 | 1 | 4 / 20 / 0.794 | 4 / 20 / 0.794 | 0.206 ± 0.008 | 0.206 ± 0.008 | same circuit |
| GHZ-5 | 2 | 4 / 16 / 0.961 | 4 / 16 / 0.961 | 0.039 ± 0.003 | 0.039 ± 0.003 | same circuit |
| GHZ-5 | 3 | 4 / 16 / 0.961 | 4 / 16 / 0.961 | 0.037 ± 0.004 | 0.037 ± 0.004 | same circuit |
| Grover-2 | 1 | 2 / 12 / 0.821 | 2 / 12 / 0.821 | 0.177 ± 0.006 | 0.177 ± 0.006 | same circuit |
| Grover-2 | 2 | 2 / 10 / 0.986 | 2 / 10 / 0.986 | 0.016 ± 0.002 | 0.016 ± 0.002 | same circuit |
| Grover-2 | 3 | 2 / 10 / 0.986 | 2 / 10 / 0.986 | 0.014 ± 0.002 | 0.014 ± 0.002 | same circuit |
| Grover-3 | 1 | 45 / 169 / 0.896 | 45 / 169 / 0.896 | 0.106 ± 0.006 | 0.106 ± 0.006 | same circuit |
| Grover-3 | 2 | 37 / 133 / 0.907 | 37 / 133 / 0.907 | 0.093 ± 0.005 | 0.093 ± 0.005 | same circuit |
| Grover-3 | 3 | 37 / 133 / 0.919 | 37 / 133 / 0.919 | 0.080 ± 0.009 | 0.080 ± 0.009 | same circuit |
| QFT-3 | 1 | 12 / 49 / 0.958 | 12 / 49 / 0.958 | 0.045 ± 0.003 | 0.045 ± 0.003 | same circuit |
| QFT-3 | 2 | 9 / 32 / 0.965 | 9 / 32 / 0.965 | 0.036 ± 0.003 | 0.036 ± 0.003 | same circuit |
| QFT-3 | 3 | 7 / 25 / 0.970 | 7 / 25 / 0.970 | 0.032 ± 0.002 | 0.032 ± 0.002 | same circuit |
| QFT-4 | 1 | 27 / 80 / 0.920 | 27 / 80 / 0.920 | 0.087 ± 0.006 | 0.087 ± 0.006 | same circuit |
| QFT-4 | 2 | 17 / 55 / 0.937 | 17 / 55 / 0.937 | 0.065 ± 0.003 | 0.065 ± 0.003 | same circuit |
| QFT-4 | 3 | 14 / 44 / 0.947 | 14 / 44 / 0.947 | 0.055 ± 0.002 | 0.055 ± 0.002 | same circuit |
| BV-4 | 1 | 3 / 10 / 0.971 | 3 / 10 / 0.971 | 0.027 ± 0.002 | 0.027 ± 0.002 | same circuit |
| BV-4 | 2 | 3 / 9 / 0.971 | 3 / 9 / 0.971 | 0.028 ± 0.001 | 0.028 ± 0.001 | same circuit |
| BV-4 | 3 | 3 / 9 / 0.978 | 3 / 9 / 0.978 | 0.021 ± 0.003 | 0.021 ± 0.003 | same circuit |
| QAOA-3 | 1 | 9 / 39 / 0.962 | 9 / 46 / 0.967 | 0.984 ± 0.001 | 0.984 ± 0.003 | no difference (within spread) |
| QAOA-3 | 2 | 7 / 32 / 0.970 | 7 / 32 / 0.970 | 0.986 ± 0.002 | 0.986 ± 0.002 | same circuit |
| QAOA-3 | 3 | 7 / 32 / 0.970 | 7 / 32 / 0.970 | 0.986 ± 0.002 | 0.986 ± 0.002 | same circuit |
| QAOA-4 | 1 | 11 / 56 / 0.947 | 11 / 56 / 0.947 | 0.736 ± 0.005 | 0.736 ± 0.005 | same circuit |
| QAOA-4 | 2 | 11 / 45 / 0.947 | 12 / 40 / 0.947 | 0.736 ± 0.003 | 0.735 ± 0.002 | no difference (within spread) |
| QAOA-4 | 3 | 11 / 45 / 0.952 | 11 / 45 / 0.952 | 0.741 ± 0.004 | 0.741 ± 0.004 | same circuit |
| GHZ-7 | 1 | 6 / 28 / 0.772 | 6 / 28 / 0.772 | 0.229 ± 0.009 | 0.229 ± 0.009 | same circuit |
| GHZ-7 | 2 | 6 / 22 / 0.941 | 6 / 22 / 0.941 | 0.057 ± 0.003 | 0.057 ± 0.003 | same circuit |
| GHZ-7 | 3 | 6 / 22 / 0.941 | 6 / 22 / 0.941 | 0.055 ± 0.004 | 0.055 ± 0.004 | same circuit |
| Grover-4 | 1 | 89 / 396 / 0.815 | 89 / 396 / 0.815 | 0.184 ± 0.007 | 0.184 ± 0.007 | same circuit |
| Grover-4 | 2 | 73 / 287 / 0.839 | 73 / 287 / 0.839 | 0.157 ± 0.010 | 0.157 ± 0.010 | same circuit |
| Grover-4 | 3 | 73 / 287 / 0.844 | 73 / 287 / 0.844 | 0.156 ± 0.006 | 0.156 ± 0.006 | same circuit |
| QFT-5 | 1 | 41 / 120 / 0.885 | 41 / 120 / 0.885 | 0.116 ± 0.005 | 0.116 ± 0.005 | same circuit |
| QFT-5 | 2 | 29 / 99 / 0.899 | 30 / 85 / 0.906 | 0.103 ± 0.004 | 0.097 ± 0.004 | no difference (within spread) |
| QFT-5 | 3 | 28 / 77 / 0.909 | 28 / 77 / 0.909 | 0.094 ± 0.003 | 0.094 ± 0.003 | same circuit |
| QAOA-4-p2 | 1 | 25 / 116 / 0.921 | 25 / 116 / 0.921 | 0.958 ± 0.003 | 0.958 ± 0.003 | same circuit |
| QAOA-4-p2 | 2 | 25 / 90 / 0.921 | 25 / 90 / 0.921 | 0.957 ± 0.002 | 0.957 ± 0.002 | same circuit |
| QAOA-4-p2 | 3 | 25 / 90 / 0.926 | 25 / 90 / 0.926 | 0.961 ± 0.003 | 0.961 ± 0.003 | same circuit |

## Tally

| Verdict | Circuits |
|---|---|
| same circuit | 39 |
| no difference (within spread) | 3 |
