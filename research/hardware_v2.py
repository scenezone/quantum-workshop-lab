"""Hardware round for recipe v2 (PREREGISTRATION.md Part F): the 2 v2 held-out circuits, one round.

Methods and jobs (sent ONE AT A TIME, each finishes before the next is submitted):

  none        1 SamplerV2 job: the compiled circuits
  recipe_v1   2 SamplerV2 jobs: all-gate folding at 1/3/5; readout calibration          (recipe.py, frozen)
  recipe_v2   2 SamplerV2 jobs: TWIRLS twirled instances of two-qubit folding at 1/1.5/2; readout calibration
              (recipe_v2.py, frozen before this round)
  ibm_rl2     1 EstimatorV2 job, resilience_level=2

Budget: none, recipe_v1 and recipe_v2 get equal ESTIMATED quantum seconds as a method total (budget x circuits),
because SamplerV2 needs one shot count per job. IBM level 2 uses precision 1/sqrt(shots of none) and adds its own
overhead. Every job's charged seconds (metrics qpu_charge_time_seconds) and RUs are saved.

DEFAULT IS A DRY RUN on FakeKingston: Sampler jobs run locally one PUB at a time, the Estimator job is built and
checked but not run. Real hardware needs --submit, --confirm-qpu-seconds >= the estimate, and the device rule.

    .venv/Scripts/python hardware_v2.py                                   # dry run + estimate
    .venv/Scripts/python hardware_v2.py --submit --backend auto --confirm-qpu-seconds 150 --max-rus 3.0
"""

from __future__ import annotations

import argparse
import math
import statistics
import sys
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit_ibm_runtime import fake_provider

import hardware
import recipe
import recipe_v2
import runlog
from baseline import compile_best_of_seeds, measured_physical_qubits, to_probs
from folding import fold
from mitigation import (
    OPT_LEVEL,
    TRANSPILE_SEEDS,
    apply_readout_correction,
    calibration_circuits,
    confusion_matrix,
    extrapolate,
)
from mitigation_v2 import V1_KEYS, V1_SCALES, V2_KEYS, tasks
from twirl import fold_2q_series, twirl

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message="The extrapolation fit may be ill-conditioned")

BUDGET_QS = 6.0  # estimated quantum seconds per circuit per method (Part F)
METHODS = ("none", "recipe_v1", "recipe_v2", "ibm_rl2")
DEFAULT_ORDER = "none,recipe_v1,recipe_v2,ibm_rl2"
TWIRL_SEED = 20261125
BOOTSTRAP = 500
RL2_SECONDS_PER_SHOT_PER_CIRCUIT = 83 / (8 * 10469)  # measured in rounds 1-2 (planning only)


def estimator_observables() -> dict[str, SparsePauliOp]:
    h = SparsePauliOp.from_sparse_list([("Z", [j], (-1) ** j / 4) for j in range(4)], num_qubits=4).simplify()
    # P(1011) on counting qubits 0..3 of the 5-qubit QPE circuit (qubit 4 = eigenstate qubit, not measured)
    bits = "1011"
    signs = [1 if bits[::-1][i] == "0" else -1 for i in range(4)]
    terms = []
    for mask in range(16):
        subset = [i for i in range(4) if mask >> i & 1]
        terms.append(("Z" * len(subset), subset, math.prod(signs[i] for i in subset) / 16))
    q = SparsePauliOp.from_sparse_list(terms, num_qubits=5).simplify()
    return {"Heisenberg-4": h, "QPE-4": q}


