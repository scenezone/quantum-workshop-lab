"""Recipe v1.2 hardware round on four NEW circuits (PREREGISTRATION.md Part H). No IBM resilience levels.

  none        1 SamplerV2 job
  recipe_v1   2 SamplerV2 jobs: all-gate folding at 1/3/5; readout calibration (recipe.py, frozen 23 Nov)

Recipe v1.2 (recipe_v1_2.py) is computed from recipe_v1's counts: v1 plus the "decay" and "alive" flag rules;
when flagged it reports the scale-1 readout-corrected value. No extra job.

Reused unchanged: compilation (level 2, best of 20 seeds), folding, calibration circuits, the job submission with
one resubmission of a failed job (hardware_v2.run_jobs), 500 bootstrap replicas (seed 7), and the verdict
"clearly better" = error gap > sqrt(sigma_a^2 + sigma_b^2).

    .venv/Scripts/python hardware_v1_2.py --plan-only
    .venv/Scripts/python hardware_v1_2.py                                    # local dry run on FakeMarrakesh
    .venv/Scripts/python hardware_v1_2.py --submit --confirm-qpu-seconds 30 --max-rus 0.65
"""
from __future__ import annotations

import argparse
import math
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from qiskit_ibm_runtime import fake_provider

import hardware
import hardware_v2 as hv2
import recipe
import recipe_v1_1
import recipe_v1_2
import runlog
from baseline import compile_best_of_seeds, measured_physical_qubits, to_probs
from folding import fold
from heldout_v12 import DEEP, tasks
from mitigation import OPT_LEVEL, TRANSPILE_SEEDS, apply_readout_correction, calibration_circuits, confusion_matrix
from mitigation import extrapolate
from mitigation_v2 import V1_KEYS, V1_SCALES

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message="The extrapolation fit may be ill-conditioned")

DEVICE = "ibm_marrakesh"
ORDER = ("none", "recipe_v1")
JOBS = {"none": 1, "recipe_v1": 2}
BUDGET_QS = 3.0  # estimated quantum seconds per circuit per method
RESERVE_RUS = 0.5  # Part H: at least this must remain after the round
BOOTSTRAP = 500
SEED = 7
FAIL_E, GOOD_E = 0.10, 0.04  # classes of v1's result, as in the v1.1 design replay (reported, no target)
HERE = Path(__file__).parent


# ----------------------------------------------------------------- plan


def build_plan(backend) -> dict:
    rep = getattr(backend.configuration(), "default_rep_delay", 250e-6) or 250e-6
    plan = {"rep_delay_s": rep, "tasks": {}}
    for task in tasks():
        (basis, logical), = task.circuits.items()
        best = compile_best_of_seeds(logical, backend, OPT_LEVEL, TRANSPILE_SEEDS)[0]
        base = best.circuit
        physical = measured_physical_qubits(base)
        cal = calibration_circuits(backend.num_qubits, physical)
        v1 = {k: fold(base, s) for k, s in zip(V1_KEYS, V1_SCALES)}
        dur = lambda c: c.estimate_duration(backend.target, unit="s")  # noqa: E731
        plan["tasks"][task.name] = {
            "task": task, "basis": basis, "seed": best.seed, "physical": physical,
            "two_qubit_gates": sum(1 for i in base.data if i.operation.num_qubits == 2 and i.operation.name != "barrier"),
            "none": base, "v1": v1, "cal": cal, "twirled": {},
            "durations": {"none": dur(base), **{k: dur(c) for k, c in v1.items()}, **{k: dur(c) for k, c in cal.items()}},
        }
    rep, entries = plan["rep_delay_s"], list(plan["tasks"].values())
    total = BUDGET_QS * len(entries)
    cal_time = sum(e["durations"]["cal0"] + e["durations"]["cal1"] + 2 * rep for e in entries)
    n_s = int(total / (sum(sum(e["durations"][k] + rep for k in V1_KEYS) for e in entries) + 0.375 * cal_time))
    plan["shots"] = {"none": int(total / sum(e["durations"]["none"] + rep for e in entries)),
                     "v1_scales": n_s, "v1_cal": int(0.375 * n_s)}  # 20% of v1's shots on calibration
    return plan


def estimated_seconds(plan: dict) -> dict[str, float]:
    rep, s = plan["rep_delay_s"], plan["shots"]
    est = dict.fromkeys(ORDER, 0.0)
    for e in plan["tasks"].values():
        d = e["durations"]
        est["none"] += s["none"] * (d["none"] + rep)
        est["recipe_v1"] += sum(s["v1_scales"] * (d[k] + rep) for k in V1_KEYS)
        est["recipe_v1"] += sum(s["v1_cal"] * (d[k] + rep) for k in ("cal0", "cal1"))
    return est


