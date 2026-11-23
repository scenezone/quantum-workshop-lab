# Pre-registration: mitigation recipe targets

Written so that targets are fixed before the results that test them exist. Every run records the SHA-256 of this file in its `manifest.json`, so the version a result was tested against can be checked later.

**Rules:** Part A was written before any run with the exponential guard or the quantum-seconds budget, and before any held-out circuit was simulated. Part B (the recipe) was written after the training rerun and before the held-out run. Neither part changes after it is written; any deviation is logged in Part C with its date and reason.

---

## Part A: targets, test set and metrics (written 23 Nov 2026, before any new run)

### A1. Old target (kept, not deleted)

**O1:** "Advisor beats the best fixed default on 6 of 10 class 1 circuits at equal budget, median error down 10%." (90-day plan, section 5.)

On the 21 Nov training run (`20261121-141214_mitigation`) this is **not met**. Even choosing the best method per circuit with hindsight gives a median gain of 0% over readout+ZNE (linear). It will be evaluated again on the held-out set and reported either way.

### A2. Reference method

**F = readout+ZNE (linear)**: the non-adaptive fixed method with the most per-circuit wins on the 21 Nov training run (8 of 14). The recipe is compared against F in simulation. On hardware it is compared against IBM's Runtime resilience levels 1 and 2.

### A3. Held-out test set (defined in `heldout.py`, never used to design the recipe)

| Name | Circuit | Observable | Physical range |
|---|---|---|---|
| Ising-4 | TFIM chain, 4 qubits, 6 Trotter steps, dt = 0.3, J = h = 1, from \|0000⟩ | magnetization (1/4) Σ ⟨Z_j⟩ | [−1, 1] |
| Mirror-4 | 4 random U+CZ layers (seed 2026), barrier, inverse | P(0000) | [0, 1] |
| Grover-4-3it | Grover, 4 qubits, marked 0110, 3 iterations | P(0110) | [0, 1] |
| QFT-6 | QFT on \|43⟩ = \|101011⟩ | ⟨X_j⟩, ⟨Y_j⟩ on all 6 qubits (12 values) | [−1, 1] each |
| QAOA-5-p2 | MaxCut 5-ring, p = 2, angles optimized noise-free | expected cut | [0, 5] |
| QAOA-6 | MaxCut triangular prism (3-regular), p = 1 | expected cut | [0, 9] |

**Deep** means more than 12 two-qubit gates after compilation (level 2, best of 20 seeds), summed over a circuit's measurement-basis circuits. A held-out circuit that compiles to 12 or fewer is reported but left out of the deep-circuit target.

### A4. Budget

**The budget is quantum seconds**, which is how we will measure from now on.

- **Simulator:** each method gets the same *estimated* quantum seconds per circuit, **Q = 3.0 s**, where estimated QPU time = Σ shots × (circuit duration from the backend's gate durations + the backend's default repetition delay, 250 µs on `FakeKingston`). Shots for each circuit are derived from Q, so methods with longer circuits (ZNE) get fewer shots.
- **Hardware:** the measured `quantum_seconds` of each job, from IBM Runtime job usage. Each method runs as its own job, so its usage is attributable.

### A5. Metrics

- Per circuit: RMSE of the circuit's observables against exact values from the noise-free statevector, mean ± std over repeats (simulator: 10 repeats).
- "Clearly better/worse": the gap in mean RMSE is larger than the combined std, √(std₁² + std₂²).

### A6. Simulator targets (held-out set, `FakeKingston`, recipe vs F, equal Q)

| ID | Target | Pass condition |
|---|---|---|
| **T1** worst case | The recipe's worst circuit is better than F's worst | max over held-out circuits of recipe RMSE ≤ 0.80 × max of F RMSE |
| **T2** deep circuits | Lower average error on deep circuits | mean recipe RMSE over held-out deep circuits ≤ 0.85 × mean F RMSE over the same circuits |
| **T3** no harm | Rarely clearly worse | recipe clearly worse than F on at most 1 of the 6 held-out circuits |
| O1 (old) | Median −10% | median over held-out of (recipe − F)/F ≤ −10%. Reported, kept as the old criterion |

