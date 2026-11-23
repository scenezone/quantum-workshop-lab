# Baseline v2: FakeKingston (no error mitigation)

Qiskit Aer with the `FakeKingston` noise model · 4000 shots per run · 20 transpiler seeds (1-20), best kept · 10 simulator repeats per configuration (seed 1234+i) · values are mean ± std over repeats.

Best-of-seeds rule: fewest two-qubit gates, then lowest depth. Selection uses compile metrics only, never the measured error.

## Counts circuits (optimization level 2)

| Circuit | Qubits | Logical CX | 2q gates (best) | 2q over seeds | Depth | TVD | Hellinger F | Shot-noise TVD |
|---|---|---|---|---|---|---|---|---|
| Bell | 2 | 1 | 1 | 1-1 | 7 | 0.015 ± 0.004 | 0.988 ± 0.002 | 0.006 |
| GHZ-3 | 3 | 2 | 2 | 2-2 | 10 | 0.027 ± 0.002 | 0.974 ± 0.002 | 0.006 |
| GHZ-5 | 5 | 4 | 4 | 4-4 | 16 | 0.037 ± 0.004 | 0.963 ± 0.004 | 0.006 |
| Grover-2 | 2 | 2 | 2 | 2-2 | 10 | 0.015 ± 0.001 | 0.985 ± 0.001 | 0.000 |
| Grover-3 | 3 | 24 | 37 | 37-39 | 133 | 0.092 ± 0.004 | 0.974 ± 0.002 | 0.006 |
| QFT-3 | 3 | 9 | 9 | 9-9 | 32 | 0.037 ± 0.003 | 0.963 ± 0.003 | 0.000 |
| QFT-4 | 4 | 18 | 17 | 17-19 | 55 | 0.065 ± 0.004 | 0.934 ± 0.004 | 0.000 |
| BV-4 | 5 | 3 | 3 | 3-3 | 9 | 0.029 ± 0.002 | 0.971 ± 0.002 | 0.000 |
| GHZ-7 | 7 | 6 | 6 | 6-6 | 22 | 0.057 ± 0.004 | 0.943 ± 0.004 | 0.006 |
| Grover-4 | 4 | 56 | 73 | 73-109 | 287 | 0.155 ± 0.006 | 0.953 ± 0.003 | 0.009 |
| QFT-5 | 5 | 26 | 29 | 29-31 | 99 | 0.101 ± 0.004 | 0.899 ± 0.004 | 0.000 |

## QAOA (optimization level 2)

| Circuit | Qubits | 2q gates (best) | 2q over seeds | Depth | Approx. ratio (noisy) | Approx. ratio (ideal) | Problem |
|---|---|---|---|---|---|---|---|
| QAOA-3 | 3 | 7 | 7-9 | 32 | 0.986 ± 0.002 | 0.994 | MaxCut triangle, p=1, max cut 2, gamma1=2.880 beta1=0.327 |
| QAOA-4 | 4 | 11 | 11-12 | 45 | 0.738 ± 0.004 | 0.750 | MaxCut 4-ring, p=1, max cut 4, gamma1=2.749 beta1=0.393 |
| QAOA-4-p2 | 4 | 25 | 25-28 | 90 | 0.957 ± 0.002 | 1.000 | MaxCut 4-ring, p=2, max cut 4, gamma1=2.689 beta1=0.559, gamma2=2.582 beta2=0.452 |

## Effect of optimization level

Counts circuits only for gates, depth and TVD (QAOA is scored separately). "Median-seed" is what a single random seed typically gives; "best" is best of all seeds.

| Opt level | Total 2q (best) | Total 2q (median seed) | Total depth | Mean TVD | Median TVD | Mean QAOA ratio |
|---|---|---|---|---|---|---|
| 0 | 331 | 352.0 | 1371 | 0.220 | 0.216 | 0.839 |
| 1 | 232 | 269.5 | 904 | 0.138 | 0.172 | 0.893 |
| 2 | 183 | 189.0 | 680 | 0.057 | 0.037 | 0.894 |
| 3 | 177 | 186.0 | 640 | 0.053 | 0.037 | 0.896 |

## Per-circuit change

Primary metric is TVD (lower is better) or, for QAOA, approximation ratio (higher is better). Percentages are relative changes.