# ----------------------------------------------------------------- analyze


def corrected(o, keys: dict) -> list[float]:
    zero, one = to_probs(keys["cal0"]), to_probs(keys["cal1"])
    n = len(next(iter(zero)))
    m = confusion_matrix(zero, one, n)
    return [o.value(apply_readout_correction(to_probs(keys[k]), m, n)) for k in V1_KEYS]


def v1_value(o, vals: list[float]) -> tuple[float, str]:
    est = {f"readout_zne_{f}": extrapolate(f, vals, o)[0] for f in ("linear", "expg")}
    return recipe.estimate({}, o, est, vals)


def verdict(a: str, b: str, r: dict) -> tuple[str, str]:
    gap, sigma = r[b] - r[a], math.hypot(r[f"{a}_std"], r[f"{b}_std"])
    v = "clearly better" if gap > sigma else ("clearly worse" if -gap > sigma else "no clear difference")
    return v, f"{r[a]:.4f} vs {r[b]:.4f} (gap {gap:+.4f}, combined spread {sigma:.4f})"


def analyze(plan: dict, results: dict) -> list[dict]:
    rng = np.random.default_rng(SEED)
    rows = []
    for name, e in plan["tasks"].items():
        (o,) = e["task"].observables
        row = {"circuit": name, "depth_class": "deep" if name in DEEP else "shallow",
               "two_qubit_gates": e["two_qubit_gates"], "exact": o.exact, "asymptote": o.asymptote}
        if any("counts" not in results.get(m, {}) for m in ORDER):
            rows.append(row)
            continue
        keys = results["recipe_v1"]["counts"][name][e["basis"]]
        s1 = results["none"]["counts"][name][e["basis"]]["s1"]
        vals = corrected(o, keys)
        boot_vals, boot_none = [], []
        for _ in range(BOOTSTRAP):
            boot_vals.append(corrected(o, {k: hardware.resample(c, rng) for k, c in keys.items()}))
            boot_none.append(o.value(to_probs(hardware.resample(s1, rng))))
        bv = np.array(boot_vals)
        v1, branch1 = v1_value(o, vals)
        v12, branch12, failed = recipe_v1_2.estimate(o, vals, bv)
        none = o.value(to_probs(s1))
        boot_v1 = [abs(v1_value(o, list(x))[0] - o.exact) for x in bv]
        boot_v12 = [abs(x[0] - o.exact) for x in bv] if failed else boot_v1
        d = [v - o.asymptote for v in vals]
        row.update({
            "scaled": vals, "d": d, "se_d": [float(np.std(bv[:, i] - o.asymptote, ddof=1)) for i in range(3)],
            "checks": recipe_v1_1.checks(d, bv - o.asymptote), "failed_rules": failed, "flagged": bool(failed),
            "none_value": none, "recipe_v1_value": v1, "recipe_v1_branch": branch1,
            "recipe_v1_2_value": v12, "recipe_v1_2_branch": branch12,
            "none": abs(none - o.exact), "recipe_v1": abs(v1 - o.exact), "recipe_v1_2": abs(v12 - o.exact),
            "none_std": float(np.std([abs(x - o.exact) for x in boot_none], ddof=1)),
            "recipe_v1_std": float(np.std(boot_v1, ddof=1)), "recipe_v1_2_std": float(np.std(boot_v12, ddof=1)),
        })
        v1_vs_none = verdict("recipe_v1", "none", row)[0]
        e_rel = row["recipe_v1"] / (o.high - o.low)
        row["v1_class"] = ("failure" if v1_vs_none == "clearly worse" or e_rel > FAIL_E else
                           "good" if v1_vs_none == "clearly better" and e_rel < GOOD_E else "ambiguous")
        rows.append(row)
    return rows


def evaluate(rows: list[dict]) -> list[dict]:
    """Part H targets and reported comparisons, each circuit separately."""
    out = []
    for r in rows:
        if "none_std" not in r:
            continue
        v, detail = verdict("recipe_v1_2", "none", r)
        out.append({"id": f"T1 {r['circuit']}: v1.2 not clearly worse than no mitigation",
                    "passed": v in ("clearly better", "no clear difference"), "detail": f"v1.2 {v}: {detail}"})
    for r in rows:
        if "none_std" not in r:
            continue
        for a, b in (("recipe_v1", "none"), ("recipe_v1_2", "recipe_v1"), ("recipe_v1_2", "none")):
            v, detail = verdict(a, b, r)
            out.append({"id": f"reported {r['circuit']}: {a} vs {b}", "passed": None, "detail": f"{a} {v}: {detail}"})
    return out


