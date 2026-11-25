"""Recipe v2 vs v1 in the simulator, at an equal estimated QPU-time budget (PREREGISTRATION.md Part F).

Methods (our own implementations, not Qiskit Runtime resilience levels):

  none        all of the budget on the compiled circuit
  F           readout + ZNE at 1/3/5 (all gates folded), linear                    (v1-era reference)
  recipe_v1   recipe.py, frozen 23 Nov, on the same data group as F
  v1_clip     v1 data, v2 rule (exp/linear branch, then clip): isolates the clipping change
  v2_notwirl  two-qubit folding at 1/1.5/2, no twirling, v2 rule: isolates the scale-factor change
  recipe_v2   recipe_v2.py: twirled two-qubit folding at 1/1.5/2, readout-corrected, v2 rule

Data groups (each gets the same estimated quantum seconds per circuit): none, v1 (F, recipe_v1, v1_clip),
v2nt (v2_notwirl), v2 (recipe_v2). Calibration is 20% of the shots of every readout group.

Twirled circuits are drawn independently for every repeat (TWIRLS instances per scale per repeat) and each is
simulated with its own seed; circuits shared by all repeats (the compiled circuit, folds, calibration) are
simulated once and their shot record is split into disjoint chunks, as in mitigation.py.

Sets:
  train    the 14 training circuits (design only; seen data)
  test     the 2 v2 held-out circuits (heldout_v2.py); refused until recipe_v2.FROZEN

    .venv/Scripts/python mitigation_v2.py --set train [--noise-scale 2]
    .venv/Scripts/python mitigation_v2.py --set test
    .venv/Scripts/python mitigation_v2.py --analyze results/runs/<id>_mitigation-v2-<set>
"""

from __future__ import annotations

import argparse
import csv
import math
import shutil
import statistics
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import fake_provider

import recipe
import recipe_v2
import runlog
from baseline import compile_best_of_seeds, measured_physical_qubits, to_probs
from folding import fold
from heldout_v2 import heisenberg, qpe
from mitigation import (
    OPT_LEVEL,
    TRANSPILE_SEEDS,
    Task,
    _single,
    apply_readout_correction,
    calibration_circuits,
    confusion_matrix,
    exact_distribution,
    extrapolate,
    parity,
    probability,
    rmse,
    scaled_backend,
)
from mitigation import tasks as v1_tasks
from twirl import fold_2q_series, twirl, two_qubit_count

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message="The extrapolation fit may be ill-conditioned")

SIM_SEED_BASE = {"train": 50_000, "test": 70_000}  # disjoint from every earlier run's simulator seeds
DEFAULT_BUDGET_QS = 3.0
DEEP_MIN_2Q = 13
V1_SCALES = (1, 3, 5)
V1_KEYS = ("s1", "s3", "s5")
V2_KEYS = ("q1", "q15", "q2")  # nominal 1, 1.5, 2 (two-qubit folding)
CAL = recipe_v2.CAL_FRACTION
GROUPS = ("none", "v1", "v2nt", "v2")
METHODS = ("none", "F", "recipe_v1", "v1_clip", "v2_notwirl", "recipe_v2")
LABEL = {"none": "None", "F": "F: readout+ZNE 1/3/5 linear", "recipe_v1": "Recipe v1", "v1_clip": "v1 data + clip",
         "v2_notwirl": "1/1.5/2 + clip, no twirl", "recipe_v2": "Recipe v2"}
FRACTIONS = {
    "none": {"s1": 1.0},
    "v1": {**{k: (1 - CAL) / 3 for k in V1_KEYS}, "cal0": CAL / 2, "cal1": CAL / 2},
    "v2nt": {**{k: (1 - CAL) / 3 for k in V2_KEYS}, "cal0": CAL / 2, "cal1": CAL / 2},
    "v2": {**{k: (1 - CAL) / 3 for k in V2_KEYS}, "cal0": CAL / 2, "cal1": CAL / 2},
}


