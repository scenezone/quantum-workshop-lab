# Seed selection: gates vs ESP (FakeKingston, no mitigation)

Run `20261121-141701_selection` · 20 transpiler seeds · 4000 shots × 10 repeats. Raw counts and the method are in the run folder.

- **A (gates):** fewest two-qubit gates, then lowest depth.
- **B (ESP):** highest estimated success probability from calibration data.

Metric: TVD (lower is better) or, for QAOA, approximation ratio (higher is better); mean ± std over repeats. "Within spread" means the gap is smaller than the combined std.

> **Caveat:** on a fake backend the noise model is built from the same calibration data as ESP, so ESP picking better layouts here is partly circular. It shows the formula is consistent, not that it predicts real-hardware error. That has to be confirmed on hardware.

| Circuit | Opt | A: 2q / depth / ESP | B: 2q / depth / ESP | A metric | B metric | Verdict |
|---|---|---|---|---|---|---|
| Bell | 2 | 1 / 7 / 0.988 | 1 / 7 / 0.988 | 0.014 ± 0.002 | 0.014 ± 0.002 | same circuit |
| GHZ-3 | 2 | 2 / 10 / 0.973 | 2 / 10 / 0.973 | 0.026 ± 0.003 | 0.026 ± 0.003 | same circuit |
| GHZ-5 | 2 | 4 / 16 / 0.961 | 4 / 16 / 0.961 | 0.040 ± 0.003 | 0.040 ± 0.003 | same circuit |
| Grover-2 | 2 | 2 / 10 / 0.986 | 2 / 10 / 0.986 | 0.016 ± 0.002 | 0.016 ± 0.002 | same circuit |
| Grover-3 | 2 | 37 / 133 / 0.907 | 37 / 133 / 0.907 | 0.094 ± 0.006 | 0.094 ± 0.006 | same circuit |
| QFT-3 | 2 | 9 / 32 / 0.965 | 9 / 32 / 0.965 | 0.037 ± 0.003 | 0.037 ± 0.003 | same circuit |
| QFT-4 | 2 | 17 / 55 / 0.937 | 17 / 55 / 0.937 | 0.064 ± 0.003 | 0.064 ± 0.003 | same circuit |
| BV-4 | 2 | 3 / 9 / 0.971 | 3 / 9 / 0.971 | 0.030 ± 0.003 | 0.030 ± 0.003 | same circuit |
| QAOA-3 | 2 | 7 / 32 / 0.970 | 7 / 32 / 0.970 | 0.986 ± 0.002 | 0.986 ± 0.002 | same circuit |
| QAOA-4 | 2 | 11 / 45 / 0.947 | 12 / 40 / 0.947 | 0.738 ± 0.003 | 0.738 ± 0.004 | no difference (within spread) |
| GHZ-7 | 2 | 6 / 22 / 0.941 | 6 / 22 / 0.941 | 0.058 ± 0.004 | 0.058 ± 0.004 | same circuit |
| Grover-4 | 2 | 73 / 287 / 0.839 | 73 / 287 / 0.839 | 0.157 ± 0.005 | 0.157 ± 0.005 | same circuit |
| QFT-5 | 2 | 29 / 99 / 0.899 | 30 / 85 / 0.906 | 0.104 ± 0.004 | 0.092 ± 0.005 | B (ESP) better |
| QAOA-4-p2 | 2 | 25 / 90 / 0.921 | 25 / 90 / 0.921 | 0.957 ± 0.002 | 0.957 ± 0.002 | same circuit |

## Tally

| Verdict | Circuits |
|---|---|
| same circuit | 12 |
| no difference (within spread) | 1 |
| B (ESP) better | 1 |
