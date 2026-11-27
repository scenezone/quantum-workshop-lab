# Decisions

Agreed with the senior reviewer on 19 Nov 2026, after the Week 0 baseline. These are the starting point for the frozen benchmark spec (due end of Week 2, 6 Dec 2026).

## Budget

- **Equal budget = total shots across every circuit execution**, including mitigation overhead.
  - ZNE with noise factors 1/3/5 splits the shot budget across the three factors.
  - Readout-calibration shots count toward the budget.
- On real hardware, compare by measured `quantum_seconds`.
- ZNE's QPU-time overhead must be counted in the hardware budget. The senior's estimate is about 9x for ZNE 1/3/5. Simulator estimate on Kingston (`results/mitigation_FakeKingston.md`, with the backend's default 250 µs repetition delay per shot):
  - **Equal shots (our rule):** QPU time ×1.00-1.03, gate time ×1.1-2.3.
  - **Full shots for every factor:** QPU time ×3.0-3.1, gate time ×3.3-6.9.
  - 9x is the upper limit of gate time alone (1 + 3 + 5) for a full-budget run whose duration is all gates. Per-shot overhead (repetition delay, measurement) does not scale with folding and dominates for these short circuits. These are estimates; measure real `quantum_seconds` in the hardware phase.

## Baselines

- **Simulator phase:** three baselines
  1. no mitigation
  2. readout mitigation
  3. ZNE with `mitiq`, noise factors 1, 3, 5
- The report must say clearly that these are **not** Qiskit Runtime resilience levels. Runtime's `resilience_level` has no effect in local testing mode (confirmed: levels 0, 1 and 2 gave an identical ⟨ZZ⟩ = 0.8135 on `FakeSherbrooke`, with the warning "The resilience_level option has no effect in local testing mode").
- **Hardware phase:** Qiskit Runtime mitigation options are the baseline.

## ZNE implementation (agreed 20 Nov 2026)

- Fold **in Qiskit, after transpilation, on native gates** (CZ/ECR), and use mitiq **only for extrapolation** (Richardson). Never re-optimize after folding, or the inserted G† G pairs cancel. Implemented in `folding.py`.
- Verified: folded circuits are exactly equivalent to the original (operator check on CZ and ECR bases), and the two-qubit gate count is exactly 1x/3x/5x at scales 1/3/5. `mitigation.py` asserts this for every circuit.
- The mitiq-folding bug on Sherbrooke (`zne_smoke.py`) is not being pursued; target is Kingston. Native folding does not have the bug, because nothing goes through OpenQASM.

## Round 3 (agreed 21 Nov 2026)

- **Readout + ZNE:** readout-correct every folded circuit first, then extrapolate. Same 12,000-shot total: 20% calibration, the rest split equally over the scale factors.
- **Extrapolation:** compare Richardson, linear and exponential on the same saved counts (no re-simulation). Exponential uses the observable's fully-mixed value as its asymptote.
- **Seed selection:** compare (A) fewest 2q gates then depth vs (B) highest ESP (`selection_compare.py`).
- **ESP caveat:** on fake backends the noise model and ESP come from the same calibration, so their agreement is partly circular. It shows the formula is consistent, not that it predicts hardware error. The same applies to the ×3 ZNE QPU-time estimate. Both must be confirmed on hardware (`quantum_seconds`).
- **Deeper circuits added:** GHZ-7, Grover-4 (2 iterations; Grover-3 already uses 2), QFT-5 (input \|21⟩), QAOA 4-ring with p=2.
- **PoC simulation report** for the grant application: `POC_REPORT.md`.
- **Raw files and the method of every run are saved** (`runlog.py`, `results/runs/`).

Results are in `POC_REPORT.md`. Points that need a decision:

- The success threshold "median error −10% vs best fixed default" is not reachable in simulation against readout+ZNE (linear), even when the best method is picked per circuit with hindsight (median gain 0%, mean 12%). Recalibrate it (the plan allows this after Week 2), for example to a worst-case or deep-circuit metric.
- Exponential extrapolation fails on observables whose exact value equals their fully-mixed value (QFT-3: RMSE 1.05). The advisor must detect this case.

## Round 4 (agreed 23 Nov 2026)

- **Recalibrated success criteria:** worst-case and deep-circuit metrics. The original "median −10%" target stays in every report, marked **not met**, and is never deleted.
- **Pre-registration:** new targets are written before the results that test them, and tested on new (held-out) circuits. See `PREREGISTRATION.md`. Its SHA-256 is recorded in every run manifest, and the code will not run the held-out set until the recipe is frozen.
- **Exponential guard:** if exponential extrapolation leaves the observable's physical range, fall back to linear (`expg` in `mitigation.py`). Recipe v1 adds a decay check on measured values, because the range guard alone does not catch QFT-type failures, which stay inside the range.
- **More deep circuits:** 6 held-out circuits (`heldout.py`): Ising-4 Trotter, Mirror-4, Grover-4 with 3 iterations, QFT-6, QAOA-5 ring p=2, QAOA-6 prism.
- **Budget in quantum seconds,** from now on.
  - Simulator: equal estimated QPU time per circuit per method (3.0 s = Σ shots × (duration + 250 µs rep delay)).
  - Hardware: measured `quantum_seconds` per job. IBM SamplerV2 needs one shot count per job, so hardware budgets are equal per method total (Part C of the pre-registration).
- **Next: hardware.** The same circuits with no mitigation, our recipe, and IBM resilience levels 1 and 2 (`hardware.py`; targets H1-H3 are pre-registered). Not submitted yet; it needs an IBM account and approval to spend QPU time.

Results: held-out T1, T2 and T3 **PASS**; O1 (old median target) **NOT MET** (−3.7%). Details in `POC_REPORT.md` section 0.

## Round 5 (23 Nov 2026)

- **Noise scaling 0.5x-2x** (pending since round 2): pre-registered as Part D (16:11) before any run. Held-out set, recipe unchanged, circuits compiled on the unscaled backend. **N1, N2 and N3 all PASS.** The old median target is met at ×1.5 and ×2, and not met at ×0.5 and ×1.
- **Fingerprints for reviewers:** `fingerprint.py` writes `results/FINGERPRINTS.md`, with SHA-256 of every run file and key method file. It also verifies that Parts A and B and `recipe.py` are byte-identical to the versions the runs recorded (all match).

## Round 6: hardware (24 Nov 2026)

- Budget in RUs (reviewer approved; Part C, 23 Nov 19:58). Every job's seconds, RUs and full `metrics()` are saved.
- Smoke job, then round 1 and round 2 (drift check, reversed order) on `ibm_fez`, jobs sent one at a time. All Part E rules were checked and logged in Part C before each step.
- Results: **H1 FAIL in both rounds** (IBM level 2 is much better on deep circuits); **H2 PASS, H3 PASS in both rounds**. The recipe is best on shallow circuits at about a third of level 2's RU cost. Details in `POC_REPORT.md` section 0.3.
- Usage: about 5.6 RU of 9.9 (343 charged QPU seconds); 4.28 RU remain. Per round, charged seconds: none 27, recipe 29, IBM level 1 30, IBM level 2 83 (`results/hardware_usage.md`, written by `hardware_usage.py` for the reviewer's upgrade-cost estimate). `job.usage()` had shown 0 s for two short jobs; charged seconds come from IBM's job metrics (Part C, after round 2). The trial account expires around 4 Dec 2026; upgrading (card → Pay-As-You-Go) is the owner's decision.
- Recipe v1 is not modified. Any v2 (twirling, smaller scale factors for deep circuits, clipping instead of linear fallback) must be pre-registered and tested on new circuits and new hardware runs.

## Round 7: v2, replication, v1.1 / v1.2 (25-27 Nov 2026)

- **Recipe v2** (Part F, scales 1/2/3 chosen by the reviewer):
  - passed its simulator gate S1;
  - failed G1 on `ibm_marrakesh` (25 Nov): clearly worse than v1 on both circuits.
- **v1 replication** (Part G, 26 Nov):
  - Heisenberg-4 repeated.
  - QPE-4 did not: error 0.015 → 0.291. The guard fired and v1 fell back to linear extrapolation with no warning.
- **v1.1 flag rules** (`decay`, `alive`, `one_exp`, k = 2): fixed from physics before a 0 RU replay of all saved hardware data.
  - The replay used 12 independent cases (device + day + circuit), with an "ambiguous" class.
  - It flagged 4/4 failures but also 3/8 good cases (all by `one_exp`), so v1.1 failed.
  - Rules were not tuned after the replay.
- **v1.2** = v1.1 without `one_exp`: the reviewer's choice after the replay, so post hoc.
  - Part H: four new circuits, none + v1 only, no IBM levels, 0.5 RU reserve.
  - T1 PASS on 4/4, but no flag fired.
- **Final decisions (reviewer, 27 Nov):**
  - **v1 stays as it is.**
  - The v1.2 flags are reported as an **untested safety net**.
  - **Hardware stops** (0.633 RU left).
  - **No claim about IBM's resilience levels** for now.
  - The Draper-adder-4 bias (0.805 vs 1.0, clean decay, no flag) is recorded as a limitation.
- **Record:** git tag `poc-final-20261127`, `results/FINGERPRINTS.md`, and raw counts copied to `results/raw_counts/` with SHA-256 sums.

## Seeds and repeats

- 10-20 transpiler seeds; report best of seeds. (Implemented: 20 seeds, best = fewest two-qubit gates, then lowest depth.)
- Every configuration repeated 10 times; report mean and spread. (Implemented: 10 simulator seeds.)
- **Seed selection never uses the measured error.** The best seed is chosen on compile metrics only (two-qubit count, then depth), before any simulation; repeats then use fresh simulator seeds. ESP is also acceptable as a selection metric. Choosing on TVD and then reporting that TVD would be optimistic.
- Do not claim "level 3 is better than level 2" unless the gap is outside the spread. On Kingston it is outside the spread for 5 of 10 circuits, but only QFT-3 and QFT-4 have fewer two-qubit gates at level 3. For the other three, both levels use the same gate count and the gap comes from which physical qubits were picked (see the level 2 vs level 3 table in `results/baseline_FakeKingston.md`).

## Backends and noise

- Fake backends are old calibration snapshots. Use them to build methods; validate on hardware later.
- Target hardware is **Kingston (Heron r2)**. Run on both `FakeSherbrooke` (Eagle) and `FakeKingston`, and keep both tables.
- Also check robustness by scaling noise from 0.5x to 2x. *(Not implemented yet.)*

## Error metrics

| Circuit type | Primary | Secondary |
|---|---|---|
| Counts circuits | TVD vs exact distribution | Hellinger fidelity |
| QAOA | Approximation ratio or expected cut | none |
| Expectation-value circuits | RMSE vs exact value of one fixed observable per circuit | none |

Fixed observables for expectation-value circuits (implemented in `mitigation.py`):

| Circuit | Observable | Exact |
|---|---|---|
| Bell | ⟨ZZ⟩ | 1 |
| GHZ-3, GHZ-5 | X-parity ⟨X⊗n⟩ | 1 |
| Grover-2, Grover-3 | P(target) | 1, 0.945 |
| QFT-3 | Input \|5⟩ = \|101⟩, QFT, then ⟨X_j⟩ and ⟨Y_j⟩ on every qubit (6 values) | cos and sin of each qubit's phase |
| QFT-4 | Input \|11⟩ = \|1011⟩, same (8 values) | cos and sin of each qubit's phase |
| BV-4 | P(1011) | 1 |
| QAOA-3, QAOA-4 | Expected cut | 1.988, 3.0 |

- GHZ uses **X**-parity, not Z-parity: the Z-parity of an odd-size GHZ state is 0 whatever the noise, so it cannot measure error.
- QFT: a Z-basis readout after QFT is uniform and uninformative, so a non-zero basis state goes in and each qubit is measured in X (H before measure) and Y (S† then H).
- Exact values come from the noise-free statevector of the same measurement circuits. On a noise-free simulator all three methods reproduce them within shot noise.

Report median and per-circuit change alongside the mean, because Grover-3 and QFT-4 dominate the mean.

## Open items

- ~~mitiq needs Python < 3.13.~~ Resolved 19 Nov 2026: the research venv now runs on Python 3.12 with mitiq 1.1.0 (see `requirements.txt`). Baseline results are identical to the Python 3.13 run.
- **mitiq gate folding is wrong on ECR backends.** `zne_smoke.py` shows that on `FakeSherbrooke`, folding for scale factors 1/3/5 actually multiplies the two-qubit gate count by 1/5/9, and Richardson extrapolation overshoots (P(correct) 1.112 for QFT-4, 1.045 for Grover-3). On `FakeKingston` (CZ) the scaling is a correct 1/3/5 (QFT-4: 0.925 raw → 0.961 ZNE; Grover-3: 0.851 → 0.929). Most likely cause: mitiq converts through OpenQASM 2, where ECR is not a standard gate. Proposed fix: fold natively in Qiskit and use mitiq only for the extrapolation. Needs agreement before the ZNE baseline.
- QFT observable for the RMSE metric is not chosen yet.