| Circuit | Metric | 2q gates L0 → L2 | Depth L0 → L2 | Metric L0 → L1 → L2 → L3 | Metric change L0 → L2 | 2q L2 / L3 | Metric L2 − L3 |
|---|---|---|---|---|---|---|---|
| Bell | TVD | 1 → 1 (+0%) | 8 → 7 (-12%) | 0.172 → 0.172 → 0.015 → 0.014 | -91% | 1 / 1 | +0.001 |
| GHZ-3 | TVD | 2 → 2 (+0%) | 12 → 10 (-17%) | 0.183 → 0.183 → 0.027 → 0.020 | -85% | 2 / 2 | +0.007 |
| GHZ-5 | TVD | 4 → 4 (+0%) | 20 → 16 (-20%) | 0.204 → 0.204 → 0.037 → 0.037 | -82% | 4 / 4 | -0.000 |
| Grover-2 | TVD | 2 → 2 (+0%) | 38 → 10 (-74%) | 0.177 → 0.175 → 0.015 → 0.015 | -91% | 2 / 2 | +0.000 |
| Grover-3 | TVD | 48 → 37 (-23%) | 307 → 133 (-57%) | 0.227 → 0.107 → 0.092 → 0.083 | -59% | 37 / 37 | +0.010 |
| QFT-3 | TVD | 15 → 9 (-40%) | 72 → 32 (-56%) | 0.200 → 0.043 → 0.037 → 0.031 | -82% | 9 / 7 | +0.006 |
| QFT-4 | TVD | 36 → 17 (-53%) | 116 → 55 (-53%) | 0.228 → 0.087 → 0.065 → 0.055 | -71% | 17 / 14 | +0.010 |
| BV-4 | TVD | 18 → 3 (-83%) | 39 → 9 (-77%) | 0.216 → 0.029 → 0.029 → 0.021 | -87% | 3 / 3 | +0.007 |
| QAOA-3 | ratio | 9 → 7 (-22%) | 56 → 32 (-43%) | 0.932 → 0.983 → 0.986 → 0.986 | +6% | 7 / 7 | +0.000 |
| QAOA-4 | ratio | 14 → 11 (-21%) | 68 → 45 (-34%) | 0.701 → 0.738 → 0.738 → 0.740 | +5% | 11 / 11 | -0.002 |
| GHZ-7 | TVD | 6 → 6 (+0%) | 28 → 22 (-21%) | 0.229 → 0.229 → 0.057 → 0.057 | -75% | 6 / 6 | +0.000 |
| Grover-4 | TVD | 137 → 73 (-47%) | 565 → 287 (-49%) | 0.319 → 0.180 → 0.155 → 0.156 | -52% | 73 / 73 | -0.002 |
| QFT-5 | TVD | 62 → 29 (-53%) | 166 → 99 (-40%) | 0.270 → 0.114 → 0.101 → 0.091 | -63% | 29 / 28 | +0.010 |
| QAOA-4-p2 | ratio | 31 → 25 (-19%) | 127 → 90 (-29%) | 0.885 → 0.957 → 0.957 → 0.961 | +8% | 25 / 25 | -0.004 |

## Level 2 vs level 3: is the difference real?

"Outside spread" means the gap is larger than the combined std of the two (sqrt(std2² + std3²)). The std only covers simulator repeats, not seed-to-seed layout variation. When both levels use the same number of two-qubit gates, any gap comes from which physical qubits were picked, not from level 3's extra optimization.

