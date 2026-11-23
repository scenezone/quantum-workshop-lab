# Proof of concept: choosing error mitigation per circuit (simulation)

GoQuantum Labs · optimization and error-mitigation layer · simulation results, 21 November 2026, updated 23 November 2026

**Status:** simulator only. No real-hardware data yet. All numbers come from Qiskit Aer using noise models of IBM devices (`FakeKingston`, Heron r2; `FakeSherbrooke`, Eagle). The mitigation methods are our own implementations, **not** Qiskit Runtime resilience levels, which have no effect on simulated backends.

## 0. Update, 23 November: pre-registered test on held-out circuits

**What changed.** After the 21 November results (Sections 1-8), the success criteria were recalibrated toward worst-case and deep-circuit error. To avoid fooling ourselves, the new targets were written down **before** any new result existed, and they were tested on **six new circuits** that were not used to design the method (`PREREGISTRATION.md`).

1. **Targets first.** Part A (targets, held-out circuits, metrics, budget) was written at 11:14, before any new run. Its SHA-256 (`042725…1906`) is recorded in the next run's manifest.
2. **Recipe designed on training circuits only.** The 14 training circuits were rerun with a guarded exponential extrapolation (exponential, falling back to linear if the result leaves the observable's physical range) and a budget in quantum seconds. The recipe was designed on that run and then frozen (Part B, 11:22; `recipe.py` SHA-256 `0b08bb…7428`).
3. **Held-out test.** The six held-out circuits were simulated once, against the frozen recipe; the run recorded the Part A+B hash `15bb25…a15`. The code refuses to run the held-out set before the recipe is frozen.

**Budget is now quantum seconds.** Every method gets the same estimated QPU time per circuit, 3.0 s, where estimated QPU time = Σ shots × (circuit duration + 250 µs repetition delay). Shots are derived from it, so ZNE, whose folded circuits are longer, gets slightly fewer shots (for example 10,495 vs 11,267 on Grover-4-3it). On hardware the budget will be the measured `quantum_seconds` of each job.

**Recipe v1.** Use readout correction plus ZNE (1/3/5). For each observable, extrapolate exponentially only if the measured values decay steadily toward the fully-mixed value from a clear distance (same sign, shrinking, |d₁| ≥ 0.1 × range); otherwise extrapolate linearly. The exponential result also falls back to linear if it leaves the physical range. These checks use measured values only, never the exact answer.

**Held-out results** (`FakeKingston`, 10 repeats, RMSE vs exact, mean ± std; run `20261123-112303_mitigation-test`):

| Circuit | 2q gates | None | Readout | F = Readout+ZNE (linear) | Recipe |
|---|---|---|---|---|---|
| Ising-4 (Trotter) | 36 | **0.0045 ± 0.0040** | 0.0051 ± 0.0035 | 0.0088 ± 0.0091 | 0.0088 ± 0.0091 |
| Mirror-4 | 12 | 0.0646 ± 0.0015 | 0.0400 ± 0.0044 | 0.0072 ± 0.0047 | **0.0048 ± 0.0027** |
| Grover-4, 3 iterations | 111 | 0.2246 ± 0.0033 | 0.2028 ± 0.0057 | 0.1201 ± 0.0141 | **0.0186 ± 0.0122** |
| QFT-6 | 88 | 0.0485 ± 0.0036 | 0.0407 ± 0.0026 | **0.0231 ± 0.0050** | 0.0231 ± 0.0058 |
| QAOA-5 ring, p=2 | 34 | 0.1185 ± 0.0048 | 0.0692 ± 0.0060 | **0.0140 ± 0.0121** | 0.0146 ± 0.0091 |
| QAOA-6 prism | 31 | 0.1045 ± 0.0075 | 0.0584 ± 0.0098 | 0.0176 ± 0.0150 | **0.0163 ± 0.0152** |

| Pre-registered target | Result | Detail |
|---|---|---|
| T1 worst case: recipe worst ≤ 0.80 × F worst | **PASS** | 0.0231 vs 0.80 × 0.1201 = 0.0961 |
| T2 deep circuits: mean ≤ 0.85 × F (5 deep circuits) | **PASS** | 0.0163 vs 0.85 × 0.0367 = 0.0312 (recipe 56% lower) |
| T3 no harm: clearly worse than F on ≤ 1 circuit | **PASS** | 0 circuits |
| **O1, original plan target**: median −10% vs best fixed | **NOT MET** | median −3.7%. Also not met on the 21 Nov training run (0%). Kept as the original criterion |

Across all 11 method variants on the held-out set, the recipe had the **lowest worst-case error** (0.0231; next best readout+ZNE expg 0.0307, readout+ZNE Richardson 0.0447) and the lowest median (0.0155).

**What this does and does not show.** The recipe's value is in avoiding large failures, especially on deep circuits (Grover-4-3it: 0.1201 → 0.0186). It is not in improving the typical circuit, where a good fixed method is already about as accurate. One held-out observable turned out to be uninformative: Ising-4's exact magnetization (−0.010) is almost equal to its fully-mixed value (0), so noise barely moves it and no method beat doing nothing. We keep it as defined, because changing a held-out circuit after seeing its result would defeat the test. This is still simulation on one noise model; whether it holds on hardware is the next step (Section 9).

*Sections 1-8 are the 21 November exploratory results (equal shots, not quantum seconds). They motivated the recipe and are kept unchanged.*

## 1. Summary

1. **No single mitigation method is best for every circuit.** At an equal budget of 12,000 shots, readout correction combined with zero-noise extrapolation (ZNE) gave the lowest median error. But which extrapolation works depends on the circuit, and the wrong choice can be much worse than doing nothing.
2. **Readout+ZNE cut the median error by 81% vs no mitigation** (median RMSE 0.0443 → 0.0110, 14 circuits on `FakeKingston`). Readout correction alone cut it by 56%. ZNE alone cut it by only 23-36%, because it does not correct measurement error.
3. **ZNE pays off where gate noise dominates.** It clearly beat readout correction alone on four circuits. Three of them (Grover-3, Grover-4 and QAOA-4 with p=2) have by far the largest error left after readout correction; the fourth is GHZ-7. For example, Grover-4 went from 0.1365 to 0.0108. On shallow circuits the gain was within the run-to-run spread.
4. **Extrapolation choice is a bias-variance trade-off.** Richardson removes bias but triples the spread on QFT circuits. Linear is stable but biased on deep circuits. Exponential is best on deep circuits but fails badly when an observable's exact value equals its fully-noisy value (QFT-3: RMSE 1.05). This is the decision a per-circuit advisor has to make.
5. **Headroom for an advisor is concentrated, not broad.** Picking the best method per circuit, with hindsight, beats the best fixed method on 6 of 14 circuits: by 81% on Grover-4, 45% on QAOA-4 p=2, and 5-20% on the other four. It leaves the median unchanged (0%). Gains therefore show up in worst-case and deep-circuit error, not in the median.
6. **Compilation:** on `FakeKingston`, optimization level 2 used 45% fewer two-qubit gates than level 0 and cut mean TVD by 74% (11 non-QAOA circuits). Level 3 was better than level 2 beyond the spread on 7 of 14 circuits, but only 3 of those (QFT-3/4/5) had fewer gates. The other 4 differed only in which physical qubits were picked.
7. **Seed selection by ESP rarely changes the result.** On `FakeKingston` it picked the same circuit as "fewest gates" in 39 of 42 cases. On `FakeSherbrooke` it was better in 5 of 42 cases (all QAOA) and worse in 1. On simulators this test is partly circular; it has to be confirmed on hardware.

## 2. Question

Can a thin layer on top of Qiskit pick error-mitigation settings per circuit and measurably beat fixed settings at the same shot budget? This report covers the simulation stage. It establishes baselines, finds where the methods differ, and measures how much room there is for automatic selection.

## 3. Method

**Circuits (14).** Ten core circuits (Bell; GHZ-3/5; Grover-2/3; QFT-3/4; Bernstein-Vazirani-4; QAOA MaxCut p=1 on a triangle and a 4-ring) and four deeper ones added to find where ZNE pays off (GHZ-7; Grover-4 with 2 iterations; QFT-5; QAOA 4-ring with p=2).

**Observables, with exact values from the noise-free statevector.**

| Circuit | Observable |
|---|---|
| Bell | ⟨ZZ⟩ |
| GHZ-n | X-parity ⟨X⊗n⟩ (the Z-parity of an odd GHZ state is 0 at any noise level, so it cannot show error) |
| Grover, BV | Probability of the correct bitstring |
| QFT-n | QFT applied to a non-zero basis state (\|5⟩, \|11⟩, \|21⟩), then ⟨X⟩ and ⟨Y⟩ on every qubit. The exact values are cos and sin of each qubit's phase; a Z-basis readout would be uniform and uninformative |
| QAOA | Expected cut |

**Compilation.** Transpiler optimization level 2, best of 20 transpiler seeds (fewest two-qubit gates, then depth), chosen before any simulation.

**Equal budget.** Every method gets 12,000 shots per circuit, including calibration shots and every ZNE scale factor.

**Methods.**
- **Readout:** tensored per-qubit confusion matrices from all-0 and all-1 calibration circuits on the circuit's physical qubits (20% of the shots).
- **ZNE:** native unitary folding of the compiled circuit at scale factors 1, 3 and 5, with the shots split equally. Folding is done after transpilation, with no re-optimization, so inverse pairs cannot cancel. We verified that the two-qubit gate count scales exactly 1x/3x/5x on every circuit, and that the folded circuits are equivalent to the originals. Extrapolation uses mitiq 1.1.0: Richardson, linear least squares, or exponential with a known asymptote.
- **Readout+ZNE:** every folded circuit is readout-corrected first, then extrapolated.

**Repeats and metric.** 10 repeats. Each distinct circuit is simulated once with all the shots it needs, and the shot record is split into disjoint chunks, one per repeat and method. The metric is RMSE of the observables against their exact values, reported as mean ± std over repeats. "Clearly better" means the gap is larger than the combined std.

**Reproducibility.** Every run writes a manifest (command, configuration, seeds, method, package versions) and the raw counts to its own folder (Section 8). The analysis reads only the saved counts.

## 4. Results: mitigation at equal budget (`FakeKingston`)

RMSE vs exact (mean ± std over 10 repeats; lower is better). "Best" is over all eight method variants.

| Circuit | 2q gates | None | Readout | Readout+ZNE (linear) | Readout+ZNE (exp) | Best |
|---|---|---|---|---|---|---|
| Bell | 1 | 0.0228 ± 0.0022 | 0.0051 ± 0.0028 | 0.0027 ± 0.0026 | 0.0027 ± 0.0026 | Readout+ZNE (linear) |
| GHZ-3 | 2 | 0.0500 ± 0.0033 | 0.0089 ± 0.0055 | 0.0079 ± 0.0063 | 0.0080 ± 0.0063 | Readout+ZNE (linear) |
| GHZ-5 | 4 | 0.0722 ± 0.0043 | 0.0150 ± 0.0063 | 0.0108 ± 0.0065 | 0.0110 ± 0.0067 | Readout+ZNE (linear) |
| GHZ-7 | 6 | 0.1104 ± 0.0031 | 0.0258 ± 0.0136 | 0.0088 ± 0.0055 | 0.0106 ± 0.0054 | Readout+ZNE (linear) |
| Grover-2 | 2 | 0.0151 ± 0.0014 | 0.0074 ± 0.0041 | 0.0048 ± 0.0028 | 0.0049 ± 0.0029 | Readout+ZNE (linear) |
| Grover-3 | 37 | 0.0931 ± 0.0032 | 0.0723 ± 0.0060 | 0.0112 ± 0.0075 | 0.0107 ± 0.0048 | Readout+ZNE (exp) |
| Grover-4 | 73 | 0.1574 ± 0.0034 | 0.1365 ± 0.0061 | 0.0563 ± 0.0130 | 0.0108 ± 0.0141 | Readout+ZNE (exp) |
| QFT-3 | 18 | 0.0242 ± 0.0028 | 0.0166 ± 0.0039 | 0.0207 ± 0.0073 | 1.0489 ± 3.1490 | Readout |
| QFT-4 | 34 | 0.0346 ± 0.0017 | 0.0256 ± 0.0023 | 0.0238 ± 0.0094 | 0.1233 ± 0.1871 | ZNE (linear), 0.0227 |
| QFT-5 | 56 | 0.0386 ± 0.0023 | 0.0266 ± 0.0027 | 0.0238 ± 0.0045 | 0.0884 ± 0.0760 | Readout+ZNE (linear) |
| BV-4 | 3 | 0.0284 ± 0.0010 | 0.0073 ± 0.0046 | 0.0034 ± 0.0042 | 0.0034 ± 0.0042 | Readout+ZNE (linear) |
| QAOA-3 | 7 | 0.0187 ± 0.0024 | 0.0074 ± 0.0041 | 0.0039 ± 0.0028 | 0.0043 ± 0.0029 | Readout+ZNE (linear) |
| QAOA-4 | 11 | 0.0514 ± 0.0101 | 0.0174 ± 0.0095 | 0.0212 ± 0.0087 | 0.0223 ± 0.0099 | Readout |
| QAOA-4 p=2 | 25 | 0.1743 ± 0.0068 | 0.1199 ± 0.0085 | 0.0311 ± 0.0181 | 0.0170 ± 0.0155 | Readout+ZNE (exp) |

Across all 14 circuits:

| Method | Best on | Median RMSE | Median change vs none |
|---|---|---|---|
| None | 0 | 0.0443 | 0% |
| Readout | 2 | 0.0170 | −56% |
| ZNE (Richardson / linear / exp) | 0 / 1 / 0 | 0.0343 / 0.0279 / 0.0366 | −23% / −36% / −24% |
| Readout+ZNE (Richardson) | 0 | 0.0183 | −68% |
| Readout+ZNE (linear) | 8 | 0.0110 | −81% |
| Readout+ZNE (exp) | 3 | 0.0107 | −84% |

For every circuit, the best of the four main methods (none, readout, ZNE and readout+ZNE, all with Richardson) beats no mitigation by more than the spread.

### 4.1 When does ZNE pay off?

ZNE adds variance: it spreads the shots over three noise levels, and the extrapolation amplifies their noise. So it only helps when the bias it removes is larger than the variance it adds.

- **Clearly better than readout correction alone:** Grover-3, Grover-4, QAOA-4 p=2 and GHZ-7. The first three have by far the largest error left after readout correction (0.072-0.137). GHZ-7's is 0.026, about the same as QFT-4 and QFT-5, where ZNE did not clearly help. All four have an estimated success probability (ESP) from calibration data of 0.94 or below, but so do QFT-4 and QFT-5. Neither measure alone predicts the outcome.
- **Within the spread or worse:** the shallow circuits (1-11 two-qubit gates). Readout error dominates there, and readout correction already captures most of the gain.
- **QFT is the exception.** Its error after readout correction is already close to the shot-noise level, so ZNE removes bias but adds more variance than it saves. On QFT-3, Richardson ZNE moves ⟨X₀⟩ from −0.688 to −0.703 (exact −0.707), but its std rises from 0.012 to 0.041.

### 4.2 Extrapolation choice

| Fit | Strength | Failure mode seen |
|---|---|---|
| Richardson | Lowest bias | High variance: worst RMSE on QFT despite the best mean |
| Linear | Low variance; best on QFT and shallow circuits | Biased on deep circuits, where decay is curved (Grover-4: 0.0563 vs 0.0108 for exp) |
| Exponential (known asymptote) | Best on deep circuits (Grover-3/4, QAOA-4 p=2) | Unstable when an observable's exact value equals its fully-mixed value. QFT-3 has ⟨X₁⟩ = ⟨Y₂⟩ = 0, and readout+ZNE (exp) RMSE reaches 1.05 ± 3.15 |

### 4.3 Headroom for a per-circuit advisor

Choosing the best of the eight variants per circuit, with hindsight, is an upper bound on what an advisor could achieve. Compared with the best single fixed method (readout+ZNE linear), it improves 6 of 14 circuits: Grover-4 by 81%, QAOA-4 p=2 by 45%, QFT-3 by 20%, QAOA-4 by 18%, and Grover-3 and QFT-4 by 5% each. The median improvement is **0%** and the mean is 12%.

The fixed method with the lowest median (readout+ZNE exp, 0.0107) also has the worst failure (1.05 on QFT-3). That is exactly the case where choosing per circuit matters.

## 5. Results: compilation and seed selection

**Optimization levels** (`FakeKingston`, best of 20 seeds per level). Gates, depth and TVD are totals or means over the 11 non-QAOA circuits; the 3 QAOA circuits are scored by approximation ratio.

| Level | Total 2q gates | Total depth | Mean TVD | Mean QAOA ratio |
|---|---|---|---|---|
| 0 | 331 | 1371 | 0.220 | 0.839 |
| 1 | 232 | 904 | 0.138 | 0.893 |
| 2 | 183 | 680 | 0.057 | 0.894 |
| 3 | 177 | 640 | 0.053 | 0.896 |

Level 3 beat level 2 beyond the spread on 7 of 14 circuits. Only QFT-3, QFT-4 and QFT-5 had fewer two-qubit gates (7 vs 9, 14 vs 17, 28 vs 29). On the other 4, both levels used the same gate count and the gap came from which physical qubits were picked. We therefore do not claim that level 3 is generally better.

**Hardware generation.** The Heron-class noise model gave much lower error on deep circuits. Grover-4 at level 2 had a TVD of 0.155 on `FakeKingston` vs 0.509 on `FakeSherbrooke`.

**Layout matters as much as gate count.** On GHZ-5, level 1 kept physical qubits 0-4, which include a qubit with a 16.8% readout error on `FakeKingston`, and reached a TVD of 0.204. Level 2 moved to better qubits and reached 0.037 with the same 4 two-qubit gates.

**Seed selection: fewest gates (A) vs highest ESP (B).** Both strategies choose among the same 20 compiled candidates using compile-time information only. We compared them on 14 circuits × levels 1-3 × both backends (84 cases), with no mitigation:

| Backend | Same circuit picked | No difference (within spread) | ESP better | Gates better |
|---|---|---|---|---|
| `FakeKingston` | 39 | 3 | 0 | 0 |
| `FakeSherbrooke` | 30 | 6 | 5 | 1 |

On `FakeKingston` the choice did not matter: the transpiler's noise-aware layout already converges on the same circuit. On `FakeSherbrooke`, ESP won on 5 cases, all QAOA (QAOA-4 at levels 1-3, QAOA-4 p=2 at levels 2-3). There it picked circuits with 1-3 *more* two-qubit gates, with lower depth in 4 of the 5 cases, for example QAOA-4 p=2 at level 2: approximation ratio 0.905 vs 0.879. ESP lost on QFT-5 at level 1 (TVD 0.347 vs 0.307), so even where it is partly circular it is not a perfect predictor; one likely reason is that it ignores idle decoherence.

A caution about single runs: an earlier Kingston-only run found ESP better on QFT-5 at level 2 (TVD 0.092 vs 0.104). The repeat with fresh simulator seeds put the gap within the spread (0.097 vs 0.103). Differences of this size need repeated runs before they are reported.

## 6. Cost

Shots are equal by construction. With the backend's default repetition delay of 250 µs per shot, per-shot overhead dominates these short circuits, so ZNE under the equal-shot rule is estimated at ×1.00-1.07 the QPU time of no mitigation (gate time ×1.1-2.6). If each scale factor got the full budget instead, the estimate is ×3.0-3.2 QPU time and ×3.3-7.8 gate time. These are estimates from gate durations; real `quantum_seconds` will be measured in the hardware phase.

## 7. Limitations

- **Simulation only.** The noise models are fixed calibration snapshots. Real devices drift, and have crosstalk and correlated readout errors that these models leave out.
- **Partly circular.** The noise model and ESP come from the same calibration data, so ESP agreeing with simulated error shows consistency, not predictive power on hardware.
- **Readout model.** Tensored correction assumes independent readout errors per qubit.
- **Scope.** One budget (12,000 shots), one optimization level for mitigation (2), 14 small circuits (at most 7 qubits, at most 73 two-qubit gates), one noise strength. Robustness under 0.5x-2x noise scaling has not been tested yet.
- **The headroom in 4.3 is an upper bound.** It uses hindsight. A real advisor must choose from circuit features before running.

## 8. Conclusion and next steps

The simulation supports the plan's premise in a narrower form than first stated. Mitigation helps a lot: −81% median error with readout+ZNE. The right choice also depends on the circuit, especially the extrapolation. A strong fixed combination already captures most of the median gain, though, so the case for an advisor rests on **avoiding failure modes and improving deep circuits**, not on the median.

Proposed next steps:

1. A rule-based advisor v1 using features available before running: two-qubit count, ESP, observable type, and whether an observable's exact value is near its fully-mixed value. Evaluate it on circuits not used to design the rules. *(Done 23 Nov as recipe v1, which uses measured decay instead of the exact value; see Section 0.)*
2. Recalibrate the success threshold. "Median error −10% vs best fixed default" is not reachable against readout+ZNE (linear), even with hindsight. A worst-case or deep-circuit metric would fit the evidence better. *(Done 23 Nov: pre-registered T1-T3, all passed on held-out circuits; the original target is kept and remains not met.)*
3. Noise scaling 0.5x-2x, then hardware validation of 2-3 results, including measured `quantum_seconds`. *(Hardware plan in Section 9; noise scaling not done yet.)*

**Runs behind this report** (under `research/results/runs/`; each has `manifest.json` and raw counts):

| Run | Contents | Command |
|---|---|---|
| `20261121-141214_mitigation` | Section 4, Section 6 | `python mitigation.py` |
| `20261121-141802_baseline` | Section 5, optimization levels and backends | `python baseline.py` |
| `20261121-142309_selection` | Section 5, seed selection | `python selection_compare.py --backends FakeKingston FakeSherbrooke --levels 1 2 3` |
| `20261121-141701_selection` | Earlier Kingston-only seed-selection run (the single-run caution in Section 5) | `python selection_compare.py` |
| `20261123-111818_mitigation-train` | Section 0: training rerun (guard, quantum-seconds budget); recipe designed on it | `python mitigation.py --set train` |
| `20261123-112303_mitigation-test` | Section 0: held-out test of the frozen recipe; pre-registered targets | `python mitigation.py --set test` |
| `20261123-115437_hardware-dryrun` | Section 9: hardware pipeline dry run (not evidence) | `python hardware.py` |

The 21 November commands refer to the code as it was on that date; the scripts have since gained options. The GHZ-5 layout figures come from `python layout_check.py`.

## 9. Next: hardware validation (planned, not run)

Plan (`hardware.py`, targets H1-H3 pre-registered in `PREREGISTRATION.md` A7):

- **Circuits:** Bell and GHZ-5 as sanity checks, plus the 6 held-out circuits.
- **Methods:** no mitigation; our recipe; IBM Runtime Estimator resilience levels 1 and 2.
- **Jobs:** five in total (none; recipe folded circuits; recipe calibration; level 1; level 2), so every job's measured `quantum_seconds` belongs to one method.
- **Budget:** about 3 s per circuit per method. IBM SamplerV2 requires one shot count per job, so the budget is equalized per method total rather than per circuit (logged in Part C). Shots per PUB: 10,426 for no mitigation and the IBM levels; 2,728 per scale factor and 1,023 per calibration circuit for the recipe.
- **Estimated QPU time:** no mitigation 24 s, recipe 24 s, IBM level 1 about 23 s, IBM level 2 about 63 s. The level 1 and level 2 figures are planning guesses (level 2 assumes 3× for its ZNE); IBM's real overhead will be measured. **Total ≈ 135 s.**
- **Dry run:** the full pipeline was exercised locally on `FakeKingston`. The Sampler jobs ran; the Estimator jobs were built and checked but cannot run in local mode (Section 9 report in the dry-run folder).

Before submitting: confirm the IBM plan's remaining minutes and which Heron device is available, and get approval to spend about 2.5-3.5 minutes of QPU time.