METHOD_TEXT = [
    "Our own implementations on Qiskit Aer with the fake backend's noise model; NOT Qiskit Runtime resilience levels.",
    f"Compilation: level {OPT_LEVEL}, best of {len(TRANSPILE_SEEDS)} seeds (fewest 2q gates, then depth), identical "
    "to mitigation.py.",
    "Budget: every data group gets the same estimated quantum seconds per circuit (sum of shots x (duration + rep "
    "delay)), including 20% calibration shots for readout groups.",
    "v1 group: all-gate native folding at 1/3/5 (folding.py). v2 groups: two-qubit-only folding at nominal 1/1.5/2 "
    "(twirl.fold_2q_series; actual scales used in fits). recipe_v2: every CZ Pauli-twirled, "
    f"{recipe_v2.TWIRLS} independent instances per scale per repeat, counts pooled over instances.",
    "Readout correction (tensored, per-qubit) of every scale before extrapolation; extrapolation with mitiq 1.1.0 "
    "(linear; exponential with known asymptote).",
    "Metric: RMSE vs exact noise-free value per repeat; mean +- std over repeats.",
]


# ----------------------------------------------------------------- tasks


def staggered_magnetization(probs: dict[str, float]) -> float:
    n = len(next(iter(probs)))
    return sum((-1) ** j * parity(probs, [j]) for j in range(n)) / n


def test_tasks() -> list[Task]:
    """PREREGISTRATION.md Part F: the two v2 held-out circuits."""
    h = heisenberg()
    q, answer = qpe()
    return [
        _single(h, "Z", "M_stag", staggered_magnetization, -1.0, 1.0, "staggered magnetization (1/4) sum (-1)^j <Z_j>",
                "heldout-v2"),
        _single(q, "Z", f"P({answer})", probability(answer), 0.0, 1.0, f"P({answer}), the 4-bit phase 11/16",
                "heldout-v2"),
    ]


def tasks(which: str) -> list[Task]:
    if which == "train":
        return v1_tasks("train")
    out = test_tasks()
    for task in out:
        exact = {b: exact_distribution(qc) for b, qc in task.circuits.items()}
        for obs in task.observables:
            n = len(next(iter(exact[obs.basis])))
            obs.exact = obs.value(exact[obs.basis])
            obs.asymptote = obs.value({format(i, f"0{n}b"): 1 / 2**n for i in range(2**n)})
    return out


# -------------------------------------------------------------- simulate


def plan_shots(per_shot: dict[str, dict[str, float]], fractions: dict[str, float], budget_qs: float) -> dict:
    """shots[basis][key] so the group's estimated QPU time is (just under) budget_qs.

    per_shot[basis][key] = circuit duration + rep delay (s). For twirled keys the shots are the total over all
    TWIRLS instances of that scale.
    """
    m = len(per_shot)
    time_per_shot = sum(f / m * per_shot[b][k] for b in per_shot for k, f in fractions.items())
    total = budget_qs / time_per_shot
    return {b: {k: int(total * f / m) for k, f in fractions.items()} for b in per_shot}


def _pooled_run(simulator, circuit, per_repeat: dict[str, int], repeats: int, seed: int) -> list[dict]:
    """Run once with all shots (memory=True), split into disjoint chunks per repeat and group."""
    total = repeats * sum(per_repeat.values())
    memory = simulator.run(circuit, shots=total, seed_simulator=seed, memory=True).result().get_memory()
    chunks, pos = [], 0
    for _ in range(repeats):
        rep = {}
        for g, shots in per_repeat.items():
            rep[g] = dict(Counter(memory[pos: pos + shots]))
            pos += shots
        chunks.append(rep)
    return chunks