### A7. Hardware targets (to be run later, after approval; `ibm_kingston` or the Heron device available)

Circuits: the 6 held-out circuits plus Bell and GHZ-5 as sanity checks (8 circuits). Methods: no mitigation (Sampler), our recipe (Sampler + our post-processing), IBM Runtime Estimator resilience level 1, and resilience level 2. Spread on hardware: bootstrap std over shots (500 resamples) for Sampler-based methods, and the Estimator's reported std for IBM levels.

| ID | Target | Pass condition |
|---|---|---|
| **H1** vs IBM level 2 | Better at no more QPU time | recipe RMSE lower than resilience level 2 on ≥ 5 of 8 circuits, **and** the recipe's total measured quantum_seconds ≤ level 2's |
| **H2** vs IBM level 1 | Better on deep circuits | mean recipe RMSE over deep circuits ≤ 0.85 × resilience level 1 |
| **H3** holds on hardware | Mitigation works on real hardware | recipe clearly better than no mitigation on ≥ 6 of 8 circuits |

A failed target is reported as failed. Thresholds are not edited after results exist.

---

## Part B: the recipe (written 23 Nov 2026, 11:22, before the held-out run)

Part A's SHA-256 was `042725112296bf1b863795e1771d82448c1026eb8f3f929b08feeb0ee65b1906`, and the training rerun `20261123-111818_mitigation-train` recorded that hash.

**Recipe v1** (`recipe.py`, SHA-256 `0b08bb7e96d9046e3be34ada9917c09859d2dba9895d1894d647ad26f1a67428`, `FROZEN = True`):

- **Data:** the readout+ZNE data group: readout calibration, then scale factors 1/3/5, each readout-corrected. Same estimated quantum seconds as every other method.
- **Per observable**, using measured values only, never the exact answer. Let d_s = (corrected value at scale s) − asymptote, where the asymptote is the observable's fully-mixed value. Use **guarded exponential** extrapolation if
  1. d₁, d₃, d₅ all have the same sign,
  2. |d₁| > |d₃| > |d₅| (decaying toward the asymptote), and
  3. |d₁| ≥ 0.1 × (physical range width).

  Otherwise use **linear** extrapolation. Guarded exponential falls back to linear when its result leaves the physical range, as the reviewer asked on 23 Nov.

**How it was designed (training set only):** On the training rerun, the range guard alone fixed exponential's worst failures: readout+ZNE (exp) worst RMSE 0.0963 → (expg) 0.0609. It did not fix QFT, where exponential gives wrong values inside the physical range for observables whose exact value equals the asymptote. Checks 1-2 target that case. DELTA was checked on copies of the training run at 0, 0.05, 0.1, 0.15, 0.2 and 0.3; the results were almost identical, so the a-priori 0.1 was kept.

**Recipe on the training set** (in-sample, so not evidence; for reference only):

| | Recipe | F = readout+ZNE (linear) |
|---|---|---|
| Worst RMSE | 0.0266 (QAOA-4) | 0.0593 (Grover-4) |
| Mean RMSE, deep training circuits | 0.59 × F | 1 |
| Clearly worse than F | 0 of 14 | n/a |
| Median change vs F | about 0% (O1 not met in-sample either) | n/a |

The held-out test (Part A, A6) is the only evidence that counts.

---

## Part C: deviations log

| Date | What | Why | Effect on targets |
|---|---|---|---|
| 23 Nov 2026, after the held-out run | **Hardware budget is equal per method total, not per circuit.** `none` and `recipe` get equal estimated quantum seconds summed over the 8 hardware circuits. Each SamplerV2 job uses one shot count for all its circuits, and the recipe runs as two jobs (folded circuits; calibration). | IBM's SamplerV2 (`qiskit-ibm-runtime` 0.52) rejects jobs whose PUBs have different shot counts, so per-circuit equal budgets cannot be submitted. Found in the hardware dry run. | None to the definitions. H1 already compares total measured quantum_seconds. Per-circuit budgets on hardware differ by a few percent between methods; this is reported. |
