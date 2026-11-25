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

## Part D: noise-scaling robustness (written 23 Nov 2026, 16:11, before any noise-scaled run)

The file before this part had SHA-256 `ebbdb7d17bb4643b1c98055f23c791395533b528fb84ab3db83b862fdbbc3d1d` (Parts A, B and C as committed in `d65539c`).

**Question:** does recipe v1 (unchanged, `FROZEN`) keep its advantage when the hardware is noisier or cleaner than the `FakeKingston` snapshot?

**Setup:**
- Held-out set (A3) only.
- Noise scale λ ∈ {0.5, 1.5, 2.0}. λ = 1.0 is the existing run `20261123-112303_mitigation-test`.
- At scale λ: every calibrated gate error and readout error is multiplied by λ (capped at 0.5), and every qubit's T1 and T2 are divided by λ.
- The circuits are compiled on the unscaled backend, so only the noise changes, not the circuits.
- Budget unchanged: 3.0 estimated quantum seconds per circuit per method. Fresh simulator seeds for each λ.

**Targets** (F = readout+ZNE (linear), as in A2):

| ID | Target | Pass condition |
|---|---|---|
| **N1** robustness | The A6 targets survive moderate change | T1, T2 and T3 all pass at λ = 0.5 **and** at λ = 1.5 |
| **N2** high noise | No worse than F when noise doubles | at λ = 2.0: recipe worst RMSE ≤ F worst RMSE, **and** recipe clearly worse than F on ≤ 1 circuit |
| **N3** still useful | Mitigation still helps at every level | at each λ ∈ {0.5, 1.5, 2.0}: recipe clearly better than no mitigation on ≥ 4 of 6 circuits |

Also reported, not targets: O1 (median vs F) at each λ, and how often the exponential guard fell back to linear.

---

## Part E: hardware execution plan (written 23 Nov 2026, 16:47, before any hardware job)

The file before this part had SHA-256 `caceaa4bc588c549599fd7a779196a9f0eb3dec831a05cc8319a19d907cc1d15` (Parts A-D). The reviewer approved the hardware run on 23 Nov. The targets are H1-H3 from A7, **unchanged**. This part fixes how they are run.

**Device:** a Heron r2 QPU available on our IBM Quantum open instance. `ibm_kingston` is not listed for this account; previous jobs ran on `ibm_fez` and `ibm_marrakesh`. We use whichever of those two has the shorter queue at submission, and record it. Circuits are compiled for that device (level 2, best of 20 seeds), and noise-free exact values are unchanged.

**Budget unit:** the platform reports usage in **Resource Units (RUs)**. The instance had **9.90 RUs** before any job. The RU ↔ quantum-seconds conversion is not known in advance, so:

1. **Smoke job first.** Bell only: one SamplerV2 job and one EstimatorV2 resilience-level-1 job, 1,000 shots each. It checks that both job types run, and records each job's reported usage (quantum seconds and/or RUs). It is not used for any target.
2. **Round 1.** Methods in the order none → recipe → IBM level 1 → IBM level 2. It runs only if its estimate (135 estimated quantum seconds, converted with the smoke job's rate, × 1.5 buffer) is at most 60% of the remaining RUs.
3. **Round 2 (drift check).** The reversed order: IBM level 2 → IBM level 1 → recipe → none. It runs only if the RUs remaining after round 1 are at least 1.5 × round 1's measured usage.

**Queue rule:** jobs are submitted one at a time, and each finishes before the next is sent. That keeps us well under the open plan's limit of 3 queued jobs.

**Abort rule:** `hardware.py --max-usage` stops submitting further jobs once the cumulative measured usage of the round exceeds the approved cap. Jobs already finished are kept and reported.

**Evaluation:**
- H1-H3 are evaluated on **round 1**. H1's quantum-seconds comparison uses each job's measured usage, in the same unit for all methods.
- Round 2 is reported next to round 1, with H1-H3 evaluated again. If the rounds disagree, both are reported and neither is dropped.
- No further rounds are run to "fix" a result.

---

## Part C: deviations log

| Date | What | Why | Effect on targets |
|---|---|---|---|
| 23 Nov 2026, after the held-out run | **Hardware budget is equal per method total, not per circuit.** `none` and `recipe` get equal estimated quantum seconds summed over the 8 hardware circuits. Each SamplerV2 job uses one shot count for all its circuits, and the recipe runs as two jobs (folded circuits; calibration). | IBM's SamplerV2 (`qiskit-ibm-runtime` 0.52) rejects jobs whose PUBs have different shot counts, so per-circuit equal budgets cannot be submitted. Found in the hardware dry run. | None to the definitions. H1 already compares total measured quantum_seconds. Per-circuit budgets on hardware differ by a few percent between methods; this is reported. |
| 23 Nov 2026, 19:58, before any hardware job | **H1's usage comparison may use Resource Units (RUs).** For each job we record both the seconds (`job.usage()`) and the RUs (`job.usage(resource_units=True)`) that IBM reports, plus the full `job.metrics()`. H1 compares the methods in RUs, or in seconds if RUs are not reported, always in the same unit for every method. | Our IBM Quantum instance (Open Plan) meters usage in RUs. IBM's plans page: "For standard QPU workloads, 1 RU = 1 minute of QPU compute time." The reviewer approved this on 23 Nov. IBM's free dry-run usage estimate is not available on the Open Plan, so the Bell smoke job (Part E) stays. | H1's threshold is unchanged (recipe ≤ IBM level 2 in total usage). Only the unit is named. |
| 24 Nov 2026, 10:45, after the smoke job, before round 1 | **Log (not a change):** (1) Smoke job `20261124-104212_hardware-smoke` on `ibm_fez`: Sampler, Bell, 1,000 shots = 0.0327 RU; Estimator level 1, 1,000 shots = 0.0382 RU, against an estimate of about 0.25 s each. So each job carries about 1.7-2 s of fixed overhead. `usage()` seconds are rounded (0 for the Sampler job), so RUs are the reliable unit, and `--max-usage` now counts RUs × 60. (2) Round 1 check: 135 s + 5 jobs × ~2 s ≈ 145 s ≈ 2.4 RU; × 1.5 = 3.6 RU ≤ 60% of 9.83 RU remaining. **Round 1 is allowed.** (3) `ibm_kingston` was listed as operational at 10:41. Part E's device rule (least busy of `ibm_fez`/`ibm_marrakesh`) is followed anyway, so the device is not chosen after seeing anything. | Part E's rules applied as written. | None. |
| 24 Nov 2026, after round 1, before round 2 | **Log:** Round 1 (`20261124-104424_hardware-round1`, `ibm_fez`) used 2.78 RU (none 0.439, recipe 0.469, IBM level 1 0.496, IBM level 2 1.373); 7.05 RU remain. Round 2 check: 7.05 ≥ 1.5 × 2.78 = 4.17, so **round 2 is allowed**. Round 2 runs on **`ibm_fez`, the same device as round 1**, because its purpose is a drift check on the same device. Part E's "shorter queue" rule is read as applying to the first hardware round. | Part E applied; it did not say which device round 2 uses. | None. Round 1's H1-H3 results are final as recorded. |
| 24 Nov 2026, after round 2 | **Log (measurement correction):** (1) `job.usage()` under-reports seconds. It returned 0 s for the smoke Sampler job and for the recipe's readout-calibration job in both rounds; IBM's job metrics (`qpu_charge_time_seconds`) show 2 s and 7 s charged, and their RUs were non-zero. Charged seconds per round are: none 27, **recipe 29 (not 22 as first reported)**, IBM level 1 30, IBM level 2 83. Every job is listed in `results/hardware_usage.md`, generated from the saved results without changing the run folders. `hardware.py` now reads the charged seconds first. (2) The "10:45" in the smoke log row above is approximate. The round 1 manifest (created 10:44:24) already records the hash of the file containing that row, so the row was written before round 1 was submitted. | `usage()` is a rounded summary; the metrics record is what IBM bills. | None. H1 is decided in RUs (19:58 entry), which were complete. In seconds the recipe is still about a third of level 2 (29 vs 83). |
