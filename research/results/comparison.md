# Backend comparison (optimization level 2, best of seeds, no mitigation)

Metric: TVD for counts circuits (lower is better), approximation ratio for QAOA (higher is better). Per-backend detail is in `baseline_<backend>.md`.

| Circuit | Metric | FakeSherbrooke 2q | FakeSherbrooke depth | FakeSherbrooke metric | FakeKingston 2q | FakeKingston depth | FakeKingston metric |
|---|---|---|---|---|---|---|---|
| Bell | TVD | 1 | 6 | 0.018 | 1 | 7 | 0.015 |
| GHZ-3 | TVD | 2 | 10 | 0.030 | 2 | 10 | 0.027 |
| GHZ-5 | TVD | 4 | 24 | 0.070 | 4 | 16 | 0.037 |
| Grover-2 | TVD | 2 | 16 | 0.024 | 2 | 10 | 0.015 |
| Grover-3 | TVD | 37 | 173 | 0.208 | 37 | 133 | 0.092 |
| QFT-3 | TVD | 9 | 49 | 0.072 | 9 | 32 | 0.037 |
| QFT-4 | TVD | 17 | 80 | 0.125 | 17 | 55 | 0.065 |
| BV-4 | TVD | 3 | 18 | 0.048 | 3 | 9 | 0.029 |
| QAOA-3 | ratio | 7 | 36 | 0.979 | 7 | 32 | 0.986 |
| QAOA-4 | ratio | 11 | 68 | 0.718 | 11 | 45 | 0.738 |
| GHZ-7 | TVD | 6 | 36 | 0.107 | 6 | 22 | 0.057 |
| Grover-4 | TVD | 73 | 389 | 0.509 | 73 | 287 | 0.155 |
| QFT-5 | TVD | 30 | 142 | 0.239 | 29 | 99 | 0.101 |
| QAOA-4-p2 | ratio | 25 | 131 | 0.880 | 25 | 90 | 0.957 |
