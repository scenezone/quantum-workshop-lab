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

## Part F: recipe v2 and its held-out test (written 25 Nov 2026, before any v2 held-out circuit was simulated with noise or run on hardware)

*Revised the same day at the reviewer's request (F4-F7), still before any v2 held-out run; see Part C.*

The file before this part had SHA-256 `8b1b6812f12014ee89d96621f21850342c97cf46b6dcba9c8b236df04083ba0f` (Parts A-E and 5 Part C rows). Parts A-E, their targets and their results are unchanged, and recipe v1 (`recipe.py`) stays frozen. This part adds a second recipe and a new test of it, on circuits that no design step has used.

### F1. Why v2, and what we saw before writing this part

On `ibm_fez` (rounds 1 and 2, 24 Nov) recipe v1 lost to IBM resilience level 2 on deep circuits. On Grover-4-3it the values at scales 1/3/5 were 0.544 / 0.203 / 0.077 (exact 0.961). At scale 5 the signal was gone, and v1 returned 0.625.

Design evidence. All of it is **seen data**, and none of it is evidence that v2 works:

| Evidence (training circuits or saved hardware counts) | Recipe v1 | v1 data + clip | v2 at 1/1.5/2 | v2 at 1/2/3 |
|---|---|---|---|---|
| Simulator, 14 training circuits, median RMSE | 0.0112 / 0.0101 | 0.0096 / 0.0076 | 0.0170 | 0.0099 |
| Simulator, mean RMSE on the 6 deep circuits (≥ 13 CZ) | 0.0169 / 0.0174 | 0.0161 / 0.0168 | 0.0341 | 0.0262 |
| Simulator, Grover-4 (73 CZ) | 0.0120 / 0.0081 | 0.0120 / 0.0081 | 0.0405 | 0.0287 |
| Hardware replay of the clip rule, mean error rounds 1 / 2 | 0.0775 / 0.0768 | 0.0407 / 0.0414 | (needs new data) | (needs new data) |

Simulator rows come from two runs, FakeKingston, 3 estimated s per circuit per method, 10 repeats: `20261124-161451_mitigation-v2-train` (1/1.5/2) and `20261125-101929_mitigation-v2-train-scales1-2-3` (1/2/3). Each v1 cell gives one value per run. The replay row comes from `results/v2_design_replay.md`.

- **In the simulator v2 is not better than v1.** At 1/2/3 its median is about the same, but it is worse on deep circuits (0.026 vs 0.017; Grover-4 0.029 vs 0.008). Its RMSE is above 1.25 × v1 on 4 of the 14 circuits.
  - The fake-backend noise has no coherent part, so the simulator cannot show what twirling is for.
  - Small scale spacing amplifies shot noise, which is why 1/1.5/2 was worse still.
  - **The benefit of twirling can only be tested on hardware.**
- **Coherent-noise check** (`python twirl.py`: a ZZ over-rotation after every CZ). The linear-extrapolation error went from 0.189 untwirled to 0.048 twirled.
- **Held-out circuits.** Only their exact (noise-free) values and compiled gate counts were looked at (see F3).
- **Code-path check.** It ran on 3 training circuits only (`20261125-120531_mitigation-v2-train-partial`).

### F2. Recipe v2 (frozen)

`recipe_v2.py` SHA-256 `c98dd89d6d4cb794cdefd9c63277734ca5d2d24417f60dcfe522c1b7a957bfd8`. Building blocks are in `twirl.py`, SHA-256 `3a80e48152259026c71c9b1a4c74417d9451782df6d849e6d1cd44779d015a4a`.

v2 differs from v1 in exactly three ways:

1. **Pauli twirling of every CZ.** There are 8 random instances per scale factor, and their counts are pooled.
2. **Two-qubit-only folding at nominal scales 1 / 2 / 3.** The actual scales (1 + 2F/n) are used in the fit. The reviewer chose these scales on 25 Nov over the first proposal, 1 / 1.5 / 2, whose close spacing made extrapolation too noisy in the training runs.
3. **Clipping.** The estimate is clipped to the observable's physical range, instead of falling back to linear.

Everything else is v1: 20% of shots on readout calibration, readout correction before extrapolation, and the same exponential/linear branch rule with DELTA = 0.1.

**Secondary methods (reported, no target):**
- `v1_clip`: v1's data with v2's rule. It needs no extra job.
- `v2_s15`: recipe v2 at 1 / 1.5 / 2. It has its own jobs and the same budget, and is submitted last.

Their results cannot change the recipe in this round. Any change to v2 after this part needs new held-out circuits.

### F3. Held-out circuits

These are defined in `heldout_v2.py`, SHA-256 `47cebe4405b52f8ee46d84b121fa9ec39862fa97011a4b210a97c05e2207d3be`.

