"""Hardware round for recipe v2 (PREREGISTRATION.md Part F): the 2 v2 held-out circuits, one round.

Methods and jobs (sent ONE AT A TIME, each finishes before the next is submitted):

  none        1 SamplerV2 job: the compiled circuits
  recipe_v1   2 SamplerV2 jobs: all-gate folding at 1/3/5; readout calibration          (recipe.py, frozen)
  recipe_v2   2 SamplerV2 jobs: TWIRLS twirled instances of two-qubit folding at 1/2/3; readout calibration
              (recipe_v2.py, frozen 25 Nov 2026)
  ibm_rl2     1 EstimatorV2 job, resilience_level=2
  v2_s15      SECONDARY, no target: 2 SamplerV2 jobs, recipe v2 at 1/1.5/2 (recipe_v2.SECONDARY_SCALES); last, so
              the --max-rus cap can only ever cut the secondary

v1_clip (secondary, no target) needs no job: recipe v1's counts with v2's rule.

Budget: none, recipe_v1, recipe_v2 and v2_s15 get equal ESTIMATED quantum seconds as a method total (budget x circuits),
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
from mitigation_v2 import SEC_KEYS, V1_KEYS, V1_SCALES, V2_KEYS, tasks
from twirl import fold_2q_series, twirl

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message="The extrapolation fit may be ill-conditioned")

BUDGET_QS = 6.0  # estimated quantum seconds per circuit per method (Part F)
METHODS = ("none", "recipe_v1", "recipe_v2", "ibm_rl2", "v2_s15")  # one or two jobs each, in this order
TARGET_METHODS = ("none", "recipe_v1", "recipe_v2", "ibm_rl2")  # G1-G3 need all four
REPORTED = ("none", "recipe_v1", "v1_clip", "recipe_v2", "v2_s15", "ibm_rl2")
SECONDARY = ("v1_clip", "v2_s15")  # Part F: reported, no target
TWIRLED = {"recipe_v2": ("v2", recipe_v2.SCALES, V2_KEYS, 0), "v2_s15": ("sec", recipe_v2.SECONDARY_SCALES, SEC_KEYS, 1)}
DEFAULT_ORDER = ",".join(METHODS)
TWIRL_SEED = 20261125
BOOTSTRAP = 500
RL2_SECONDS_PER_SHOT_PER_CIRCUIT = 83 / (8 * 10469)  # measured in rounds 1-2 (planning only)
SAMPLER_JOB_OVERHEAD_S = 2.5  # rounds 1-2: charged minus estimated, per Sampler job (27 vs 24, 29 vs 24 in 2 jobs)
RESERVE_RUS = 1.0  # Part F5: kept for resubmitting a failed job


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
        actual, twirled = {}, {}
        for g, scales, keys, offset in TWIRLED.values():
            rng = np.random.default_rng([TWIRL_SEED + offset, len(plan["tasks"])])
            series = fold_2q_series(base, scales)
            actual[g] = {k: a for k, (_, a) in zip(keys, series)}
            twirled[g] = {k: [twirl(c, rng) for _ in range(recipe_v2.TWIRLS)] for k, (c, _) in zip(keys, series)}
        dur = lambda c: c.estimate_duration(backend.target, unit="s")  # noqa: E731
        isa = compile_best_of_seeds(_strip(logical), backend, OPT_LEVEL, TRANSPILE_SEEDS)[0].circuit
        plan["tasks"][task.name] = {
            "task": task, "basis": basis, "seed": best.seed, "physical": physical, "two_qubit_gates":
                sum(1 for i in base.data if i.operation.num_qubits == 2 and i.operation.name != "barrier"),
            "none": base, "v1": v1, "cal": cal, "twirled": twirled, "actual_scales": actual,
            "durations": {"none": dur(base), **{k: dur(c) for k, c in v1.items()}, **{k: dur(c) for k, c in cal.items()},
                          **{f"{g}:{k}": statistics.mean(dur(c) for c in cs) for g in twirled
                             for k, cs in twirled[g].items()}},
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
    out = {"none": none, "v1_scales": n_s, "v1_cal": int(0.375 * n_s), "ibm": none}
    # twirled groups: m shots per twirled PUB (TWIRLS per scale), cal n_c = 0.375 x TWIRLS x m (20% on calibration)
    t = recipe_v2.TWIRLS
    for g, _, keys, _ in TWIRLED.values():
        per = sum(sum(t * (e["durations"][f"{g}:{k}"] + rep) for k in keys) for e in entries) + 0.375 * t * cal_time
        m = int(total / per)
        out[f"{g}_twirl"], out[f"{g}_cal"] = m, int(0.375 * t * m)
    return out


def estimated_seconds(plan: dict) -> dict[str, float]:
    rep, s = plan["rep_delay_s"], plan["shots"]
    est = dict.fromkeys(METHODS, 0.0)
    for e in plan["tasks"].values():
        d = e["durations"]
        est["none"] += s["none"] * (d["none"] + rep)
        est["recipe_v1"] += sum(s["v1_scales"] * (d[k] + rep) for k in V1_KEYS)
        est["recipe_v1"] += sum(s["v1_cal"] * (d[k] + rep) for k in ("cal0", "cal1"))
        for method, (g, _, keys, _) in TWIRLED.items():
            est[method] += sum(recipe_v2.TWIRLS * s[f"{g}_twirl"] * (d[f"{g}:{k}"] + rep) for k in keys)
            est[method] += sum(s[f"{g}_cal"] * (d[k] + rep) for k in ("cal0", "cal1"))
        est["ibm_rl2"] += s["ibm"] * RL2_SECONDS_PER_SHOT_PER_CIRCUIT
    return est


def run_jobs(plan: dict, mode, order: list[str], max_rus: float | None, save) -> dict:
    s = plan["shots"]
    items = {"none": [], "v1": [], "v1cal": [], "v2": [], "v2cal": [], "sec": [], "seccal": []}
    for name, e in plan["tasks"].items():
        b = e["basis"]
        items["none"].append((name, b, "s1", e["none"]))
        items["v1"] += [(name, b, k, e["v1"][k]) for k in V1_KEYS]
        items["v1cal"] += [(name, b, k, e["cal"][k]) for k in ("cal0", "cal1")]
        for g in e["twirled"]:
            items[g] += [(name, b, f"{k}#{i}", c) for k, cs in e["twirled"][g].items() for i, c in enumerate(cs)]
            items[f"{g}cal"] += [(name, b, k, e["cal"][k]) for k in ("cal0", "cal1")]
    results: dict = {}
    used_rus = 0.0

    def submit(label: str, fn, resubmitted: list):
        """Part F5: a job that fails (error, no data) is resubmitted once, unchanged; a second failure stops."""
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            print(f"{label} FAILED ({type(exc).__name__}: {exc}); resubmitting once, unchanged (Part F5)")
            resubmitted.append(f"{label}: {type(exc).__name__}: {exc}")
            return fn()

    for method in order:
        if max_rus is not None and used_rus >= max_rus:
            print(f"STOP: {used_rus:.3f} RU used reached the cap {max_rus}; not submitting {method} or later.")
            break
        resubmitted: list = []
        if method == "none":
            counts, info = submit("none", lambda: hardware._sampler_job(mode, items["none"], s["none"]), resubmitted)
            results[method] = {"jobs": [info], "counts": counts}
        elif method in ("recipe_v1", *TWIRLED):
            key = "v1" if method == "recipe_v1" else TWIRLED[method][0]
            shots = s["v1_scales" if key == "v1" else f"{key}_twirl"]
            counts, info1 = submit(f"{method} scales", lambda: hardware._sampler_job(mode, items[key], shots), resubmitted)
            cal, info2 = submit(f"{method} calibration",
                                lambda: hardware._sampler_job(mode, items[f"{key}cal"], s[f"{key}_cal"]), resubmitted)
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
                results[method] = submit("ibm_rl2", lambda: hardware._estimator_job(mode, plan, 2), resubmitted)
        else:
            raise ValueError(method)
        results[method]["resubmitted"] = resubmitted
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
    if method in ("recipe_v1", "v1_clip"):
        vals = [o.value(apply_readout_correction(to_probs(keys[k]), matrix, n)) for k in V1_KEYS]
        if method == "v1_clip":  # secondary (Part F): v1's data with v2's rule, no extra job
            return recipe_v2.estimate(o, list(V1_SCALES), vals)
        est = {f"readout_zne_{f}": extrapolate(f, vals, o)[0] for f in ("linear", "expg")}
        return recipe.estimate({}, o, est, vals)
    g, _, scale_keys, _ = TWIRLED[method]
    vals = []
    for k in scale_keys:
        pooled = Counter()
        for key, c in keys.items():
            if key.startswith(f"{k}#"):
                pooled.update(c)
        vals.append(o.value(apply_readout_correction(to_probs(dict(pooled)), matrix, n)))
    actual = [plan_entry["actual_scales"][g][k] for k in scale_keys]
    return recipe_v2.estimate(o, actual, vals)


def analyze(plan: dict, results: dict) -> list[dict]:
    rng = np.random.default_rng(7)
    rows = []
    for name, e in plan["tasks"].items():
        (o,) = e["task"].observables
        row = {"circuit": name, "two_qubit_gates": e["two_qubit_gates"], "exact": o.exact}
        for m in REPORTED:
            source = "recipe_v1" if m == "v1_clip" else m
            if source not in results or ("counts" not in results[source] and not results[source].get("values")):
                row[m] = row[f"{m}_std"] = row[f"{m}_value"] = float("nan")
                row[f"{m}_branch"] = "not run"
                continue
            if m == "ibm_rl2":
                v = results[m]["values"][name]
                value, std = v["evs"][0], v["stds"][0]
                row[m], row[f"{m}_value"], row[f"{m}_branch"] = abs(value - o.exact), value, "-"
                row[f"{m}_std"] = statistics.stdev(abs(rng.normal(value, std) - o.exact) for _ in range(BOOTSTRAP))
                continue
            counts = results[source]["counts"][name]
            value, branch = method_value(e, counts, m)
            row[m], row[f"{m}_value"], row[f"{m}_branch"] = abs(value - o.exact), value, branch
            boots = []
            for _ in range(BOOTSTRAP):
                fake = {b: {k: hardware.resample(c, rng) for k, c in keys.items()} for b, keys in counts.items()}
                boots.append(abs(method_value(e, fake, m)[0] - o.exact))
            row[f"{m}_std"] = statistics.stdev(boots)
        rows.append(row)
    return rows


def compare(r: dict, a: str, b: str) -> tuple[str, str]:
    """Three-way verdict for method a vs method b on one circuit (Part F6), and a detail string.

    Error = |estimate - exact|; sigma = bootstrap std; "clearly better" = gap > sqrt(sigma_a^2 + sigma_b^2)."""
    gap = r[b] - r[a]  # > 0: a has the smaller error
    sigma = math.hypot(r[f"{a}_std"], r[f"{b}_std"])
    verdict = "clearly better" if gap > sigma else ("clearly worse" if -gap > sigma else "no clear difference")
    return verdict, f"{r[a]:.4f} vs {r[b]:.4f} (gap {gap:+.4f}, combined spread {sigma:.4f})"


def evaluate(rows: list[dict], rus: dict[str, float]) -> list[dict]:
    """PREREGISTRATION.md Part F6: hardware targets, each circuit separately, plus the cost target."""
    targets = []
    for r in rows:
        c = r["circuit"]
        for tid, other, rule, ok in (
                ("G1", "recipe_v1", "v2 clearly better than recipe v1", ("clearly better",)),
                ("G2", "ibm_rl2", "v2 not clearly worse than IBM level 2", ("clearly better", "no clear difference")),
                ("G3", "none", "v2 clearly better than no mitigation", ("clearly better",))):
            verdict, detail = compare(r, "recipe_v2", other)
            targets.append({"id": f"{tid} {c}: {rule}", "passed": verdict in ok,
                            "detail": f"v2 {verdict}: {detail}"})
    targets.append({"id": "G2-cost: v2 RUs <= 0.5 x IBM level 2 RUs (round total)",
                    "passed": rus["recipe_v2"] <= 0.5 * rus["ibm_rl2"],
                    "detail": f"v2 {rus['recipe_v2']:.3f} RU vs 0.5 x L2 = {0.5 * rus['ibm_rl2']:.3f} RU"})
    for r in rows:  # secondary methods vs v2: reported, no target
        for m in SECONDARY:
            verdict, detail = compare(r, m, "recipe_v2")
            targets.append({"id": f"secondary {r['circuit']}: {m} vs recipe v2", "passed": None,
                            "detail": f"{m} {verdict}: {detail}"})
    return targets


def verdict_text(t: dict, dry_run: bool) -> str:
    if t["passed"] is None:
        return "reported (no target)"
    return "n/a (dry run)" if dry_run else ("**PASS**" if t["passed"] else "**FAIL**")


def write_report(path: Path, rows, targets, est, results, dry_run, backend_name, run_id) -> None:
    lines = [f"# Recipe v2 hardware round: {backend_name}{' (DRY RUN, local simulator)' if dry_run else ''}", "",
             f"Run `{run_id}`. Circuits: the v2 held-out set (Heisenberg-4, QPE-4). Methods: no mitigation, recipe "
             f"v1, recipe v2 ({recipe_v2.TWIRLS} twirls, scales {'/'.join(f'{s:g}' for s in recipe_v2.SCALES)}, clip), "
             "IBM resilience level 2; secondary (no target): v1 data + clip, and recipe v2 at "
             f"{'/'.join(f'{s:g}' for s in recipe_v2.SECONDARY_SCALES)}.", ""]
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
              "| Circuit | 2q | Exact | " + " | ".join(REPORTED) + " |", "|---|---|---|" + "---|" * len(REPORTED)]
    for r in rows:
        lines.append(f"| {r['circuit']} | {r['two_qubit_gates']} | {r['exact']:+.3f} | " + " | ".join(
            "not run" if math.isnan(r[m]) else f"{r[m]:.4f} ± {r[f'{m}_std']:.4f} ({r[f'{m}_value']:+.3f}, {r[f'{m}_branch']})"
            for m in REPORTED) + " |")
    lines += ["", "Secondary methods (Part F), no target uses them: `v1_clip` = recipe v1's data with v2's rule; "
              "`v2_s15` = recipe v2 at nominal scales 1/1.5/2 (own jobs, same budget, submitted last).",
              "", "## Pre-registered targets (PREREGISTRATION.md Part F)", "", "| Target | Result | Detail |", "|---|---|---|",
              *(f"| {t['id']} | {verdict_text(t, dry_run)} | {t['detail']} |" for t in targets), "",
              "Two circuits and one round can show a direction, not a proof (Part F6)."]
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
    sampler_jobs = {m: 0 if m == "ibm_rl2" else (1 if m == "none" else 2) for m in order}
    charged = {m: v + SAMPLER_JOB_OVERHEAD_S * sampler_jobs[m] for m, v in est.items()}
    print("Estimated quantum seconds: " + ", ".join(f"{m} {v:.1f}" for m, v in est.items()) + f"; total {total:.1f}")
    print("Expected charged (with per-job overhead): " + ", ".join(
        f"{m} {v:.1f} s = {v / 60:.2f} RU" for m, v in charged.items())
          + f"; total {sum(charged.values()):.1f} s = {sum(charged.values()) / 60:.2f} RU "
          f"(rule: remaining RUs >= 1.5 x total = {1.5 * sum(charged.values()) / 60:.2f}, and {RESERVE_RUS} RU kept)")
    if args.plan_only:
        for name, e in plan["tasks"].items():
            print(f"{name}: seed {e['seed']}, {e['two_qubit_gates']} CZ, physical {e['physical']}, actual scales "
                  + ", ".join(f"{g} {[round(a, 3) for a in sc.values()]}" for g, sc in e["actual_scales"].items())
                  + f", Estimator PUB on {e['estimator']['circuit'].num_qubits} qubits")
        pubs = {"none": len(plan["tasks"]), "recipe_v1 (scales + cal)": 5 * len(plan["tasks"]),
                "recipe_v2 / v2_s15 (twirled + cal), each": (3 * recipe_v2.TWIRLS + 2) * len(plan["tasks"])}
        print("PUBs:", pubs)
        return
    if args.submit and args.confirm_qpu_seconds < total:
        raise SystemExit(f"Refusing to submit: estimate {total:.1f} s > --confirm-qpu-seconds {args.confirm_qpu_seconds}")

    kind = "hardware-v2" if args.submit else "hardware-v2-dryrun"
    run_dir = runlog.new_run(kind, config={
        "backend": args.backend, "submit": args.submit, "order": order, "max_rus": args.max_rus,
        "budget_qs_per_circuit": args.budget_qs, "circuits": list(plan["tasks"]), "twirls": recipe_v2.TWIRLS,
        "twirl_seed": TWIRL_SEED, "recipe_v1": recipe.VERSION, "recipe_v2": recipe_v2.VERSION,
        "recipe_v2_frozen": recipe_v2.FROZEN, "v2_nominal_scales": recipe_v2.SCALES,
        "secondary_nominal_scales": recipe_v2.SECONDARY_SCALES, "shots_per_pub": plan["shots"],
        "estimated_quantum_seconds": est, "actual_scales": {n: e["actual_scales"] for n, e in plan["tasks"].items()},
        "bootstrap": BOOTSTRAP},
        method=[
            "Eight jobs, one at a time: none (1 Sampler), recipe v1 (Sampler: all-gate folding 1/3/5; Sampler: "
            "readout calibration), recipe v2 (Sampler: Pauli-twirled two-qubit folding at nominal 1/2/3, "
            f"{recipe_v2.TWIRLS} instances per scale; Sampler: readout calibration), IBM Estimator resilience_level 2, "
            "then the secondary v2 at 1/1.5/2 (same two Sampler jobs as recipe v2, own twirls).",
            "Compilation: level 2, best of 20 seeds (fewest 2q gates, then depth). Same compiled circuit for every method.",
            "none, recipe v1, recipe v2 and v2_s15 get equal estimated quantum seconds per method total; IBM level 2 uses "
            "precision 1/sqrt(shots of none).",
            "Error = |estimate - exact|; spread = bootstrap std (Sampler: multinomial resampling; Estimator: normal "
            "draws from the reported std).",
        ])
    results = run_jobs(plan, backend, order, args.max_rus, lambda res: runlog.write_json(run_dir / "results.json", res))
    runlog.write_json(run_dir / "results.json", results)
    rows = analyze(plan, results)
    rus = {m: results.get(m, {}).get("rus") for m in METHODS}
    complete = all(rus.get(m) is not None for m in TARGET_METHODS)
    if not args.submit:  # dry run: exercise the comparison code; IBM level 2 is not run, so its cells are nan
        rus = {m: (v if v is not None else float("nan")) for m, v in rus.items()}
    # incomplete hardware round: no target is evaluated (Part F5)
    targets = evaluate(rows, rus) if (complete or not args.submit) else []
    runlog.write_json(run_dir / "summary.json", {"rows": rows, "targets": targets, "estimated": est, "rus": rus})
    report = run_dir / "hardware_v2.md"
    write_report(report, rows, targets, est, results, not args.submit, args.backend, run_dir.name)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"{kind}_{args.backend}.md").write_text(report.read_text(encoding="utf-8"), encoding="utf-8")
    for r in rows:
        print(f"{r['circuit']:13} exact {r['exact']:+.3f}  " + "  ".join(
            f"{m}={r[m]:.4f}" for m in REPORTED))
    for t in targets:
        print(f"{t['id']}: {verdict_text(t, not args.submit).strip('*')}  {t['detail']}")
    print(f"\nReport: {report}")


if __name__ == "__main__":
    main()
