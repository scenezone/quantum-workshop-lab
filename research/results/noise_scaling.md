# Noise-scaling robustness (held-out set, simulator)

Run `20261123-161422_noise-scaling`. Recipe v1 unchanged. Noise scale λ multiplies every gate and readout error (capped at 0.5) and divides T1/T2. Circuits are compiled on the unscaled `FakeKingston`. Budget: 3.0 estimated quantum seconds per circuit per method. Targets from PREREGISTRATION.md Part D.

| Target | Result | Detail |
|---|---|---|
| N1 robustness | **PASS** | T1/T2/T3 at ×0.5: PASS/PASS/PASS; at ×1.5: PASS/PASS/PASS |
| N2 high noise (×2.0) | **PASS** | recipe worst 0.0325 vs F worst 0.2863; recipe clearly worse than F on 0 (none) |
| N3 still useful | **PASS** | recipe clearly better than none on ×0.5: 4/6, ×1.5: 5/6, ×2: 5/6 |

## A6 targets at each noise scale

| λ | Run | T1 worst case | T2 deep | T3 no harm | O1 median (old) |
|---|---|---|---|---|---|
| ×0.5 | `20261123-161435_mitigation-test-noise0.5` | PASS: recipe worst 0.0259 vs 0.80 x F worst 0.0373 = 0.0298 | PASS: mean over 5 deep: recipe 0.0134 vs 0.85 x F 0.0187 = 0.0159 | PASS: recipe clearly worse than F on 0 circuit(s): none | FAIL: median change vs F +1.7% |
| ×1 | `20261123-112303_mitigation-test` | PASS: recipe worst 0.0231 vs 0.80 x F worst 0.1201 = 0.0961 | PASS: mean over 5 deep: recipe 0.0163 vs 0.85 x F 0.0367 = 0.0312 | PASS: recipe clearly worse than F on 0 circuit(s): none | FAIL: median change vs F -3.7% |
| ×1.5 | `20261123-161735_mitigation-test-noise1.5` | PASS: recipe worst 0.0282 vs 0.80 x F worst 0.2068 = 0.1654 | PASS: mean over 5 deep: recipe 0.0206 vs 0.85 x F 0.0598 = 0.0508 | PASS: recipe clearly worse than F on 0 circuit(s): none | PASS: median change vs F -23.4% |
| ×2 | `20261123-161940_mitigation-test-noise2` | PASS: recipe worst 0.0325 vs 0.80 x F worst 0.2863 = 0.2291 | PASS: mean over 5 deep: recipe 0.0256 vs 0.85 x F 0.0817 = 0.0695 | PASS: recipe clearly worse than F on 0 circuit(s): none | PASS: median change vs F -27.6% |

## Recipe: RMSE by noise scale (mean ± std)

| Circuit | ×0.5 | ×1 | ×1.5 | ×2 |
|---|---|---|---|---|
| Ising-4 | 0.0120 ± 0.0077 | 0.0088 ± 0.0091 | 0.0109 ± 0.0076 | 0.0122 ± 0.0080 |
| Mirror-4 | 0.0031 ± 0.0028 | 0.0048 ± 0.0027 | 0.0055 ± 0.0038 | 0.0089 ± 0.0061 |
| Grover-4-3it | 0.0087 ± 0.0054 | 0.0186 ± 0.0122 | 0.0241 ± 0.0142 | 0.0264 ± 0.0220 |
| QFT-6 | 0.0259 ± 0.0083 | 0.0231 ± 0.0058 | 0.0282 ± 0.0067 | 0.0302 ± 0.0096 |
| QAOA-5-p2 | 0.0056 ± 0.0057 | 0.0146 ± 0.0091 | 0.0172 ± 0.0131 | 0.0266 ± 0.0192 |
| QAOA-6 | 0.0149 ± 0.0125 | 0.0163 ± 0.0152 | 0.0229 ± 0.0128 | 0.0325 ± 0.0222 |

## F = readout+ZNE (linear): RMSE by noise scale (mean ± std)

| Circuit | ×0.5 | ×1 | ×1.5 | ×2 |
|---|---|---|---|---|
| Ising-4 | 0.0120 ± 0.0077 | 0.0088 ± 0.0091 | 0.0109 ± 0.0076 | 0.0122 ± 0.0080 |
| Mirror-4 | 0.0036 ± 0.0026 | 0.0072 ± 0.0047 | 0.0095 ± 0.0076 | 0.0202 ± 0.0083 |
| Grover-4-3it | 0.0373 ± 0.0086 | 0.1201 ± 0.0141 | 0.2068 ± 0.0113 | 0.2863 ± 0.0139 |
| QFT-6 | 0.0251 ± 0.0085 | 0.0231 ± 0.0050 | 0.0294 ± 0.0070 | 0.0339 ± 0.0097 |
| QAOA-5-p2 | 0.0050 ± 0.0070 | 0.0140 ± 0.0121 | 0.0302 ± 0.0171 | 0.0476 ± 0.0240 |
| QAOA-6 | 0.0143 ± 0.0135 | 0.0176 ± 0.0150 | 0.0218 ± 0.0175 | 0.0286 ± 0.0278 |

## No mitigation: RMSE by noise scale (mean ± std)

| Circuit | ×0.5 | ×1 | ×1.5 | ×2 |
|---|---|---|---|---|
| Ising-4 | 0.0045 ± 0.0050 | 0.0045 ± 0.0040 | 0.0045 ± 0.0026 | 0.0034 ± 0.0020 |
| Mirror-4 | 0.0311 ± 0.0011 | 0.0646 ± 0.0015 | 0.0940 ± 0.0017 | 0.1223 ± 0.0033 |
| Grover-4-3it | 0.1213 ± 0.0035 | 0.2246 ± 0.0033 | 0.3129 ± 0.0052 | 0.3913 ± 0.0049 |
| QFT-6 | 0.0248 ± 0.0019 | 0.0485 ± 0.0036 | 0.0696 ± 0.0025 | 0.0907 ± 0.0019 |
| QAOA-5-p2 | 0.0625 ± 0.0032 | 0.1185 ± 0.0048 | 0.1768 ± 0.0068 | 0.2306 ± 0.0050 |
| QAOA-6 | 0.0585 ± 0.0111 | 0.1045 ± 0.0075 | 0.1544 ± 0.0077 | 0.1966 ± 0.0087 |

## Summary by noise scale

| λ | Median RMSE none | Median RMSE F | Median RMSE recipe | Worst F | Worst recipe |
|---|---|---|---|---|---|
| ×0.5 | 0.0448 | 0.0131 | 0.0103 | 0.0373 | 0.0259 |
| ×1 | 0.0845 | 0.0158 | 0.0155 | 0.1201 | 0.0231 |
| ×1.5 | 0.1242 | 0.0256 | 0.0200 | 0.2068 | 0.0282 |
| ×2 | 0.1594 | 0.0313 | 0.0265 | 0.2863 | 0.0325 |