| Circuit | What | Observable | Exact | CZ after compilation |
|---|---|---|---|---|
| Heisenberg-4 | XXZ chain, J = 1, Δ = 0.5, dt = 0.25, 5 Trotter steps from the Néel state | staggered magnetization (1/4) Σ (-1)^j ⟨Z_j⟩, range [-1, 1] | -0.646 | 44 |
| QPE-4 | phase 11/16, 4 counting qubits | P(1011), range [0, 1] | 1.000 | 26 |

The Heisenberg step count was set to 5 because 4 steps gave an exact value of 0.001. That is the fully mixed value, so it would carry no information. The choice used exact values only.

### F4. Simulator test (`mitigation_v2.py --set test`)

The test uses FakeKingston, 3.0 estimated quantum seconds per circuit per data group, 10 repeats and simulator seed base 70000. Each circuit is judged separately.

- **S1 (gate), per circuit:** recipe v2 is clearly better than no mitigation.
  - "Clearly better" means the gap in mean RMSE is larger than the combined spread √(σ₁² + σ₂²) of the per-repeat RMSEs.
  - If S1 fails on either circuit, the hardware round is not run until the reviewer has seen the result.
- **E1 (expectation, not a target), per circuit:** v2 is **not** expected to beat v1 in the simulator (F1). The v2/v1 RMSE ratio is reported.
  - No simulator target compares v2 with v1. The earlier proposal (v2 ≤ 1.25 × v1) was never written into this file, and the training runs already broke it on 4 of 14 circuits.
- Secondary methods are reported, with no target.

### F5. Hardware round (`hardware_v2.py`)

**When:** on **1 or 2 December 2026**. 3-4 December is only a buffer for a queue delay or a failed job. The open-plan trial ends around 4 December.

**Device and jobs:**
- **Device:** the least busy of `ibm_fez` and `ibm_marrakesh` at submission, recorded. Compilation is level 2, best of 20 seeds, for that device, and the same compiled circuit is used for every method.
- **Jobs:** 8, sent one at a time, each finished before the next. The order is none → recipe v1 → recipe v2 → IBM level 2 → `v2_s15`. The secondary goes last, so a stop can only cut it.
- **Twirl seed:** 20261125.

**Budget:**
- Each method gets 6.0 estimated quantum seconds per circuit, 12 s per method total. The secondary `v2_s15` gets the same budget as recipe v2, so they can be compared.
- IBM level 2 uses precision 1/√(shots of none).
- Expected charge is 94.5 s plus 2.5 s per Sampler job (the overhead measured in rounds 1-2) = **112 s ≈ 1.87 RU**:

  | Method | none | v1 | v2 | IBM level 2 | `v2_s15` |
  |---|---|---|---|---|---|
  | Expected charge (RU) | 0.24 | 0.28 | 0.28 | 0.78 | 0.28 |

  4.28 RU remained after round 2.

**Run rules:**
- The round runs only if S1 passed on both circuits and the remaining RUs are at least 1.5 × 1.87 = 2.80.
- **Reserve: about 1 RU is kept** for resubmitting a failed job. `--max-rus 3.0` stops further submissions, which leaves at least 1.28 RU.
- Charged seconds (`qpu_charge_time_seconds`) and RUs are recorded for every job.
- **One round only.** A job that returned data is never rerun.
- A job that **fails** (an error, or no data) is resubmitted once, unchanged, straight away (`hardware_v2.py` does this), from the reserve. A failure on the second attempt stops the round. The remaining jobs may then be submitted on 3-4 December, in the same order.
  - If a target job (none, v1, v2, IBM level 2) still has no data, the round is incomplete. No target is evaluated, the failure is logged in Part C, and the reviewer decides what happens next.

### F6. Hardware success criteria (written before the run; each circuit separately)

**Measurement:**
- Error = |estimate − exact|.
- σ is the bootstrap std over 500 multinomial resamples of the counts. For the Estimator, it comes from normal draws using the reported std.
- For methods a and b on one circuit, gap = error_b − error_a, and combined spread = √(σ_a² + σ_b²).

**Verdict for each pair, on each circuit:**
- **a clearly better than b:** gap > combined spread.
- **a clearly worse than b:** −gap > combined spread.
- **no clear difference:** otherwise.

**Targets, each evaluated for Heisenberg-4 and QPE-4 separately (6 circuit results + 1 cost result):**

| Target | Comparison | Pass if |
|---|---|---|
| **G1** | v2 vs recipe v1 | v2 is **clearly better** |
| **G2** | v2 vs IBM level 2 | v2 is **not clearly worse** (clearly better, or no clear difference) |
| **G3** | v2 vs no mitigation | v2 is **clearly better** |
| **G2-cost** | round total | v2's RUs ≤ 0.5 × IBM level 2's RUs |

