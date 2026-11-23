# Baseline v2: FakeSherbrooke (no error mitigation)

Qiskit Aer with the `FakeSherbrooke` noise model · 4000 shots per run · 20 transpiler seeds (1-20), best kept · 10 simulator repeats per configuration (seed 1234+i) · values are mean ± std over repeats.

Best-of-seeds rule: fewest two-qubit gates, then lowest depth. Selection uses compile metrics only, never the measured error.

## Counts circuits (optimization level 2)

| Circuit | Qubits | Logical CX | 2q gates (best) | 2q over seeds | Depth | TVD | Hellinger F | Shot-noise TVD |
|---|---|---|---|---|---|---|---|---|
| Bell | 2 | 1 | 1 | 1-1 | 6 | 0.018 ± 0.003 | 0.984 ± 0.002 | 0.006 |
| GHZ-3 | 3 | 2 | 2 | 2-2 | 10 | 0.030 ± 0.003 | 0.971 ± 0.003 | 0.006 |
| GHZ-5 | 5 | 4 | 4 | 4-4 | 24 | 0.070 ± 0.006 | 0.930 ± 0.006 | 0.006 |
| Grover-2 | 2 | 2 | 2 | 2-2 | 16 | 0.024 ± 0.001 | 0.976 ± 0.001 | 0.000 |
| Grover-3 | 3 | 24 | 37 | 37-39 | 173 | 0.208 ± 0.005 | 0.910 ± 0.003 | 0.006 |
| QFT-3 | 3 | 9 | 9 | 9-9 | 49 | 0.072 ± 0.004 | 0.928 ± 0.004 | 0.000 |
| QFT-4 | 4 | 18 | 17 | 17-19 | 80 | 0.125 ± 0.005 | 0.875 ± 0.005 | 0.000 |
| BV-4 | 5 | 3 | 3 | 3-3 | 18 | 0.048 ± 0.002 | 0.952 ± 0.002 | 0.000 |
| GHZ-7 | 7 | 6 | 6 | 6-6 | 36 | 0.107 ± 0.005 | 0.893 ± 0.005 | 0.006 |
| Grover-4 | 4 | 56 | 73 | 73-109 | 389 | 0.509 ± 0.006 | 0.696 ± 0.005 | 0.009 |
| QFT-5 | 5 | 26 | 30 | 30-35 | 142 | 0.239 ± 0.007 | 0.761 ± 0.007 | 0.000 |

## QAOA (optimization level 2)

| Circuit | Qubits | 2q gates (best) | 2q over seeds | Depth | Approx. ratio (noisy) | Approx. ratio (ideal) | Problem |
|---|---|---|---|---|---|---|---|
| QAOA-3 | 3 | 7 | 7-9 | 36 | 0.979 ± 0.002 | 0.994 | MaxCut triangle, p=1, max cut 2, gamma1=2.880 beta1=0.327 |
| QAOA-4 | 4 | 11 | 11-12 | 68 | 0.718 ± 0.004 | 0.750 | MaxCut 4-ring, p=1, max cut 4, gamma1=2.749 beta1=0.393 |
| QAOA-4-p2 | 4 | 25 | 25-30 | 131 | 0.880 ± 0.004 | 1.000 | MaxCut 4-ring, p=2, max cut 4, gamma1=2.689 beta1=0.559, gamma2=2.582 beta2=0.452 |

## Effect of optimization level

Counts circuits only for gates, depth and TVD (QAOA is scored separately). "Median-seed" is what a single random seed typically gives; "best" is best of all seeds.

| Opt level | Total 2q (best) | Total 2q (median seed) | Total depth | Mean TVD | Median TVD | Mean QAOA ratio |
|---|---|---|---|---|---|---|
| 0 | 331 | 352.0 | 2119 | 0.303 | 0.197 | 0.837 |
| 1 | 232 | 268.0 | 863 | 0.227 | 0.116 | 0.861 |
| 2 | 184 | 189.0 | 943 | 0.132 | 0.072 | 0.859 |
| 3 | 184 | 189.0 | 940 | 0.112 | 0.072 | 0.859 |

## Per-circuit change

Primary metric is TVD (lower is better) or, for QAOA, approximation ratio (higher is better). Percentages are relative changes.

