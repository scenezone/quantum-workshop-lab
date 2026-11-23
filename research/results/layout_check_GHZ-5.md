# Layout check: GHZ-5

4000 shots × 10 repeats per row. ESP = estimated success probability from the backend's calibration data (product of 1 − error over all gates and measurements). Higher ESP should mean lower TVD.

## FakeSherbrooke

| Opt | Seed | Physical qubits | 2q gates | Depth | Mean readout err | Mean 2q err | ESP | TVD (mean ± std) |
|---|---|---|---|---|---|---|---|---|
| 1 | 11 (Week 0 seed) | 0 1 2 3 4 | 4 | 17 | 0.0180 | 0.0080 | 0.881 | 0.116 ± 0.006 |
| 1 | 1 (best of seeds) | 0 1 2 3 4 | 4 | 17 | 0.0180 | 0.0080 | 0.881 | 0.116 ± 0.006 |
| 2 | 11 (Week 0 seed) | 122 123 124 125 126 | 4 | 24 | 0.0094 | 0.0053 | 0.931 | 0.070 ± 0.006 |
| 2 | 1 (best of seeds) | 122 123 124 125 126 | 4 | 24 | 0.0094 | 0.0053 | 0.931 | 0.070 ± 0.006 |

### Per-qubit detail

**Level 1, seed 11 (Week 0 seed)**

| Physical qubit | Readout error | T1 (µs) | T2 (µs) |
|---|---|---|---|
| 0 | 0.0112 | 382 | 132 |
| 1 | 0.0244 | 234 | 251 |
| 2 | 0.0215 | 270 | 230 |
| 3 | 0.0120 | 329 | 333 |
| 4 | 0.0208 | 292 | 192 |

| Coupler | Gate | Error |
|---|---|---|
| 0-1 | ecr | 0.0075 |
| 1-2 | ecr | 0.0088 |
| 2-3 | ecr | 0.0087 |
| 3-4 | ecr | 0.0070 |

**Level 1, seed 1 (best of seeds)**

| Physical qubit | Readout error | T1 (µs) | T2 (µs) |
|---|---|---|---|
| 0 | 0.0112 | 382 | 132 |
| 1 | 0.0244 | 234 | 251 |
| 2 | 0.0215 | 270 | 230 |
| 3 | 0.0120 | 329 | 333 |
| 4 | 0.0208 | 292 | 192 |

| Coupler | Gate | Error |
|---|---|---|
| 0-1 | ecr | 0.0075 |
| 1-2 | ecr | 0.0088 |
| 2-3 | ecr | 0.0087 |
| 3-4 | ecr | 0.0070 |

**Level 2, seed 11 (Week 0 seed)**

| Physical qubit | Readout error | T1 (µs) | T2 (µs) |
|---|---|---|---|
| 122 | 0.0076 | 353 | 305 |
| 123 | 0.0078 | 252 | 301 |
| 124 | 0.0042 | 278 | 332 |
| 125 | 0.0078 | 239 | 63 |
| 126 | 0.0198 | 262 | 109 |

| Coupler | Gate | Error |
|---|---|---|
| 122-123 | ecr | 0.0049 |
| 123-124 | ecr | 0.0053 |
| 124-125 | ecr | 0.0063 |
| 125-126 | ecr | 0.0046 |

**Level 2, seed 1 (best of seeds)**

| Physical qubit | Readout error | T1 (µs) | T2 (µs) |
|---|---|---|---|
| 122 | 0.0076 | 353 | 305 |
| 123 | 0.0078 | 252 | 301 |
| 124 | 0.0042 | 278 | 332 |
| 125 | 0.0078 | 239 | 63 |
| 126 | 0.0198 | 262 | 109 |

| Coupler | Gate | Error |
|---|---|---|
| 122-123 | ecr | 0.0049 |
| 123-124 | ecr | 0.0053 |
| 124-125 | ecr | 0.0063 |
| 125-126 | ecr | 0.0046 |

## FakeKingston

| Opt | Seed | Physical qubits | 2q gates | Depth | Mean readout err | Mean 2q err | ESP | TVD (mean ± std) |
|---|---|---|---|---|---|---|---|---|
| 1 | 11 (Week 0 seed) | 0 1 2 3 4 | 4 | 20 | 0.0416 | 0.0013 | 0.794 | 0.204 ± 0.008 |
| 1 | 1 (best of seeds) | 0 1 2 3 4 | 4 | 20 | 0.0416 | 0.0013 | 0.794 | 0.204 ± 0.008 |
| 2 | 11 (Week 0 seed) | 148 149 150 151 152 | 4 | 16 | 0.0059 | 0.0020 | 0.961 | 0.037 ± 0.004 |
| 2 | 1 (best of seeds) | 148 149 150 151 152 | 4 | 16 | 0.0059 | 0.0020 | 0.961 | 0.037 ± 0.004 |

### Per-qubit detail

**Level 1, seed 11 (Week 0 seed)**

| Physical qubit | Readout error | T1 (µs) | T2 (µs) |
|---|---|---|---|
| 0 | 0.0095 | 384 | 354 |
| 1 | 0.1682 | 261 | 329 |
| 2 | 0.0079 | 283 | 110 |
| 3 | 0.0072 | 305 | 400 |
| 4 | 0.0149 | 330 | 79 |

| Coupler | Gate | Error |
|---|---|---|
| 0-1 | cz | 0.0012 |
| 1-2 | cz | 0.0012 |
| 2-3 | cz | 0.0012 |
| 3-4 | cz | 0.0015 |

**Level 1, seed 1 (best of seeds)**

| Physical qubit | Readout error | T1 (µs) | T2 (µs) |
|---|---|---|---|
| 0 | 0.0095 | 384 | 354 |
| 1 | 0.1682 | 261 | 329 |
| 2 | 0.0079 | 283 | 110 |
| 3 | 0.0072 | 305 | 400 |
| 4 | 0.0149 | 330 | 79 |

| Coupler | Gate | Error |
|---|---|---|
| 0-1 | cz | 0.0012 |
| 1-2 | cz | 0.0012 |
| 2-3 | cz | 0.0012 |
| 3-4 | cz | 0.0015 |

**Level 2, seed 11 (Week 0 seed)**

| Physical qubit | Readout error | T1 (µs) | T2 (µs) |
|---|---|---|---|
| 148 | 0.0022 | 243 | 201 |
| 149 | 0.0089 | 343 | 383 |
| 150 | 0.0078 | 363 | 428 |
| 151 | 0.0042 | 272 | 238 |
| 152 | 0.0066 | 201 | 90 |

| Coupler | Gate | Error |
|---|---|---|
| 148-149 | cz | 0.0026 |
| 149-150 | cz | 0.0022 |
| 150-151 | cz | 0.0020 |
| 151-152 | cz | 0.0014 |

**Level 2, seed 1 (best of seeds)**

| Physical qubit | Readout error | T1 (µs) | T2 (µs) |
|---|---|---|---|
| 148 | 0.0022 | 243 | 201 |
| 149 | 0.0089 | 343 | 383 |
| 150 | 0.0078 | 363 | 428 |
| 151 | 0.0042 | 272 | 238 |
| 152 | 0.0066 | 201 | 90 |

| Coupler | Gate | Error |
|---|---|---|
| 148-149 | cz | 0.0026 |
| 149-150 | cz | 0.0022 |
| 150-151 | cz | 0.0020 |
| 151-152 | cz | 0.0014 |