**Secondary comparisons (reported, no target):** `v1_clip` vs v2 and `v2_s15` vs v2, on each circuit, with the same verdicts.
- This is the only honest held-out test of v1 + clip, which was designed on seen hardware data.
- **If v1 + clip turns out better than v2, that is what we report.**

**How the results are read:**
- Results are reported per circuit, for example "on QPE-4 v2 is clearly better than v1; on Heisenberg-4 there is no clear difference". Two circuits are never averaged into one verdict.
- **Two circuits and one round can show a direction, not a proof.** Even if every target passes, the claim is "v2 improved on v1 on both held-out circuits in one hardware round", not "v2 is better than v1".
- The frozen recipe v2 stays at 1 / 2 / 3 whatever the secondaries show. Any change to v2 needs new held-out circuits.
- After this round, Heisenberg-4 and QPE-4 are seen data.

### F7. Frozen record (fingerprinted before any v2 held-out run)

The circuits, the exact values, the recipe and the scale decision are fixed by the files below. The criteria are fixed by this file, whose SHA-256 every run records in its manifest. `python fingerprint.py` checks that each file still has the hash listed here.

| File | Fixes | SHA-256 |
|---|---|---|
| `recipe_v2.py` | recipe v2: scales 1/2/3, secondary 1/1.5/2, 8 twirls, DELTA, clip rule | `c98dd89d6d4cb794cdefd9c63277734ca5d2d24417f60dcfe522c1b7a957bfd8` |
| `twirl.py` | two-qubit folding and Pauli twirling | `3a80e48152259026c71c9b1a4c74417d9451782df6d849e6d1cd44779d015a4a` |
| `heldout_v2.py` | the two held-out circuits (Heisenberg-4, QPE-4) | `47cebe4405b52f8ee46d84b121fa9ec39862fa97011a4b210a97c05e2207d3be` |
| `mitigation_v2.py` | simulator test, observables and exact values, S1/E1 | `0de8e15281a132a858f6b491411185b1945000369b9b7afae78087cf1485b183` |
| `hardware_v2.py` | hardware plan, shots, job order, retry, G1-G3 evaluation | `a24f2acd3b55bd0a08528cbebbd2290a3d9b05ac28ce4332d1e49213d639c1d5` |
| `recipe.py` | recipe v1 (frozen 23 Nov) | `0b08bb7e96d9046e3be34ada9917c09859d2dba9895d1894d647ad26f1a67428` |
| `mitigation.py` | readout correction, extrapolation, compilation settings | `4b8036fee7d8228aae51fa9a8aa9877e294254447281eb6b14341dafbd82c4a3` |
| `folding.py` | v1 all-gate folding | `2309126cb3bc1c6128af01a9fb3b471e52a1673b9a2f25d6765ff46378d8450a` |
| `baseline.py` | compilation (best of 20 seeds) | `3c216afa124ae8b3e4d340c3dc74958c1eda1e14df702fec8d29b6841940d094` |
| `hardware.py` | job submission and usage records | `0fcc586b83a42b7ce1b5fdecbe2df597d994883c1b7c8537a84a431e74f06b9d` |

**Exact values** (noise-free, Statevector):

| Circuit | Exact | Fully mixed value |
|---|---|---|
| Heisenberg-4 | −0.6462202415 | 0.0 |
| QPE-4 | 1.0000000000 | 0.0625 |

`hardware_v2.py` checks that the IBM Estimator's Pauli form of each observable gives the same exact value.

---

## Part C: deviations log