def build_plan(backend, budget_qs: float) -> dict:
    rep = getattr(backend.configuration(), "default_rep_delay", 250e-6) or 250e-6
    rng = np.random.default_rng(TWIRL_SEED)
    observables = estimator_observables()
    plan = {"rep_delay_s": rep, "tasks": {}}
    for task in tasks("test"):
        (basis, logical), = task.circuits.items()
        (obs,) = task.observables
        op = observables[task.name]
        sv = Statevector(_strip(logical)).expectation_value(op).real
        assert abs(sv - obs.exact) < 1e-9, f"{task.name}: Pauli form {sv} != exact {obs.exact}"
        best = compile_best_of_seeds(logical, backend, OPT_LEVEL, TRANSPILE_SEEDS)[0]
        base = best.circuit
        physical = measured_physical_qubits(base)
        cal = calibration_circuits(backend.num_qubits, physical)
        v1 = {k: fold(base, s) for k, s in zip(V1_KEYS, V1_SCALES)}
        series = fold_2q_series(base, recipe_v2.SCALES)
        actual = {k: a for k, (_, a) in zip(V2_KEYS, series)}
        twirled = {k: [twirl(c, rng) for _ in range(recipe_v2.TWIRLS)] for k, (c, _) in zip(V2_KEYS, series)}
        dur = lambda c: c.estimate_duration(backend.target, unit="s")  # noqa: E731
        isa = compile_best_of_seeds(_strip(logical), backend, OPT_LEVEL, TRANSPILE_SEEDS)[0].circuit
        plan["tasks"][task.name] = {
            "task": task, "basis": basis, "seed": best.seed, "physical": physical, "two_qubit_gates":
                sum(1 for i in base.data if i.operation.num_qubits == 2 and i.operation.name != "barrier"),
            "none": base, "v1": v1, "cal": cal, "twirled": twirled, "actual_v2_scales": actual,
            "durations": {"none": dur(base), **{k: dur(c) for k, c in v1.items()}, **{k: dur(c) for k, c in cal.items()},
                          **{k: statistics.mean(dur(c) for c in twirled[k]) for k in V2_KEYS}},
            "estimator": {"circuit": isa, "observables": [op.apply_layout(isa.layout)], "duration": dur(isa)},
        }
    plan["shots"] = shots_for(plan, budget_qs)
    return plan


def _strip(circuit):
    """The circuit without final measurements and without classical registers (for Statevector / Estimator)."""
    out = circuit.remove_final_measurements(inplace=False)
    return out


def shots_for(plan: dict, budget_qs: float) -> dict[str, int]:
    """Shots per PUB per job, equal estimated quantum seconds per method total (budget x circuits)."""
    rep = plan["rep_delay_s"]
    total = budget_qs * len(plan["tasks"])
    entries = list(plan["tasks"].values())
    none = int(total / sum(e["durations"]["none"] + rep for e in entries))
    cal_time = sum(e["durations"]["cal0"] + e["durations"]["cal1"] + 2 * rep for e in entries)
    # v1: n_s per scale PUB, cal n_c = 0.375 n_s  (20% of shots on calibration, as in hardware.py)
    v1_per = sum(sum(e["durations"][k] + rep for k in V1_KEYS) for e in entries) + 0.375 * cal_time
    n_s = int(total / v1_per)
    # v2: m shots per twirled PUB (TWIRLS per scale), cal n_c = 0.375 x TWIRLS x m  (again 20% on calibration)
    t = recipe_v2.TWIRLS
    v2_per = sum(sum(t * (e["durations"][k] + rep) for k in V2_KEYS) for e in entries) + 0.375 * t * cal_time
    m = int(total / v2_per)
    return {"none": none, "v1_scales": n_s, "v1_cal": int(0.375 * n_s), "v2_twirl": m,
            "v2_cal": int(0.375 * t * m), "ibm": none}