def simulate(args) -> Path:
    backend = getattr(fake_provider, args.backend)()  # compilation always uses the unscaled backend
    noisy = backend if args.noise_scale == 1 else scaled_backend(args.backend, args.noise_scale)
    simulator = AerSimulator.from_backend(noisy)
    rep_delay = getattr(backend.configuration(), "default_rep_delay", 250e-6) or 250e-6
    all_tasks = tasks(args.set)
    if args.only:
        all_tasks = [t for t in all_tasks if t.name in args.only.split(",")]
    suffix = "" if args.noise_scale == 1 else f"-noise{args.noise_scale:g}"
    seed_base = SIM_SEED_BASE[args.set] + (0 if args.noise_scale == 1 else int(round(args.noise_scale * 100)) * 1000)
    run_dir = runlog.new_run(
        f"mitigation-v2-{args.set}{suffix}" + ("-partial" if args.only else ""),
        config={"set": args.set, "noise_scale": args.noise_scale, "backend": args.backend, "only": args.only,
                "budget_estimated_quantum_seconds_per_method": args.budget_qs, "repeats": args.repeats,
                "optimization_level": OPT_LEVEL, "transpiler_seeds": TRANSPILE_SEEDS, "seed_selection": "gates",
                "v1_scale_factors": V1_SCALES, "v2_nominal_scales": recipe_v2.SCALES, "twirls": recipe_v2.TWIRLS,
                "calibration_fraction": CAL, "simulator_seed_base": seed_base, "rep_delay_s": rep_delay,
                "recipe_v1": recipe.VERSION, "recipe_v2": recipe_v2.VERSION, "recipe_v2_frozen": recipe_v2.FROZEN,
                "deep_min_two_qubit_gates": DEEP_MIN_2Q},
        method=METHOD_TEXT,
    )
    raw: dict = {}
    task_info: dict = {}
    seed = seed_base
    for t_index, task in enumerate(all_tasks):
        info: dict = {}
        shared_by_basis: dict = {}
        twirled_by_basis: dict = {}
        for b_index, (basis, logical) in enumerate(task.circuits.items()):
            best, _, _ = compile_best_of_seeds(logical, backend, OPT_LEVEL, TRANSPILE_SEEDS)
            base = best.circuit
            physical = measured_physical_qubits(base)
            n2q = two_qubit_count(base)
            shared = {k: fold(base, s) for k, s in zip(V1_KEYS, V1_SCALES)}
            assert [two_qubit_count(shared[k]) for k in V1_KEYS] == [s * n2q for s in V1_SCALES], task.name
            actual, folded2q = {}, {}
            for k, (circuit, a) in zip(V2_KEYS, fold_2q_series(base, recipe_v2.SCALES)):
                folded2q[k], actual[k] = circuit, a
                assert two_qubit_count(circuit) == round(a * n2q), (task.name, k)
            shared["q15"], shared["q2"] = folded2q["q15"], folded2q["q2"]
            shared.update(calibration_circuits(backend.num_qubits, physical))
            rng = np.random.default_rng([seed_base, t_index, b_index])
            twirled = [{k: [twirl(folded2q[k], rng) for _ in range(recipe_v2.TWIRLS)] for k in V2_KEYS}
                       for _ in range(args.repeats)]
            duration = {k: c.estimate_duration(backend.target, unit="s") for k, c in shared.items()}
            duration["q1"] = duration["s1"]
            tw_duration = {k: statistics.mean(c.estimate_duration(backend.target, unit="s") for c in twirled[0][k])
                           for k in V2_KEYS}
            per_shot = {g: {k: (tw_duration[k] if (g == "v2" and k in V2_KEYS) else duration[k]) + rep_delay
                            for k in FRACTIONS[g]} for g in GROUPS}
            shared_by_basis[basis], twirled_by_basis[basis] = shared, twirled
            info[basis] = {"best_seed": best.seed, "esp": best.esp, "physical_qubits": physical,
                           "two_qubit_gates": n2q, "actual_v2_scales": actual, "duration_s": duration,
                           "twirled_mean_duration_s": tw_duration, "per_shot_s": per_shot}
        plan = {g: plan_shots({b: info[b]["per_shot_s"][g] for b in info}, FRACTIONS[g], args.budget_qs)
                for g in GROUPS}
        raw[task.name] = {}
        for basis, shared in shared_by_basis.items():
            raw[task.name][basis] = {}
            seeds_used = {}
            for key, circuit in shared.items():
                per_repeat = {}
                for g in GROUPS:
                    plan_key = "q1" if (g == "v2nt" and key == "s1") else key
                    if g == "v2" and key not in ("cal0", "cal1"):
                        continue  # v2 uses its own twirled circuits
                    if plan_key in plan[g][basis]:
                        per_repeat[g] = plan[g][basis][plan_key]
                if not per_repeat:
                    continue
                seed += 1
                seeds_used[key] = seed
                raw[task.name][basis][key] = _pooled_run(simulator, circuit, per_repeat, args.repeats, seed)
            per_instance = {k: max(1, plan["v2"][basis][k] // recipe_v2.TWIRLS) for k in V2_KEYS}
            twirled_counts = []
            for r in range(args.repeats):
                rep = {}
                for k in V2_KEYS:
                    seed += 1
                    circuits = twirled_by_basis[basis][r][k]
                    result = simulator.run(circuits, shots=per_instance[k], seed_simulator=seed).result()
                    pooled = Counter()
                    for i in range(len(circuits)):
                        pooled.update(result.get_counts(i))
                    rep[k] = dict(pooled)
                twirled_counts.append(rep)
            raw[task.name][basis]["twirled"] = twirled_counts
            info[basis]["simulator_seeds_shared"] = seeds_used
            info[basis]["v2_shots_per_instance"] = per_instance
        task_info[task.name] = {
            "group": task.group, "note": task.note, "bases": list(task.circuits),
            "observables": [{"label": o.label, "basis": o.basis, "exact": o.exact, "asymptote": o.asymptote,
                             "low": o.low, "high": o.high} for o in task.observables],
            "shots_per_repeat": plan, "circuits": info,
        }
        print(f"simulated {task.name:13} 2q={sum(i['two_qubit_gates'] for i in info.values())}", flush=True)
    runlog.write_json(run_dir / "counts.json", raw)
    runlog.update_manifest(run_dir, tasks=task_info)
    return run_dir


# --------------------------------------------------------------- analyze


def corrected(counts: dict, cal0: dict, cal1: dict) -> dict[str, float]:
    measured = to_probs(counts)
    n = len(next(iter(measured)))
    return apply_readout_correction(measured, confusion_matrix(to_probs(cal0), to_probs(cal1), n), n)


def estimates_for_repeat(task: Task, raw_task: dict, info: dict, r: int, features: dict) -> tuple[dict, dict]:
    """Every method's estimate of every observable in repeat r, plus the v2 branches used."""
    est = {m: [] for m in METHODS}
    branches = {"recipe_v2": [], "v2_notwirl": [], "v1_clip": [], "recipe_v1": []}
    for o in task.observables:
        b = o.basis
        d = raw_task[b]
        ch = lambda key, g: d[key][r][g]  # noqa: E731
        est["none"].append(o.value(to_probs(ch("s1", "none"))))
        v1_vals = [o.value(corrected(ch(k, "v1"), ch("cal0", "v1"), ch("cal1", "v1"))) for k in V1_KEYS]
        f_lin = extrapolate("linear", v1_vals, o)[0]
        f_expg = extrapolate("expg", v1_vals, o)[0]
        est["F"].append(f_lin)
        v, br = recipe.estimate(features, o, {"readout_zne_linear": f_lin, "readout_zne_expg": f_expg}, v1_vals)
        est["recipe_v1"].append(v)
        branches["recipe_v1"].append(br)
        v, br = recipe_v2.estimate(o, list(V1_SCALES), v1_vals)
        est["v1_clip"].append(v)
        branches["v1_clip"].append(br)
        actual = [info[b]["actual_v2_scales"][k] for k in V2_KEYS]
        nt_vals = [o.value(corrected(ch("s1" if k == "q1" else k, "v2nt"), ch("cal0", "v2nt"), ch("cal1", "v2nt")))
                   for k in V2_KEYS]
        v, br = recipe_v2.estimate(o, actual, nt_vals)
        est["v2_notwirl"].append(v)
        branches["v2_notwirl"].append(br)
        tw = d["twirled"][r]
        v2_vals = [o.value(corrected(tw[k], ch("cal0", "v2"), ch("cal1", "v2"))) for k in V2_KEYS]
        v, br = recipe_v2.estimate(o, actual, v2_vals)
        est["recipe_v2"].append(v)
        branches["recipe_v2"].append(br)
    return est, branches


def analyze(run_dir: Path, out_dir: Path) -> None:
    manifest = runlog.read_json(run_dir / "manifest.json")
    raw = runlog.read_json(run_dir / "counts.json")
    config = manifest["config"]
    which = config["set"]
    repeats = config["repeats"]
    by_name = {t.name: t for t in tasks(which)}
    rows, detail = [], []
    branch_stats = {m: Counter() for m in ("recipe_v1", "v1_clip", "v2_notwirl", "recipe_v2")}
    for name, info in manifest["tasks"].items():
        task = by_name[name]
        for obs, saved in zip(task.observables, info["observables"]):
            assert abs(obs.exact - saved["exact"]) < 1e-9, f"{name}: observable changed since the run"
        circuits = info["circuits"]
        two_qubit = sum(c["two_qubit_gates"] for c in circuits.values())
        features = {"two_qubit_gates": two_qubit}
        per_rep = {m: [] for m in METHODS}
        values = {m: [] for m in METHODS}
        for r in range(repeats):
            est, br = estimates_for_repeat(task, raw[name], circuits, r, features)
            for m in METHODS:
                per_rep[m].append(rmse([e - o.exact for e, o in zip(est[m], task.observables)]))
                values[m].append(est[m])
            for m, bs in br.items():
                branch_stats[m].update(bs)
        row = {"circuit": name, "group": info["group"], "observable": info["note"], "two_qubit_gates": two_qubit,
               "deep": two_qubit >= DEEP_MIN_2Q}
        for m in METHODS:
            row[f"{m}_rmse_mean"] = statistics.mean(per_rep[m])
            row[f"{m}_rmse_std"] = statistics.stdev(per_rep[m]) if repeats > 1 else 0.0
        row["best"] = min(METHODS, key=lambda m: row[f"{m}_rmse_mean"])
        rows.append(row)
        for j, o in enumerate(task.observables):
            cells = [name, o.label, f"{o.exact:+.3f}"]
            for m in METHODS:
                vals = [v[j] for v in values[m]]
                cells.append(f"{statistics.mean(vals):+.3f} ± {statistics.stdev(vals):.3f}")
            detail.append(cells)
    targets = evaluate_sim_targets(rows) if which == "test" else None
    with open(run_dir / "mitigation_v2.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    if targets:
        runlog.write_json(run_dir / "targets.json", targets)
    report = run_dir / "mitigation_v2.md"
    write_markdown(rows, detail, manifest, branch_stats, targets, report)
    out_dir.mkdir(parents=True, exist_ok=True)
    scale = config.get("noise_scale", 1)
    stem = f"mitigation_v2_{config['backend']}_{which}" + ("" if scale == 1 else f"_noise{scale:g}")
    shutil.copy(report, out_dir / f"{stem}.md")
    shutil.copy(run_dir / "mitigation_v2.csv", out_dir / f"{stem}.csv")
    for r in rows:
        print(f"{r['circuit']:13} 2q={r['two_qubit_gates']:<4} " + "  ".join(
            f"{m}={r[f'{m}_rmse_mean']:.4f}" for m in METHODS) + f"  best={r['best']}")
    if targets:
        for t in targets:
            print(f"{t['id']}: {'PASS' if t['passed'] else 'FAIL'}  {t['detail']}")
    print(f"\nReport: {report}")


def _clearly(row: dict, better: str, worse: str) -> bool:
    gap = row[f"{worse}_rmse_mean"] - row[f"{better}_rmse_mean"]
    return gap > math.hypot(row[f"{better}_rmse_std"], row[f"{worse}_rmse_std"])


def evaluate_sim_targets(rows: list[dict]) -> list[dict]:
    """PREREGISTRATION.md Part F, simulator targets S1-S2, on the v2 held-out circuits."""
    s1 = [r for r in rows if r["recipe_v2_rmse_mean"] > 1.25 * r["recipe_v1_rmse_mean"]]
    s2 = [r for r in rows if not _clearly(r, "recipe_v2", "none")]
    return [
        {"id": "S1 no harm vs v1 (simulator)", "passed": not s1,
         "detail": "; ".join(f"{r['circuit']}: v2 {r['recipe_v2_rmse_mean']:.4f} vs 1.25 x v1 "
                             f"{1.25 * r['recipe_v1_rmse_mean']:.4f}" for r in rows)},
        {"id": "S2 beats no mitigation (simulator)", "passed": not s2,
         "detail": "; ".join(f"{r['circuit']}: v2 {r['recipe_v2_rmse_mean']:.4f} ± {r['recipe_v2_rmse_std']:.4f} vs none "
                             f"{r['none_rmse_mean']:.4f} ± {r['none_rmse_std']:.4f}" for r in rows)},
    ]


def write_markdown(rows, detail, manifest, branch_stats, targets, path: Path) -> None:
    config = manifest["config"]

    def cell(r, m):
        text = f"{r[f'{m}_rmse_mean']:.4f} ± {r[f'{m}_rmse_std']:.4f}"
        return f"**{text}**" if r["best"] == m else text

    lines = [
        f"# Recipe v2 vs v1: {config['backend']}, {config['set']} set, noise ×{config.get('noise_scale', 1):g} (simulator)",
        "",
        f"Run `{manifest['run_id']}` · budget **{config['budget_estimated_quantum_seconds_per_method']} estimated quantum "
        f"seconds per circuit per data group** · {config['repeats']} repeats · {config['twirls']} twirls per scale per "
        f"repeat · recipe v2 frozen: {config['recipe_v2_frozen']} · pre-registration SHA-256 "
        f"`{(manifest.get('preregistration_sha256') or 'none')[:12]}…`.",
        "",
        "**Our own implementations, not Qiskit Runtime resilience levels.** The fake-backend noise model has no "
        "coherent errors, so twirling is expected to change little here (see `python twirl.py` for a coherent-noise "
        "check). The simulator also did not reproduce the hardware failure of v1 on deep circuits.",
        "",
    ]
    if targets:
        lines += ["## Pre-registered simulator targets (PREREGISTRATION.md Part F)", "",
                  "| Target | Result | Detail |", "|---|---|---|",
                  *(f"| {t['id']} | **{'PASS' if t['passed'] else 'FAIL'}** | {t['detail']} |" for t in targets), ""]
    lines += ["## Method", "", *(f"- {m}" for m in manifest["method"]), "",
              "## RMSE vs exact (mean ± std over repeats; bold = best)", "",
              "| Circuit | 2q | " + " | ".join(LABEL[m] for m in METHODS) + " |",
              "|---|---|" + "---|" * len(METHODS)]
    for r in rows:
        lines.append(f"| {r['circuit']} | {r['two_qubit_gates']} | " + " | ".join(cell(r, m) for m in METHODS) + " |")
    lines += ["", "## Summary", "", "| Method | Best (circuits) | Median RMSE | Mean RMSE (deep) | Worst RMSE |",
              "|---|---|---|---|---|"]
    deep = [r for r in rows if r["deep"]]
    for m in METHODS:
        lines.append(f"| {LABEL[m]} | {sum(r['best'] == m for r in rows)} of {len(rows)} | "
                     f"{statistics.median(r[f'{m}_rmse_mean'] for r in rows):.4f} | "
                     f"{statistics.mean(r[f'{m}_rmse_mean'] for r in deep) if deep else float('nan'):.4f} | "
                     f"{max(r[f'{m}_rmse_mean'] for r in rows):.4f} |")
    lines += ["", "Branches used (per observable and repeat): " + "; ".join(
        f"{LABEL[m]}: " + ", ".join(f"{k} {v}" for k, v in c.most_common()) for m, c in branch_stats.items()) + ".",
              "", "## Observable estimates (mean ± std over repeats)", "",
              "| Circuit | Observable | Exact | " + " | ".join(LABEL[m] for m in METHODS) + " |",
              "|---|---|---|" + "---|" * len(METHODS), *("| " + " | ".join(d) + " |" for d in detail), ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--set", choices=("train", "test"), default="train")
    parser.add_argument("--backend", default="FakeKingston")
    parser.add_argument("--budget-qs", type=float, default=DEFAULT_BUDGET_QS)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--noise-scale", type=float, default=1.0)
    parser.add_argument("--only", default=None, help="comma-separated circuit names (quick checks only)")
    parser.add_argument("--analyze", type=Path)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    if args.set == "test" and not args.analyze and not recipe_v2.FROZEN:
        parser.error("the v2 held-out circuits are only run after recipe v2 is frozen (PREREGISTRATION.md Part F)")
    run_dir = args.analyze if args.analyze else simulate(args)
    analyze(run_dir, args.out)


if __name__ == "__main__":
    main()