| Circuit | L2 | L3 | L2 − L3 | Combined std | 2q L2 / L3 | Verdict |
|---|---|---|---|---|---|---|
| Bell | 0.015 ± 0.004 | 0.014 ± 0.005 | +0.001 | 0.006 | 1 / 1 | no difference (within spread) |
| GHZ-3 | 0.027 ± 0.002 | 0.020 ± 0.004 | +0.007 | 0.004 | 2 / 2 | L3 better: same 2q gates, different qubits |
| GHZ-5 | 0.037 ± 0.004 | 0.037 ± 0.005 | -0.000 | 0.006 | 4 / 4 | no difference (within spread) |
| Grover-2 | 0.015 ± 0.001 | 0.015 ± 0.001 | +0.000 | 0.002 | 2 / 2 | no difference (within spread) |
| Grover-3 | 0.092 ± 0.004 | 0.083 ± 0.006 | +0.010 | 0.007 | 37 / 37 | L3 better: same 2q gates, different qubits |
| QFT-3 | 0.037 ± 0.003 | 0.031 ± 0.003 | +0.006 | 0.004 | 9 / 7 | L3 better: fewer 2q gates |
| QFT-4 | 0.065 ± 0.004 | 0.055 ± 0.003 | +0.010 | 0.005 | 17 / 14 | L3 better: fewer 2q gates |
| BV-4 | 0.029 ± 0.002 | 0.021 ± 0.001 | +0.007 | 0.003 | 3 / 3 | L3 better: same 2q gates, different qubits |
| QAOA-3 | 0.986 ± 0.002 | 0.986 ± 0.002 | +0.000 | 0.003 | 7 / 7 | no difference (within spread) |
| QAOA-4 | 0.738 ± 0.004 | 0.740 ± 0.004 | -0.002 | 0.006 | 11 / 11 | no difference (within spread) |
| GHZ-7 | 0.057 ± 0.004 | 0.057 ± 0.004 | +0.000 | 0.006 | 6 / 6 | no difference (within spread) |
| Grover-4 | 0.155 ± 0.006 | 0.156 ± 0.005 | -0.002 | 0.008 | 73 / 73 | no difference (within spread) |
| QFT-5 | 0.101 ± 0.004 | 0.091 ± 0.005 | +0.010 | 0.006 | 29 / 28 | L3 better: fewer 2q gates |
| QAOA-4-p2 | 0.957 ± 0.002 | 0.961 ± 0.002 | -0.004 | 0.003 | 25 / 25 | L3 better: same 2q gates, different qubits |

## All levels