def estimated_seconds(plan: dict) -> dict[str, float]:
    rep, s = plan["rep_delay_s"], plan["shots"]
    est = dict.fromkeys(METHODS, 0.0)
    for e in plan["tasks"].values():
        d = e["durations"]
        est["none"] += s["none"] * (d["none"] + rep)
        est["recipe_v1"] += sum(s["v1_scales"] * (d[k] + rep) for k in V1_KEYS)
        est["recipe_v1"] += sum(s["v1_cal"] * (d[k] + rep) for k in ("cal0", "cal1"))
        est["recipe_v2"] += sum(recipe_v2.TWIRLS * s["v2_twirl"] * (d[k] + rep) for k in V2_KEYS)
        est["recipe_v2"] += sum(s["v2_cal"] * (d[k] + rep) for k in ("cal0", "cal1"))
        est["ibm_rl2"] += s["ibm"] * RL2_SECONDS_PER_SHOT_PER_CIRCUIT
    return est


def run_jobs(plan: dict, mode, order: list[str], max_rus: float | None, save) -> dict:
    s = plan["shots"]
    items = {"none": [], "v1": [], "v1cal": [], "v2": [], "v2cal": []}
    for name, e in plan["tasks"].items():
        b = e["basis"]
        items["none"].append((name, b, "s1", e["none"]))
        items["v1"] += [(name, b, k, e["v1"][k]) for k in V1_KEYS]
        items["v1cal"] += [(name, b, k, e["cal"][k]) for k in ("cal0", "cal1")]
        items["v2"] += [(name, b, f"{k}#{i}", c) for k in V2_KEYS for i, c in enumerate(e["twirled"][k])]
        items["v2cal"] += [(name, b, k, e["cal"][k]) for k in ("cal0", "cal1")]
    results: dict = {}
    used_rus = 0.0
    for method in order:
        if max_rus is not None and used_rus >= max_rus:
            print(f"STOP: {used_rus:.3f} RU used reached the cap {max_rus}; not submitting {method} or later.")
            break
        if method == "none":
            counts, info = hardware._sampler_job(mode, items["none"], s["none"])
            results[method] = {"jobs": [info], "counts": counts}
        elif method in ("recipe_v1", "recipe_v2"):
            key = "v1" if method == "recipe_v1" else "v2"
            counts, info1 = hardware._sampler_job(mode, items[key], s[f"{key}_scales" if key == "v1" else "v2_twirl"])
            cal, info2 = hardware._sampler_job(mode, items[f"{key}cal"], s[f"{key}_cal"])
            for name, bases in cal.items():
                for b, keys in bases.items():
                    counts[name][b].update(keys)
            results[method] = {"jobs": [info1, info2], "counts": counts}
        elif method == "ibm_rl2":
            if hardware.LOCAL_ONE_PUB_PER_JOB:
                for e in plan["tasks"].values():
                    est = e["estimator"]
                    assert all(op.num_qubits == est["circuit"].num_qubits for op in est["observables"])
                results[method] = {"jobs": [], "values": None, "note": "not executed in dry run; PUBs built and checked"}
            else:
                results[method] = hardware._estimator_job(mode, plan, 2)
        else:
            raise ValueError(method)
        jobs = results[method]["jobs"]
        results[method]["quantum_seconds"] = sum(j["quantum_seconds"] or 0 for j in jobs) if jobs else None
        results[method]["rus"] = sum(j["rus"] or 0 for j in jobs) if jobs else None
        used_rus += results[method]["rus"] or 0.0
        save(results)
    return results


# ----------------------------------------------------------------- analyze


def method_value(plan_entry: dict, counts: dict, method: str) -> tuple[float, str]:
    task = plan_entry["task"]
    (o,) = task.observables
    keys = counts[plan_entry["basis"]]
    if method == "none":
        return o.value(to_probs(keys["s1"])), "-"
    zero, one = to_probs(keys["cal0"]), to_probs(keys["cal1"])
    n = len(next(iter(zero)))
    matrix = confusion_matrix(zero, one, n)
    if method == "recipe_v1":
        vals = [o.value(apply_readout_correction(to_probs(keys[k]), matrix, n)) for k in V1_KEYS]
        est = {f"readout_zne_{f}": extrapolate(f, vals, o)[0] for f in ("linear", "expg")}
        return recipe.estimate({}, o, est, vals)
    vals = []
    for k in V2_KEYS:
        pooled = Counter()
        for key, c in keys.items():
            if key.startswith(f"{k}#"):
                pooled.update(c)
        vals.append(o.value(apply_readout_correction(to_probs(dict(pooled)), matrix, n)))
    actual = [plan_entry["actual_v2_scales"][k] for k in V2_KEYS]
    return recipe_v2.estimate(o, actual, vals)