| Date | What | Why | Effect on targets |
|---|---|---|---|
| 23 Nov 2026, after the held-out run | **Hardware budget is equal per method total, not per circuit.** `none` and `recipe` get equal estimated quantum seconds summed over the 8 hardware circuits. Each SamplerV2 job uses one shot count for all its circuits, and the recipe runs as two jobs (folded circuits; calibration). | IBM's SamplerV2 (`qiskit-ibm-runtime` 0.52) rejects jobs whose PUBs have different shot counts, so per-circuit equal budgets cannot be submitted. Found in the hardware dry run. | None to the definitions. H1 already compares total measured quantum_seconds. Per-circuit budgets on hardware differ by a few percent between methods; this is reported. |
| 23 Nov 2026, 19:58, before any hardware job | **H1's usage comparison may use Resource Units (RUs).** For each job we record both the seconds (`job.usage()`) and the RUs (`job.usage(resource_units=True)`) that IBM reports, plus the full `job.metrics()`. H1 compares the methods in RUs, or in seconds if RUs are not reported, always in the same unit for every method. | Our IBM Quantum instance (Open Plan) meters usage in RUs. IBM's plans page: "For standard QPU workloads, 1 RU = 1 minute of QPU compute time." The reviewer approved this on 23 Nov. IBM's free dry-run usage estimate is not available on the Open Plan, so the Bell smoke job (Part E) stays. | H1's threshold is unchanged (recipe ≤ IBM level 2 in total usage). Only the unit is named. |
| 24 Nov 2026, 10:45, after the smoke job, before round 1 | **Log (not a change):** (1) Smoke job `20261124-104212_hardware-smoke` on `ibm_fez`: Sampler, Bell, 1,000 shots = 0.0327 RU; Estimator level 1, 1,000 shots = 0.0382 RU, against an estimate of about 0.25 s each. So each job carries about 1.7-2 s of fixed overhead. `usage()` seconds are rounded (0 for the Sampler job), so RUs are the reliable unit, and `--max-usage` now counts RUs × 60. (2) Round 1 check: 135 s + 5 jobs × ~2 s ≈ 145 s ≈ 2.4 RU; × 1.5 = 3.6 RU ≤ 60% of 9.83 RU remaining. **Round 1 is allowed.** (3) `ibm_kingston` was listed as operational at 10:41. Part E's device rule (least busy of `ibm_fez`/`ibm_marrakesh`) is followed anyway, so the device is not chosen after seeing anything. | Part E's rules applied as written. | None. |
| 24 Nov 2026, after round 1, before round 2 | **Log:** Round 1 (`20261124-104424_hardware-round1`, `ibm_fez`) used 2.78 RU (none 0.439, recipe 0.469, IBM level 1 0.496, IBM level 2 1.373); 7.05 RU remain. Round 2 check: 7.05 ≥ 1.5 × 2.78 = 4.17, so **round 2 is allowed**. Round 2 runs on **`ibm_fez`, the same device as round 1**, because its purpose is a drift check on the same device. Part E's "shorter queue" rule is read as applying to the first hardware round. | Part E applied; it did not say which device round 2 uses. | None. Round 1's H1-H3 results are final as recorded. |
| 24 Nov 2026, after round 2 | **Log (measurement correction):** (1) `job.usage()` under-reports seconds. It returned 0 s for the smoke Sampler job and for the recipe's readout-calibration job in both rounds; IBM's job metrics (`qpu_charge_time_seconds`) show 2 s and 7 s charged, and their RUs were non-zero. Charged seconds per round are: none 27, **recipe 29 (not 22 as first reported)**, IBM level 1 30, IBM level 2 83. Every job is listed in `results/hardware_usage.md`, generated from the saved results without changing the run folders. `hardware.py` now reads the charged seconds first. (2) The "10:45" in the smoke log row above is approximate. The round 1 manifest (created 10:44:24) already records the hash of the file containing that row, so the row was written before round 1 was submitted. | `usage()` is a rounded summary; the metrics record is what IBM bills. | None. H1 is decided in RUs (19:58 entry), which were complete. In seconds the recipe is still about a third of level 2 (29 vs 83). |
| 25 Nov 2026, before any v2 held-out run | **Log: recipe v2's scale factors (1 / 2 / 3) were selected on training data only, before any held-out result was seen.** The evidence was the simulator design runs on the 14 training circuits (`20261124-161451_mitigation-v2-train` at 1/1.5/2 and `20261125-101929_mitigation-v2-train-scales1-2-3` at 1/2/3) and the saved hardware counts of rounds 1-2 (clip replay). The reviewer chose 1/2/3 on 25 Nov. At that time, no noisy simulation or hardware run of Heisenberg-4 or QPE-4 existed; only their exact values and compiled gate counts had been computed. 1/1.5/2 is kept only as a secondary with no target. | Reviewer request: record how the scales were chosen. | None. It makes the selection record explicit. |
| 25 Nov 2026, before any v2 held-out run | **Part F revised (F4-F7).** The first version of Part F had file SHA-256 `f48ec3f53ecb8c9a…`. No run recorded it and nothing was run with it. Changes: (1) every target is evaluated per circuit with the three-way verdict (clearly better / no clear difference / clearly worse; clearly = gap > combined spread). (2) v2 vs v1 (G1) and v2 vs IBM level 2 (G2) are separate targets. G2's earlier "+ 0.05" margin is replaced by "not clearly worse". G1's earlier "lower on both, clearly on one" is replaced by "clearly better" on each circuit. (3) The note that 2 circuits show a direction, not a proof. (4) v1 + clip is reported as a secondary, and it is reported if it beats v2. (5) `v2_s15` runs as a secondary at the same budget: expected 0.28 RU (the reviewer estimated ~0.1 RU). (6) The run is on 1-2 Dec, 3-4 Dec is a buffer, a failed job is resubmitted once, and ~1 RU is kept in reserve. (7) F7, the frozen record. | Reviewer's requests of 25 Nov, made before any v2 held-out result existed. | Targets are fixed in their final form before the simulator test and the hardware round. |