| Circuit | Opt | Best seed | 2q gates | 2q min / median / max over seeds | Depth | Primary metric | Hellinger F | Physical qubits | Transpile s (all seeds) |
|---|---|---|---|---|---|---|---|---|---|
| Bell | 0 | 1 | 1 | 1 / 1.0 / 1 | 8 | TVD 0.172 ± 0.006 | 0.827 | 0 1 | 0.1 |
| Bell | 1 | 1 | 1 | 1 / 1.0 / 1 | 8 | TVD 0.172 ± 0.006 | 0.827 | 0 1 | 0.2 |
| Bell | 2 | 1 | 1 | 1 / 1.0 / 1 | 7 | TVD 0.015 ± 0.004 | 0.988 | 21 20 | 0.2 |
| Bell | 3 | 1 | 1 | 1 / 1.0 / 1 | 7 | TVD 0.014 ± 0.005 | 0.989 | 20 21 | 0.2 |
| GHZ-3 | 0 | 1 | 2 | 2 / 2.0 / 2 | 12 | TVD 0.183 ± 0.008 | 0.817 | 0 1 2 | 0.1 |
| GHZ-3 | 1 | 1 | 2 | 2 / 2.0 / 2 | 12 | TVD 0.183 ± 0.008 | 0.817 | 0 1 2 | 0.2 |
| GHZ-3 | 2 | 1 | 2 | 2 / 2.0 / 2 | 10 | TVD 0.027 ± 0.002 | 0.974 | 110 109 108 | 0.2 |
| GHZ-3 | 3 | 1 | 2 | 2 / 2.0 / 2 | 10 | TVD 0.020 ± 0.004 | 0.981 | 117 105 104 | 0.3 |
| GHZ-5 | 0 | 1 | 4 | 4 / 4.0 / 4 | 20 | TVD 0.204 ± 0.008 | 0.796 | 0 1 2 3 4 | 0.1 |
| GHZ-5 | 1 | 1 | 4 | 4 / 4.0 / 4 | 20 | TVD 0.204 ± 0.008 | 0.796 | 0 1 2 3 4 | 0.2 |
| GHZ-5 | 2 | 1 | 4 | 4 / 4.0 / 4 | 16 | TVD 0.037 ± 0.004 | 0.963 | 148 149 150 151 152 | 0.3 |
| GHZ-5 | 3 | 1 | 4 | 4 / 4.0 / 4 | 16 | TVD 0.037 ± 0.005 | 0.963 | 152 151 150 149 148 | 0.3 |
| Grover-2 | 0 | 1 | 2 | 2 / 2.0 / 2 | 38 | TVD 0.177 ± 0.006 | 0.823 | 0 1 | 0.4 |
| Grover-2 | 1 | 1 | 2 | 2 / 2.0 / 2 | 12 | TVD 0.175 ± 0.006 | 0.825 | 0 1 | 0.2 |
| Grover-2 | 2 | 1 | 2 | 2 / 2.0 / 2 | 10 | TVD 0.015 ± 0.001 | 0.985 | 21 20 | 0.3 |
| Grover-2 | 3 | 1 | 2 | 2 / 2.0 / 2 | 10 | TVD 0.015 ± 0.001 | 0.985 | 21 20 | 0.3 |
| Grover-3 | 0 | 14 | 48 | 48 / 51.0 / 54 | 307 | TVD 0.227 ± 0.005 | 0.874 | 0 1 2 | 0.3 |
| Grover-3 | 1 | 1 | 45 | 45 / 45.0 / 45 | 169 | TVD 0.107 ± 0.005 | 0.968 | 21 20 36 | 0.6 |
| Grover-3 | 2 | 1 | 37 | 37 / 39.0 / 39 | 133 | TVD 0.092 ± 0.004 | 0.974 | 21 20 36 | 0.4 |
| Grover-3 | 3 | 1 | 37 | 37 / 39.0 / 39 | 133 | TVD 0.083 ± 0.006 | 0.978 | 143 142 144 | 0.4 |
| QFT-3 | 0 | 2 | 15 | 15 / 15.0 / 18 | 72 | TVD 0.200 ± 0.005 | 0.800 | 2 0 1 | 0.2 |
| QFT-3 | 1 | 1 | 12 | 12 / 12.0 / 12 | 49 | TVD 0.043 ± 0.003 | 0.957 | 108 110 109 | 0.3 |
| QFT-3 | 2 | 1 | 9 | 9 / 9.0 / 9 | 32 | TVD 0.037 ± 0.003 | 0.963 | 117 104 105 | 0.6 |
| QFT-3 | 3 | 1 | 7 | 7 / 7.0 / 9 | 25 | TVD 0.031 ± 0.003 | 0.969 | 104 117 105 | 0.4 |
| QFT-4 | 0 | 2 | 36 | 36 / 36.0 / 39 | 116 | TVD 0.228 ± 0.007 | 0.772 | 3 0 2 1 | 0.2 |
| QFT-4 | 1 | 1 | 27 | 27 / 27.0 / 27 | 80 | TVD 0.087 ± 0.004 | 0.913 | 88 91 89 90 | 0.3 |
| QFT-4 | 2 | 7 | 17 | 17 / 18.0 / 19 | 55 | TVD 0.065 ± 0.004 | 0.934 | 149 152 150 151 | 0.3 |
| QFT-4 | 3 | 9 | 14 | 14 / 17.0 / 19 | 44 | TVD 0.055 ± 0.003 | 0.945 | 138 152 150 151 | 0.6 |
| BV-4 | 0 | 3 | 18 | 18 / 18.0 / 21 | 39 | TVD 0.216 ± 0.008 | 0.784 | 1 2 0 4 | 0.2 |
| BV-4 | 1 | 1 | 3 | 3 / 3.0 / 3 | 10 | TVD 0.029 ± 0.002 | 0.971 | 108 110 148 118 | 0.2 |
| BV-4 | 2 | 1 | 3 | 3 / 3.0 / 3 | 9 | TVD 0.029 ± 0.002 | 0.971 | 108 110 148 118 | 0.3 |
| BV-4 | 3 | 1 | 3 | 3 / 3.0 / 3 | 9 | TVD 0.021 ± 0.001 | 0.979 | 38 48 148 50 | 0.3 |
| QAOA-3 | 0 | 1 | 9 | 9 / 9.0 / 9 | 56 | ratio 0.932 ± 0.004 | 0.963 | 1 0 2 | 0.5 |
| QAOA-3 | 1 | 1 | 9 | 9 / 9.0 / 9 | 39 | ratio 0.983 ± 0.002 | 0.997 | 108 110 109 | 0.3 |
| QAOA-3 | 2 | 4 | 7 | 7 / 9.0 / 9 | 32 | ratio 0.986 ± 0.002 | 0.998 | 117 104 105 | 0.3 |
| QAOA-3 | 3 | 4 | 7 | 7 / 9.0 / 9 | 32 | ratio 0.986 ± 0.002 | 0.998 | 117 104 105 | 0.3 |
| QAOA-4 | 0 | 1 | 14 | 14 / 14.0 / 14 | 68 | ratio 0.701 ± 0.004 | 0.958 | 1 0 3 2 | 0.2 |
| QAOA-4 | 1 | 3 | 11 | 11 / 14.0 / 14 | 56 | ratio 0.738 ± 0.004 | 0.997 | 108 118 110 109 | 0.5 |
| QAOA-4 | 2 | 2 | 11 | 11 / 11.0 / 12 | 45 | ratio 0.738 ± 0.004 | 0.997 | 108 118 110 109 | 0.5 |
| QAOA-4 | 3 | 2 | 11 | 11 / 11.0 / 12 | 45 | ratio 0.740 ± 0.004 | 0.997 | 152 150 138 151 | 0.7 |
| GHZ-7 | 0 | 1 | 6 | 6 / 6.0 / 6 | 28 | TVD 0.229 ± 0.005 | 0.771 | 0 1 2 3 4 5 6 | 0.2 |
| GHZ-7 | 1 | 1 | 6 | 6 / 6.0 / 6 | 28 | TVD 0.229 ± 0.005 | 0.771 | 0 1 2 3 4 5 6 | 0.3 |
| GHZ-7 | 2 | 1 | 6 | 6 / 6.0 / 6 | 22 | TVD 0.057 ± 0.004 | 0.943 | 137 147 148 149 150 151 152 | 0.7 |
| GHZ-7 | 3 | 1 | 6 | 6 / 6.0 / 6 | 22 | TVD 0.057 ± 0.004 | 0.943 | 137 147 148 149 150 151 152 | 0.5 |
| Grover-4 | 0 | 15 | 137 | 137 / 152.0 / 167 | 565 | TVD 0.319 ± 0.006 | 0.833 | 1 3 0 2 | 0.7 |
| Grover-4 | 1 | 4 | 89 | 89 / 125.0 / 125 | 396 | TVD 0.180 ± 0.007 | 0.941 | 138 150 152 151 | 0.7 |
| Grover-4 | 2 | 3 | 73 | 73 / 75.0 / 109 | 287 | TVD 0.155 ± 0.006 | 0.953 | 138 150 152 151 | 0.8 |
| Grover-4 | 3 | 3 | 73 | 73 / 75.0 / 109 | 287 | TVD 0.156 ± 0.005 | 0.952 | 136 144 142 143 | 1.2 |
| QFT-5 | 0 | 18 | 62 | 62 / 65.0 / 68 | 166 | TVD 0.270 ± 0.008 | 0.730 | 4 2 3 0 1 | 0.4 |
| QFT-5 | 1 | 1 | 41 | 41 / 42.5 / 50 | 120 | TVD 0.114 ± 0.005 | 0.886 | 149 150 138 152 151 | 0.6 |
| QFT-5 | 2 | 5 | 29 | 29 / 30.0 / 31 | 99 | TVD 0.101 ± 0.004 | 0.899 | 129 110 118 108 109 | 0.7 |
| QFT-5 | 3 | 1 | 28 | 28 / 30.0 / 31 | 77 | TVD 0.091 ± 0.005 | 0.909 | 149 138 152 150 151 | 1.1 |
| QAOA-4-p2 | 0 | 1 | 31 | 31 / 31.0 / 34 | 127 | ratio 0.885 ± 0.005 | 0.776 | 3 0 1 2 | 0.4 |
| QAOA-4-p2 | 1 | 6 | 25 | 25 / 34.0 / 34 | 116 | ratio 0.957 ± 0.002 | 0.920 | 104 106 117 105 | 0.5 |
| QAOA-4-p2 | 2 | 2 | 25 | 25 / 25.0 / 28 | 90 | ratio 0.957 ± 0.002 | 0.920 | 104 106 117 105 | 0.6 |
| QAOA-4-p2 | 3 | 2 | 25 | 25 / 25.0 / 30 | 90 | ratio 0.961 ± 0.002 | 0.926 | 150 152 138 151 | 0.7 |

## Column meanings

- **Logical CX**: CNOTs before mapping to hardware (decomposed to CX + U).
- **2q gates**: two-qubit gates after transpiling (ECR on Eagle, CZ on Heron), including routing SWAPs.
- **TVD**: total variation distance from the exact distribution. 0 is perfect, 1 is completely wrong.
- **Hellinger F**: Hellinger fidelity with the exact distribution. 1 is perfect.
- **Approx. ratio**: expected cut of the measured distribution divided by the maximum cut.
- **Shot-noise TVD**: mean TVD from finite shots alone with zero hardware noise.