| Circuit | Metric | 2q gates L0 → L2 | Depth L0 → L2 | Metric L0 → L1 → L2 → L3 | Metric change L0 → L2 | 2q L2 / L3 | Metric L2 − L3 |
|---|---|---|---|---|---|---|---|
| Bell | TVD | 1 → 1 (+0%) | 14 → 6 (-57%) | 0.042 → 0.041 → 0.018 → 0.018 | -57% | 1 / 1 | +0.000 |
| GHZ-3 | TVD | 2 → 2 (+0%) | 16 → 10 (-38%) | 0.072 → 0.072 → 0.030 → 0.030 | -59% | 2 / 2 | +0.000 |
| GHZ-5 | TVD | 4 → 4 (+0%) | 32 → 24 (-25%) | 0.118 → 0.116 → 0.070 → 0.069 | -41% | 4 / 4 | +0.000 |
| Grover-2 | TVD | 2 → 2 (+0%) | 48 → 16 (-67%) | 0.056 → 0.051 → 0.024 → 0.024 | -57% | 2 / 2 | +0.001 |
| Grover-3 | TVD | 48 → 37 (-23%) | 445 → 173 (-61%) | 0.373 → 0.237 → 0.208 → 0.197 | -44% | 37 / 37 | +0.011 |
| QFT-3 | TVD | 15 → 9 (-40%) | 110 → 49 (-55%) | 0.176 → 0.085 → 0.072 → 0.072 | -59% | 9 / 9 | +0.000 |
| QFT-4 | TVD | 36 → 17 (-53%) | 189 → 80 (-58%) | 0.337 → 0.180 → 0.125 → 0.125 | -63% | 17 / 17 | +0.000 |
| BV-4 | TVD | 18 → 3 (-83%) | 75 → 18 (-76%) | 0.197 → 0.048 → 0.048 → 0.048 | -75% | 3 / 3 | +0.000 |
| QAOA-3 | ratio | 9 → 7 (-22%) | 71 → 36 (-49%) | 0.959 → 0.978 → 0.979 → 0.979 | +2% | 7 / 7 | +0.000 |
| QAOA-4 | ratio | 14 → 11 (-21%) | 102 → 68 (-33%) | 0.709 → 0.717 → 0.718 → 0.717 | +1% | 11 / 11 | +0.000 |
| GHZ-7 | TVD | 6 → 6 (+0%) | 48 → 36 (-25%) | 0.809 → 0.809 → 0.107 → 0.107 | -87% | 6 / 6 | +0.000 |
| Grover-4 | TVD | 137 → 73 (-47%) | 872 → 389 (-55%) | 0.669 → 0.553 → 0.509 → 0.321 | -24% | 73 / 73 | +0.188 |
| QFT-5 | TVD | 62 → 30 (-52%) | 270 → 142 (-47%) | 0.480 → 0.302 → 0.239 → 0.219 | -50% | 30 / 30 | +0.020 |
| QAOA-4-p2 | ratio | 31 → 25 (-19%) | 185 → 131 (-29%) | 0.842 → 0.888 → 0.880 → 0.880 | +5% | 25 / 25 | -0.000 |

## Level 2 vs level 3: is the difference real?

"Outside spread" means the gap is larger than the combined std of the two (sqrt(std2² + std3²)). The std only covers simulator repeats, not seed-to-seed layout variation. When both levels use the same number of two-qubit gates, any gap comes from which physical qubits were picked, not from level 3's extra optimization.