def write_report(path: Path, rows, targets, results, est, dry_run, backend_name, run_id) -> None:
    L = [f"# Recipe v1.2 round on new circuits (Part H): {backend_name}{' (DRY RUN, local simulator)' if dry_run else ''}",
         "", f"Run `{run_id}`. Methods: none, recipe v1; v1.2 computed from v1's counts. No IBM resilience levels and "
         "no comparison with them.", ""]
    if dry_run:
        L += ["> **DRY RUN, not evidence.** Sampler jobs ran locally on a fake backend; seconds are estimates.", ""]
    L += ["## Jobs", "", "| Method | Job ID | Charged s | RUs | Resubmitted |", "|---|---|---|---|---|"]
    for m in ORDER:
        res = results.get(m, {})
        for j in res.get("jobs", []):
            L.append(f"| {m} | `{j['job_id']}` | {j.get('quantum_seconds')} | {j.get('rus')} | "
                     f"{'; '.join(res.get('resubmitted', [])) or '-'} |")
    L += ["", "| Method | Estimated s | Charged s | RUs |", "|---|---|---|---|",
          *(f"| {m} | {est[m]:.1f} | {results.get(m, {}).get('quantum_seconds')} | {results.get(m, {}).get('rus')} |"
            for m in ORDER),
          "", "## Error vs exact (± bootstrap std)", "",
          "| Circuit | Type | 2q | Exact | none | v1 (branch) | v1.2 (branch) | v1 class |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if "none_std" not in r:
            L.append(f"| {r['circuit']} | {r['depth_class']} | {r['two_qubit_gates']} | {r['exact']:+.3f} | not run |||")
            continue
        L.append(f"| {r['circuit']} | {r['depth_class']} | {r['two_qubit_gates']} | {r['exact']:+.3f} | "
                 f"{r['none']:.4f} ± {r['none_std']:.4f} ({r['none_value']:+.3f}) | "
                 f"{r['recipe_v1']:.4f} ± {r['recipe_v1_std']:.4f} ({r['recipe_v1_value']:+.3f}, {r['recipe_v1_branch']}) | "
                 f"{r['recipe_v1_2']:.4f} ± {r['recipe_v1_2_std']:.4f} ({r['recipe_v1_2_value']:+.3f}, "
                 f"{r['recipe_v1_2_branch']}) | {r['v1_class']} |")
    L += ["", "## Flag rules", "",
          "d(s) = readout-corrected value at scale s minus the fully mixed value. v1.2 uses decay and alive; one_exp "
          "(v1.1 only) is shown for information.", "",
          "| Circuit | d(1) / d(3) / d(5) | SE(d5) | decay | alive | one_exp (not used) | v1.2 flagged |",
          "|---|---|---|---|---|---|---|"]
    for r in rows:
        if "checks" in r:
            c = r["checks"]
            L.append(f"| {r['circuit']} | {' / '.join(f'{x:+.3f}' for x in r['d'])} | {r['se_d'][2]:.3f} | "
                     f"{'pass' if c['decay'] else 'FAIL'} | {'pass' if c['alive'] else 'FAIL'} | "
                     f"{'pass' if c['one_exp'] else 'fail'} | {'yes' if r['flagged'] else 'no'} |")
    L += ["", "## Pre-registered target and reported comparisons (PREREGISTRATION.md Part H)", "",
          "| Item | Result | Detail |", "|---|---|---|",
          *(f"| {t['id']} | {hv2.verdict_text(t, dry_run)} | {t['detail']} |" for t in targets),
          "", "Four circuits on one device and one day show a direction, not a proof.", ""]
    path.write_text("\n".join(L), encoding="utf-8")


# ----------------------------------------------------------------- main


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--confirm-qpu-seconds", type=float, default=0.0)
    parser.add_argument("--max-rus", type=float, default=None)
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--out", type=Path, default=HERE / "results")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    reads: list[dict] = []
    service = None
    if args.submit:
        from qiskit_ibm_runtime import QiskitRuntimeService
        service = QiskitRuntimeService()
        backend = service.backend(DEVICE)
        status = backend.status()
        if not status.operational:
            raise SystemExit(f"{DEVICE} is not operational now; Part H says wait, do not switch device.")
        print(f"Device: {DEVICE} ({status.pending_jobs} pending jobs)")
    else:
        backend = fake_provider.FakeMarrakesh()
        hardware.LOCAL_ONE_PUB_PER_JOB = True

    def account_remaining():
        if service is None:
            return None
        try:
            u = service.usage()
            reads.append({"read_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                          **{k: u.get(k) for k in ("usage_remaining_ru", "usage_consumed_ru", "usage_limit_ru",
                                                   "usage_remaining_seconds", "usage_consumed_seconds",
                                                   "usage_period")}})
            print(f"Account read {reads[-1]['read_at_utc']}: {u.get('usage_remaining_ru')} RU remaining")
            return float(u["usage_remaining_ru"])
        except Exception as exc:  # noqa: BLE001
            reads.append({"read_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                          "error": type(exc).__name__})
            return None

    plan = build_plan(backend)
    est = estimated_seconds(plan)
    charged = {m: est[m] + hv2.SAMPLER_JOB_OVERHEAD_S * JOBS[m] for m in ORDER}
    expected = sum(charged.values()) / 60
    print("Circuits:", {n: e["two_qubit_gates"] for n, e in plan["tasks"].items()}, "(2q gates)")
    print("Shots per PUB:", plan["shots"])
    print("Expected charged: " + ", ".join(f"{m} {v:.1f} s = {v / 60:.2f} RU" for m, v in charged.items())
          + f"; total {expected:.3f} RU; Part H needs >= {1.5 * expected:.2f} RU and >= {expected + RESERVE_RUS:.2f} RU")
    if args.plan_only:
        return
    if args.submit:
        if args.confirm_qpu_seconds < sum(est.values()):
            raise SystemExit(f"Refusing: estimate {sum(est.values()):.1f} s > --confirm-qpu-seconds {args.confirm_qpu_seconds}")
        remaining = account_remaining()
        if remaining is None or remaining < max(1.5 * expected, expected + RESERVE_RUS):
            raise SystemExit(f"Refusing: remaining RUs {remaining} < max(1.5 x {expected:.3f}, {expected:.3f} + "
                             f"{RESERVE_RUS}) (Part H)")

    kind = "hardware-v1-2" if args.submit else "hardware-v1-2-dryrun"
    run_dir = runlog.new_run(kind, config={
        "backend": backend.name, "submit": args.submit, "order": list(ORDER), "max_rus": args.max_rus,
        "budget_qs_per_circuit": BUDGET_QS, "circuits": {n: e["two_qubit_gates"] for n, e in plan["tasks"].items()},
        "recipe_v1": recipe.VERSION, "recipe_v1_2": recipe_v1_2.VERSION, "k": recipe_v1_2.K,
        "rules": list(recipe_v1_2.RULES), "shots_per_pub": plan["shots"], "estimated_quantum_seconds": est,
        "bootstrap": BOOTSTRAP, "seed": SEED, "reserve_rus": RESERVE_RUS},
        method=[
            "Three jobs, one at a time: none (1 Sampler); recipe v1 (Sampler: all-gate folding 1/3/5; Sampler: "
            "readout calibration). Recipe v1.2 = v1 + decay/alive flags, from v1's counts.",
            "Compilation level 2, best of 20 seeds; 3.0 estimated quantum s per circuit per method.",
            "Error = |estimate - exact|; spread = bootstrap std; clearly better = gap > combined spread.",
        ])
    results = hv2.run_jobs(plan, backend, list(ORDER), args.max_rus,
                           lambda res: runlog.write_json(run_dir / "results.json", res),
                           account_remaining if args.submit else None, 0.0)
    runlog.write_json(run_dir / "results.json", results)
    if args.submit:
        account_remaining()  # one read after the round
        runlog.write_json(run_dir / "account_reads.json", reads)
    rows = analyze(plan, results)
    targets = evaluate(rows)
    rus = {m: results.get(m, {}).get("rus") for m in ORDER}
    runlog.write_json(run_dir / "summary.json", {"rows": rows, "targets": targets, "estimated": est, "rus": rus})
    report = run_dir / "hardware_v1_2.md"
    write_report(report, rows, targets, results, est, not args.submit, backend.name, run_dir.name)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"{kind}_{backend.name}.md").write_text(report.read_text(encoding="utf-8"), encoding="utf-8")
    for r in rows:
        if "none_std" in r:
            print(f"{r['circuit']:15} {r['depth_class']:7} 2q {r['two_qubit_gates']:3}  none {r['none']:.4f}  "
                  f"v1 {r['recipe_v1']:.4f} ({r['recipe_v1_branch']})  v1.2 {r['recipe_v1_2']:.4f} "
                  f"({r['recipe_v1_2_branch']})  class {r['v1_class']}")
    for t in targets:
        print(f"{t['id']}: {hv2.verdict_text(t, not args.submit).strip('*')}  {t['detail']}")
    print(f"\nReport: {report}")


if __name__ == "__main__":
    main()