def analyze(plan: dict, results: dict) -> list[dict]:
    rng = np.random.default_rng(7)
    rows = []
    for name, e in plan["tasks"].items():
        (o,) = e["task"].observables
        row = {"circuit": name, "two_qubit_gates": e["two_qubit_gates"], "exact": o.exact}
        for m in METHODS:
            if m not in results or ("counts" not in results[m] and not results[m].get("values")):
                row[m] = row[f"{m}_std"] = row[f"{m}_value"] = float("nan")
                row[f"{m}_branch"] = "not run"
                continue
            if m == "ibm_rl2":
                v = results[m]["values"][name]
                value, std = v["evs"][0], v["stds"][0]
                row[m], row[f"{m}_value"], row[f"{m}_branch"] = abs(value - o.exact), value, "-"
                row[f"{m}_std"] = statistics.stdev(abs(rng.normal(value, std) - o.exact) for _ in range(BOOTSTRAP))
                continue
            counts = results[m]["counts"][name]
            value, branch = method_value(e, counts, m)
            row[m], row[f"{m}_value"], row[f"{m}_branch"] = abs(value - o.exact), value, branch
            boots = []
            for _ in range(BOOTSTRAP):
                fake = {b: {k: hardware.resample(c, rng) for k, c in keys.items()} for b, keys in counts.items()}
                boots.append(abs(method_value(e, fake, m)[0] - o.exact))
            row[f"{m}_std"] = statistics.stdev(boots)
        rows.append(row)
    return rows


def evaluate(rows: list[dict], rus: dict[str, float]) -> list[dict]:
    """PREREGISTRATION.md Part F, hardware targets G1-G3 (one round, both v2 held-out circuits)."""
    def clearly(r, better, worse):
        return r[worse] - r[better] > math.hypot(r[f"{better}_std"], r[f"{worse}_std"])

    g1 = all(r["recipe_v2"] < r["recipe_v1"] for r in rows)
    g2_acc = all(r["recipe_v2"] <= r["ibm_rl2"] + 0.05 for r in rows)
    g2_cost = rus["recipe_v2"] <= 0.5 * rus["ibm_rl2"]
    g3 = all(clearly(r, "recipe_v2", "none") for r in rows)
    return [
        {"id": "G1 v2 beats v1", "passed": g1,
         "detail": "; ".join(f"{r['circuit']}: v2 {r['recipe_v2']:.4f} vs v1 {r['recipe_v1']:.4f}" for r in rows)},
        {"id": "G2 close to IBM level 2 at half the cost", "passed": g2_acc and g2_cost,
         "detail": "; ".join(f"{r['circuit']}: v2 {r['recipe_v2']:.4f} vs L2 + 0.05 = {r['ibm_rl2'] + 0.05:.4f}"
                             for r in rows) + f"; RUs v2 {rus['recipe_v2']:.3f} vs 0.5 x L2 {0.5 * rus['ibm_rl2']:.3f}"},
        {"id": "G3 v2 clearly beats no mitigation", "passed": g3,
         "detail": "; ".join(f"{r['circuit']}: v2 {r['recipe_v2']:.4f} ± {r['recipe_v2_std']:.4f} vs none "
                             f"{r['none']:.4f} ± {r['none_std']:.4f}" for r in rows)},
    ]