| Circuit | L2 | L3 | L2 − L3 | Combined std | 2q L2 / L3 | Verdict |
|---|---|---|---|---|---|---|
| Bell | 0.018 ± 0.003 | 0.018 ± 0.004 | +0.000 | 0.005 | 1 / 1 | no difference (within spread) |
| GHZ-3 | 0.030 ± 0.003 | 0.030 ± 0.003 | +0.000 | 0.004 | 2 / 2 | no difference (within spread) |
| GHZ-5 | 0.070 ± 0.006 | 0.069 ± 0.006 | +0.000 | 0.008 | 4 / 4 | no difference (within spread) |
| Grover-2 | 0.024 ± 0.001 | 0.024 ± 0.001 | +0.001 | 0.002 | 2 / 2 | no difference (within spread) |
| Grover-3 | 0.208 ± 0.005 | 0.197 ± 0.005 | +0.011 | 0.007 | 37 / 37 | L3 better: same 2q gates, different qubits |
| QFT-3 | 0.072 ± 0.004 | 0.072 ± 0.004 | +0.000 | 0.006 | 9 / 9 | no difference (within spread) |
| QFT-4 | 0.125 ± 0.005 | 0.125 ± 0.005 | +0.000 | 0.007 | 17 / 17 | no difference (within spread) |
| BV-4 | 0.048 ± 0.002 | 0.048 ± 0.002 | +0.000 | 0.003 | 3 / 3 | no difference (within spread) |
| QAOA-3 | 0.979 ± 0.002 | 0.979 ± 0.002 | +0.000 | 0.003 | 7 / 7 | no difference (within spread) |
| QAOA-4 | 0.718 ± 0.004 | 0.717 ± 0.004 | +0.000 | 0.005 | 11 / 11 | no difference (within spread) |
| GHZ-7 | 0.107 ± 0.005 | 0.107 ± 0.005 | +0.000 | 0.007 | 6 / 6 | no difference (within spread) |
| Grover-4 | 0.509 ± 0.006 | 0.321 ± 0.008 | +0.188 | 0.010 | 73 / 73 | L3 better: same 2q gates, different qubits |
| QFT-5 | 0.239 ± 0.007 | 0.219 ± 0.007 | +0.020 | 0.010 | 30 / 30 | L3 better: same 2q gates, different qubits |
| QAOA-4-p2 | 0.880 ± 0.004 | 0.880 ± 0.003 | -0.000 | 0.005 | 25 / 25 | no difference (within spread) |

## All levels

| Circuit | Opt | Best seed | 2q gates | 2q min / median / max over seeds | Depth | Primary metric | Hellinger F | Physical qubits | Transpile s (all seeds) |
|---|---|---|---|---|---|---|---|---|---|
| Bell | 0 | 1 | 1 | 1 / 1.0 / 1 | 14 | TVD 0.042 ± 0.004 | 0.958 | 0 1 | 0.1 |
| Bell | 1 | 1 | 1 | 1 / 1.0 / 1 | 8 | TVD 0.041 ± 0.004 | 0.958 | 0 1 | 0.2 |
| Bell | 2 | 1 | 1 | 1 / 1.0 / 1 | 6 | TVD 0.018 ± 0.003 | 0.984 | 104 103 | 0.2 |
| Bell | 3 | 1 | 1 | 1 / 1.0 / 1 | 6 | TVD 0.018 ± 0.004 | 0.984 | 124 123 | 0.3 |
| GHZ-3 | 0 | 1 | 2 | 2 / 2.0 / 2 | 16 | TVD 0.072 ± 0.004 | 0.928 | 0 1 2 | 0.1 |
| GHZ-3 | 1 | 1 | 2 | 2 / 2.0 / 2 | 9 | TVD 0.072 ± 0.004 | 0.928 | 0 1 2 | 0.2 |
| GHZ-3 | 2 | 1 | 2 | 2 / 2.0 / 2 | 10 | TVD 0.030 ± 0.003 | 0.971 | 124 123 122 | 0.2 |
| GHZ-3 | 3 | 1 | 2 | 2 / 2.0 / 2 | 9 | TVD 0.030 ± 0.003 | 0.971 | 124 123 122 | 0.2 |
| GHZ-5 | 0 | 1 | 4 | 4 / 4.0 / 4 | 32 | TVD 0.118 ± 0.006 | 0.882 | 0 1 2 3 4 | 0.2 |
| GHZ-5 | 1 | 1 | 4 | 4 / 4.0 / 4 | 17 | TVD 0.116 ± 0.006 | 0.884 | 0 1 2 3 4 | 0.2 |
| GHZ-5 | 2 | 1 | 4 | 4 / 4.0 / 4 | 24 | TVD 0.070 ± 0.006 | 0.930 | 122 123 124 125 126 | 0.4 |
| GHZ-5 | 3 | 1 | 4 | 4 / 4.0 / 4 | 23 | TVD 0.069 ± 0.006 | 0.931 | 122 123 124 125 126 | 0.3 |
| Grover-2 | 0 | 1 | 2 | 2 / 2.0 / 2 | 48 | TVD 0.056 ± 0.003 | 0.944 | 0 1 | 0.1 |
| Grover-2 | 1 | 1 | 2 | 2 / 2.0 / 2 | 12 | TVD 0.051 ± 0.002 | 0.949 | 0 1 | 0.2 |
| Grover-2 | 2 | 1 | 2 | 2 / 2.0 / 2 | 16 | TVD 0.024 ± 0.001 | 0.976 | 123 124 | 0.2 |
| Grover-2 | 3 | 1 | 2 | 2 / 2.0 / 2 | 16 | TVD 0.024 ± 0.001 | 0.976 | 103 104 | 0.2 |
| Grover-3 | 0 | 14 | 48 | 48 / 51.0 / 54 | 445 | TVD 0.373 ± 0.007 | 0.788 | 0 1 2 | 0.4 |
| Grover-3 | 1 | 1 | 45 | 45 / 45.0 / 45 | 158 | TVD 0.237 ± 0.004 | 0.890 | 124 123 125 | 0.3 |
| Grover-3 | 2 | 1 | 37 | 37 / 39.0 / 39 | 173 | TVD 0.208 ± 0.005 | 0.910 | 124 123 125 | 0.4 |
| Grover-3 | 3 | 1 | 37 | 37 / 39.0 / 39 | 173 | TVD 0.197 ± 0.005 | 0.917 | 123 122 124 | 0.4 |
| QFT-3 | 0 | 2 | 15 | 15 / 15.0 / 18 | 110 | TVD 0.176 ± 0.007 | 0.824 | 2 0 1 | 0.2 |
| QFT-3 | 1 | 1 | 12 | 12 / 12.0 / 12 | 51 | TVD 0.085 ± 0.006 | 0.915 | 122 124 123 | 0.2 |
| QFT-3 | 2 | 4 | 9 | 9 / 9.0 / 9 | 49 | TVD 0.072 ± 0.004 | 0.928 | 124 123 122 | 0.3 |
| QFT-3 | 3 | 4 | 9 | 9 / 9.0 / 9 | 49 | TVD 0.072 ± 0.004 | 0.928 | 124 123 122 | 0.3 |
| QFT-4 | 0 | 2 | 36 | 36 / 36.0 / 39 | 189 | TVD 0.337 ± 0.007 | 0.662 | 3 0 2 1 | 0.3 |
| QFT-4 | 1 | 1 | 27 | 27 / 27.0 / 27 | 89 | TVD 0.180 ± 0.005 | 0.820 | 122 125 123 124 | 0.3 |
| QFT-4 | 2 | 11 | 17 | 17 / 18.0 / 19 | 80 | TVD 0.125 ± 0.005 | 0.875 | 122 123 125 124 | 0.3 |
| QFT-4 | 3 | 11 | 17 | 17 / 18.0 / 19 | 79 | TVD 0.125 ± 0.005 | 0.875 | 122 123 125 124 | 0.4 |
| BV-4 | 0 | 10 | 18 | 18 / 18.0 / 21 | 75 | TVD 0.197 ± 0.007 | 0.803 | 0 1 4 3 | 0.2 |
| BV-4 | 1 | 1 | 3 | 3 / 3.0 / 3 | 16 | TVD 0.048 ± 0.002 | 0.952 | 99 101 74 110 | 0.2 |
| BV-4 | 2 | 1 | 3 | 3 / 3.0 / 3 | 18 | TVD 0.048 ± 0.002 | 0.952 | 99 101 74 110 | 0.2 |
| BV-4 | 3 | 1 | 3 | 3 / 3.0 / 3 | 18 | TVD 0.048 ± 0.002 | 0.952 | 99 101 74 110 | 0.3 |
| QAOA-3 | 0 | 1 | 9 | 9 / 9.0 / 9 | 71 | ratio 0.959 ± 0.004 | 0.983 | 1 0 2 | 0.2 |
| QAOA-3 | 1 | 1 | 9 | 9 / 9.0 / 9 | 38 | ratio 0.978 ± 0.002 | 0.994 | 123 122 124 | 0.2 |
| QAOA-3 | 2 | 4 | 7 | 7 / 9.0 / 9 | 36 | ratio 0.979 ± 0.002 | 0.995 | 124 122 123 | 0.3 |
| QAOA-3 | 3 | 4 | 7 | 7 / 9.0 / 9 | 36 | ratio 0.979 ± 0.002 | 0.995 | 124 122 123 | 0.5 |
| QAOA-4 | 0 | 3 | 14 | 14 / 14.0 / 14 | 102 | ratio 0.709 ± 0.004 | 0.981 | 2 0 1 3 | 0.2 |
| QAOA-4 | 1 | 4 | 11 | 11 / 14.0 / 14 | 44 | ratio 0.717 ± 0.004 | 0.985 | 17 31 29 30 | 0.3 |
| QAOA-4 | 2 | 1 | 11 | 11 / 11.0 / 12 | 68 | ratio 0.718 ± 0.004 | 0.986 | 17 31 29 30 | 0.3 |
| QAOA-4 | 3 | 1 | 11 | 11 / 11.0 / 12 | 68 | ratio 0.717 ± 0.004 | 0.986 | 29 31 17 30 | 0.3 |
| GHZ-7 | 0 | 1 | 6 | 6 / 6.0 / 6 | 48 | TVD 0.809 ± 0.005 | 0.191 | 0 1 2 3 4 5 6 | 0.1 |
| GHZ-7 | 1 | 1 | 6 | 6 / 6.0 / 6 | 23 | TVD 0.809 ± 0.004 | 0.191 | 0 1 2 3 4 5 6 | 0.2 |
| GHZ-7 | 2 | 1 | 6 | 6 / 6.0 / 6 | 36 | TVD 0.107 ± 0.005 | 0.893 | 122 123 124 125 126 112 108 | 0.3 |
| GHZ-7 | 3 | 1 | 6 | 6 / 6.0 / 6 | 36 | TVD 0.107 ± 0.005 | 0.893 | 122 123 124 125 126 112 108 | 0.3 |
| Grover-4 | 0 | 15 | 137 | 137 / 152.0 / 167 | 872 | TVD 0.669 ± 0.006 | 0.532 | 1 3 0 2 | 0.7 |
| Grover-4 | 1 | 3 | 89 | 89 / 125.0 / 125 | 345 | TVD 0.553 ± 0.005 | 0.655 | 17 31 29 30 | 0.5 |
| Grover-4 | 2 | 2 | 73 | 73 / 75.0 / 109 | 389 | TVD 0.509 ± 0.006 | 0.696 | 17 31 29 30 | 0.6 |
| Grover-4 | 3 | 2 | 73 | 73 / 75.0 / 109 | 389 | TVD 0.321 ± 0.008 | 0.851 | 59 53 61 60 | 0.7 |
| QFT-5 | 0 | 18 | 62 | 62 / 65.0 / 68 | 270 | TVD 0.480 ± 0.006 | 0.520 | 4 2 3 0 1 | 0.4 |
| QFT-5 | 1 | 7 | 41 | 41 / 41.0 / 50 | 135 | TVD 0.302 ± 0.005 | 0.698 | 118 99 101 100 110 | 0.3 |
| QFT-5 | 2 | 2 | 30 | 30 / 30.0 / 35 | 142 | TVD 0.239 ± 0.007 | 0.761 | 118 101 99 110 100 | 0.4 |
| QFT-5 | 3 | 2 | 30 | 30 / 30.0 / 35 | 142 | TVD 0.219 ± 0.007 | 0.781 | 58 53 61 59 60 | 0.4 |
| QAOA-4-p2 | 0 | 5 | 31 | 31 / 31.0 / 34 | 185 | ratio 0.842 ± 0.004 | 0.703 | 3 0 1 2 | 0.3 |
| QAOA-4-p2 | 1 | 4 | 25 | 25 / 34.0 / 34 | 96 | ratio 0.888 ± 0.004 | 0.790 | 103 111 105 104 | 0.4 |
| QAOA-4-p2 | 2 | 1 | 25 | 25 / 25.0 / 30 | 131 | ratio 0.880 ± 0.004 | 0.777 | 103 111 105 104 | 0.4 |
| QAOA-4-p2 | 3 | 1 | 25 | 25 / 25.0 / 30 | 131 | ratio 0.880 ± 0.003 | 0.776 | 76 78 71 77 | 0.4 |

## Column meanings

- **Logical CX**: CNOTs before mapping to hardware (decomposed to CX + U).
- **2q gates**: two-qubit gates after transpiling (ECR on Eagle, CZ on Heron), including routing SWAPs.
- **TVD**: total variation distance from the exact distribution. 0 is perfect, 1 is completely wrong.
- **Hellinger F**: Hellinger fidelity with the exact distribution. 1 is perfect.
- **Approx. ratio**: expected cut of the measured distribution divided by the maximum cut.
- **Shot-noise TVD**: mean TVD from finite shots alone with zero hardware noise.