def write_report(path: Path, rows, targets, est, results, dry_run, backend_name, run_id) -> None:
    lines = [f"# Recipe v2 hardware round: {backend_name}{' (DRY RUN, local simulator)' if dry_run else ''}", "",
             f"Run `{run_id}`. Circuits: the v2 held-out set (Heisenberg-4, QPE-4). Methods: no mitigation, recipe "
             f"v1, recipe v2 ({recipe_v2.TWIRLS} twirls, scales 1/1.5/2, clip), IBM resilience level 2.", ""]
    if dry_run:
        lines += ["> **DRY RUN, not evidence.** Sampler jobs ran locally on a fake backend; the IBM Estimator job was "
                  "built and checked but not executed. Usage is an estimate.", ""]
    lines += ["## Jobs, in submission order", "", "| Method | Job ID | Shots per PUB | Charged s | RUs |", "|---|---|---|---|---|"]
    for m, res in results.items():
        for j in res.get("jobs", []):
            lines.append(f"| {m} | `{j['job_id']}` | {j.get('shots', 'n/a')} | {j.get('quantum_seconds')} | {j.get('rus')} |")
    lines += ["", "| Method | Estimated s | Charged s | RUs |", "|---|---|---|---|",
              *(f"| {m} | {est.get(m, float('nan')):.1f} | {results.get(m, {}).get('quantum_seconds')} | "
                f"{results.get(m, {}).get('rus')} |" for m in METHODS),
              "", "## Error vs exact (± bootstrap std)", "",
              "| Circuit | 2q | Exact | " + " | ".join(METHODS) + " |", "|---|---|---|" + "---|" * len(METHODS)]
    for r in rows:
        lines.append(f"| {r['circuit']} | {r['two_qubit_gates']} | {r['exact']:+.3f} | " + " | ".join(
            "not run" if math.isnan(r[m]) else f"{r[m]:.4f} ± {r[f'{m}_std']:.4f} ({r[f'{m}_value']:+.3f}, {r[f'{m}_branch']})"
            for m in METHODS) + " |")
    lines += ["", "## Pre-registered targets (PREREGISTRATION.md Part F)", "", "| Target | Result | Detail |", "|---|---|---|",
              *(f"| {t['id']} | {'n/a (dry run)' if dry_run else ('**PASS**' if t['passed'] else '**FAIL**')} | {t['detail']} |"
                for t in targets), ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--backend", default="FakeKingston", help="fake backend (dry run), device name, or 'auto'")
    parser.add_argument("--instance", default=None)
    parser.add_argument("--confirm-qpu-seconds", type=float, default=0.0)
    parser.add_argument("--max-rus", type=float, default=None, help="stop before the next job once RUs used reach this")
    parser.add_argument("--order", default=DEFAULT_ORDER)
    parser.add_argument("--budget-qs", type=float, default=BUDGET_QS)
    parser.add_argument("--plan-only", action="store_true",
                        help="build and check every PUB and print the shot/usage plan; execute nothing")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    order = args.order.split(",")
    assert set(order) <= set(METHODS), order
    if not args.plan_only and not recipe_v2.FROZEN:
        # A dry run simulates the held-out circuits with noise, so it too must wait for the freeze.
        raise SystemExit("Refusing to run: recipe v2 is not frozen (PREREGISTRATION.md Part F). Use --plan-only.")

    if args.submit:
        from qiskit_ibm_runtime import QiskitRuntimeService
        service = QiskitRuntimeService(instance=args.instance) if args.instance else QiskitRuntimeService()
        backend = hardware.pick_device(service) if args.backend == "auto" else service.backend(args.backend)
        args.backend = backend.name
        print(f"Device: {backend.name}")
    else:
        backend = getattr(fake_provider, args.backend)()
        hardware.LOCAL_ONE_PUB_PER_JOB = True

    plan = build_plan(backend, args.budget_qs)
    est = {m: v for m, v in estimated_seconds(plan).items() if m in order}
    total = sum(est.values())
    print("Shots per PUB:", plan["shots"])
    print("Estimated quantum seconds: " + ", ".join(f"{m} {v:.1f}" for m, v in est.items()) + f"; total {total:.1f} "
          f"(+ about 2 s fixed overhead per job, 6 jobs)")
    if args.plan_only:
        for name, e in plan["tasks"].items():
            print(f"{name}: seed {e['seed']}, {e['two_qubit_gates']} CZ, physical {e['physical']}, actual v2 scales "
                  f"{[round(a, 3) for a in e['actual_v2_scales'].values()]}, Estimator PUB on "
                  f"{e['estimator']['circuit'].num_qubits} qubits")
        pubs = {"none": len(plan["tasks"]), "recipe_v1 (scales + cal)": 5 * len(plan["tasks"]),
                "recipe_v2 (twirled + cal)": (3 * recipe_v2.TWIRLS + 2) * len(plan["tasks"])}
        print("PUBs:", pubs)
        return
    if args.submit and args.confirm_qpu_seconds < total:
        raise SystemExit(f"Refusing to submit: estimate {total:.1f} s > --confirm-qpu-seconds {args.confirm_qpu_seconds}")

    kind = "hardware-v2" if args.submit else "hardware-v2-dryrun"
    run_dir = runlog.new_run(kind, config={
        "backend": args.backend, "submit": args.submit, "order": order, "max_rus": args.max_rus,
        "budget_qs_per_circuit": args.budget_qs, "circuits": list(plan["tasks"]), "twirls": recipe_v2.TWIRLS,
        "twirl_seed": TWIRL_SEED, "recipe_v1": recipe.VERSION, "recipe_v2": recipe_v2.VERSION,
        "recipe_v2_frozen": recipe_v2.FROZEN, "shots_per_pub": plan["shots"], "estimated_quantum_seconds": est,
        "actual_v2_scales": {n: e["actual_v2_scales"] for n, e in plan["tasks"].items()}, "bootstrap": BOOTSTRAP},
        method=[
            "Six jobs, one at a time: none (1 Sampler), recipe v1 (Sampler: all-gate folding 1/3/5; Sampler: "
            "readout calibration), recipe v2 (Sampler: Pauli-twirled two-qubit folding at nominal 1/1.5/2, "
            f"{recipe_v2.TWIRLS} instances per scale; Sampler: readout calibration), IBM Estimator resilience_level 2.",
            "Compilation: level 2, best of 20 seeds (fewest 2q gates, then depth). Same compiled circuit for every method.",
            "none, recipe v1 and recipe v2 get equal estimated quantum seconds per method total; IBM level 2 uses "
            "precision 1/sqrt(shots of none).",
            "Error = |estimate - exact|; spread = bootstrap std (Sampler: multinomial resampling; Estimator: normal "
            "draws from the reported std).",
        ])
    results = run_jobs(plan, backend, order, args.max_rus, lambda res: runlog.write_json(run_dir / "results.json", res))
    runlog.write_json(run_dir / "results.json", results)
    rows = analyze(plan, results)
    rus = {m: results.get(m, {}).get("rus") for m in METHODS}
    complete = args.submit and all(rus.get(m) is not None for m in METHODS)
    targets = evaluate(rows, rus) if complete else []
    runlog.write_json(run_dir / "summary.json", {"rows": rows, "targets": targets, "estimated": est, "rus": rus})
    report = run_dir / "hardware_v2.md"
    write_report(report, rows, targets, est, results, not args.submit, args.backend, run_dir.name)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"{kind}_{args.backend}.md").write_text(report.read_text(encoding="utf-8"), encoding="utf-8")
    for r in rows:
        print(f"{r['circuit']:13} exact {r['exact']:+.3f}  " + "  ".join(
            f"{m}={r[m]:.4f}" for m in METHODS))
    for t in targets:
        print(f"{t['id']}: {'PASS' if t['passed'] else 'FAIL'}  {t['detail']}")
    print(f"\nReport: {report}")


if __name__ == "__main__":
    main()
