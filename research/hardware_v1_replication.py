"""Replication round of recipe v1 on the v2 held-out circuits (PREREGISTRATION.md Part G).

The 25 Nov 2026 round (`20261125-145032_hardware-v2`, ibm_marrakesh) showed recipe v1 level with IBM resilience
level 2 on Heisenberg-4 and clearly better on QPE-4, at a third of its cost. This round asks whether that holds:
the same two circuits, the same device, the same budget and shots rule, methods in REVERSED order (drift check,
as in the hardware round 2 of 24 Nov):

  ibm_rl2     1 EstimatorV2 job, resilience_level=2
  recipe_v1   2 SamplerV2 jobs: all-gate folding at 1/3/5; readout calibration (recipe.py, frozen 23 Nov)
  none        1 SamplerV2 job

v1_clip (reported, no target) is computed from recipe_v1's counts. Recipe v2 is not run.

Everything is reused from hardware_v2.py (Part F, unchanged): compilation, plan, shots, job submission with one
resubmission of a failed job, bootstrap errors and the three-way "clearly" verdict.

    .venv/Scripts/python hardware_v1_replication.py --plan-only
    .venv/Scripts/python hardware_v1_replication.py                         # local dry run on FakeKingston
    .venv/Scripts/python hardware_v1_replication.py --submit --confirm-qpu-seconds 70 --max-rus 1.4
"""

from __future__ import annotations

import argparse
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

from qiskit_ibm_runtime import fake_provider

import hardware
import hardware_v2 as hv2
import recipe
import runlog

ORDER = ("ibm_rl2", "recipe_v1", "none")
DEVICE = "ibm_marrakesh"  # the device of the 25 Nov round
REFERENCE_RUN = "20261125-145032_hardware-v2"
REPORTED = ("none", "recipe_v1", "v1_clip", "ibm_rl2")
COMPARISONS = (("recipe_v1", "none"), ("recipe_v1", "ibm_rl2"), ("v1_clip", "recipe_v1"))
HERE = Path(__file__).parent


def evaluate(rows: list[dict], rus: dict, reference: list[dict]) -> tuple[list[dict], list[dict]]:
    """Part G targets (each circuit separately) and the replication table against the 25 Nov round."""
    targets = []
    for r in rows:
        c = r["circuit"]
        for tid, other, rule, ok in (
                ("R1", "none", "v1 clearly better than no mitigation", ("clearly better",)),
                ("R2", "ibm_rl2", "v1 not clearly worse than IBM level 2", ("clearly better", "no clear difference"))):
            verdict, detail = hv2.compare(r, "recipe_v1", other)
            targets.append({"id": f"{tid} {c}: {rule}", "passed": verdict in ok, "detail": f"v1 {verdict}: {detail}"})
    targets.append({"id": "R2-cost: v1 RUs <= 0.5 x IBM level 2 RUs (round total)",
                    "passed": rus["recipe_v1"] <= 0.5 * rus["ibm_rl2"],
                    "detail": f"v1 {rus['recipe_v1']:.3f} RU vs 0.5 x L2 = {0.5 * rus['ibm_rl2']:.3f} RU"})
    by_name = {r["circuit"]: r for r in reference}
    replication = []
    for r in rows:
        ref = by_name[r["circuit"]]
        for a, b in COMPARISONS:
            then, then_detail = hv2.compare(ref, a, b)
            now, now_detail = hv2.compare(r, a, b)
            replication.append({"circuit": r["circuit"], "comparison": f"{a} vs {b}", "25 Nov": then,
                                "25 Nov detail": then_detail, "now": now, "now detail": now_detail,
                                "same": then == now})
    return targets, replication


def write_report(path: Path, rows, targets, replication, results, est, dry_run, backend_name, run_id) -> None:
    lines = [f"# Recipe v1 replication round (Part G): {backend_name}{' (DRY RUN, local simulator)' if dry_run else ''}",
             "", f"Run `{run_id}`. Circuits: Heisenberg-4, QPE-4 (seen data since 25 Nov). Order: "
             f"{' → '.join(ORDER)}. Reference: `{REFERENCE_RUN}`.", ""]
    if dry_run:
        lines += ["> **DRY RUN, not evidence.** Sampler jobs ran locally; the IBM Estimator job was built but not "
                  "executed.", ""]
    lines += ["## Jobs, in submission order", "", "| Method | Job ID | Charged s | RUs | Resubmitted |", "|---|---|---|---|---|"]
    for m in ORDER:
        res = results.get(m, {})
        for j in res.get("jobs", []):
            lines.append(f"| {m} | `{j['job_id']}` | {j.get('quantum_seconds')} | {j.get('rus')} | "
                         f"{'; '.join(res.get('resubmitted', [])) or '-'} |")
    lines += ["", "| Method | Estimated s | Charged s | RUs |", "|---|---|---|---|",
              *(f"| {m} | {est.get(m, float('nan')):.1f} | {results.get(m, {}).get('quantum_seconds')} | "
                f"{results.get(m, {}).get('rus')} |" for m in ORDER),
              "", "## Error vs exact (± bootstrap std)", "",
              "| Circuit | 2q | Exact | " + " | ".join(REPORTED) + " |", "|---|---|---|" + "---|" * len(REPORTED)]
    for r in rows:
        lines.append(f"| {r['circuit']} | {r['two_qubit_gates']} | {r['exact']:+.3f} | " + " | ".join(
            "not run" if math.isnan(r[m]) else f"{r[m]:.4f} ± {r[f'{m}_std']:.4f} ({r[f'{m}_value']:+.3f}, "
            f"{r[f'{m}_branch']})" for m in REPORTED) + " |")
    lines += ["", "## Pre-registered targets (PREREGISTRATION.md Part G)", "", "| Target | Result | Detail |",
              "|---|---|---|", *(f"| {t['id']} | {hv2.verdict_text(t, dry_run)} | {t['detail']} |" for t in targets),
              "", "## Replication: verdicts on 25 Nov vs now", "",
              "| Circuit | Comparison | 25 Nov | Now | Same verdict |", "|---|---|---|---|---|",
              *(f"| {x['circuit']} | {x['comparison']} | {x['25 Nov']} ({x['25 Nov detail']}) | {x['now']} "
                f"({x['now detail']}) | {'yes' if x['same'] else '**no**'} |" for x in replication),
              "", "`v1_clip` is reported, no target. Two circuits and two rounds show a direction, not a proof.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


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
            raise SystemExit(f"{DEVICE} is not operational now; Part G says wait, do not switch device.")
        print(f"Device: {DEVICE} ({status.pending_jobs} pending jobs)")
    else:
        backend = fake_provider.FakeKingston()
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

    plan = hv2.build_plan(backend, hv2.BUDGET_QS)
    est = {m: v for m, v in hv2.estimated_seconds(plan).items() if m in ORDER}
    jobs = {"ibm_rl2": 0, "recipe_v1": 2, "none": 1}
    charged = {m: est[m] + hv2.SAMPLER_JOB_OVERHEAD_S * jobs[m] for m in ORDER}
    need = 1.5 * sum(charged.values()) / 60
    print("Shots per PUB:", {k: plan["shots"][k] for k in ("none", "v1_scales", "v1_cal", "ibm")})
    print("Expected charged: " + ", ".join(f"{m} {v:.1f} s = {v / 60:.2f} RU" for m, v in charged.items())
          + f"; total {sum(charged.values()) / 60:.2f} RU; Part G needs >= {need:.2f} RU remaining")
    if args.plan_only:
        return
    total = sum(est.values())
    if args.submit:
        if args.confirm_qpu_seconds < total:
            raise SystemExit(f"Refusing: estimate {total:.1f} s > --confirm-qpu-seconds {args.confirm_qpu_seconds}")
        remaining = account_remaining()
        if remaining is None or remaining < need:
            raise SystemExit(f"Refusing: remaining RUs {remaining} < 1.5 x expected = {need:.2f} (Part G)")

    kind = "hardware-v1-replication" if args.submit else "hardware-v1-replication-dryrun"
    run_dir = runlog.new_run(kind, config={
        "backend": backend.name, "submit": args.submit, "order": list(ORDER), "max_rus": args.max_rus,
        "budget_qs_per_circuit": hv2.BUDGET_QS, "circuits": list(plan["tasks"]), "recipe_v1": recipe.VERSION,
        "shots_per_pub": plan["shots"], "estimated_quantum_seconds": est, "reference_run": REFERENCE_RUN,
        "bootstrap": hv2.BOOTSTRAP},
        method=[
            "Four jobs, one at a time, in the reverse of the 25 Nov order: IBM Estimator resilience_level 2; recipe v1 "
            "(Sampler: all-gate folding 1/3/5; Sampler: readout calibration); none (1 Sampler).",
            "Plan, compilation (level 2, best of 20 seeds), shots and analysis from hardware_v2.py (Part F).",
            "Error = |estimate - exact|; spread = bootstrap std; clearly better = gap > combined spread.",
        ])
    results = hv2.run_jobs(plan, backend, list(ORDER), args.max_rus,
                           lambda res: runlog.write_json(run_dir / "results.json", res), account_remaining
                           if args.submit else None, 0.0)
    runlog.write_json(run_dir / "results.json", results)
    if args.submit:
        account_remaining()  # one read after the round
        runlog.write_json(run_dir / "account_reads.json", reads)
    rows = hv2.analyze(plan, results)
    rus = {m: results.get(m, {}).get("rus") for m in ORDER}
    complete = all(v is not None for v in rus.values())
    if not args.submit:
        rus = {m: (v if v is not None else float("nan")) for m, v in rus.items()}
    reference = runlog.read_json(HERE / "results" / "runs" / REFERENCE_RUN / "summary.json")["rows"]
    targets, replication = evaluate(rows, rus, reference) if (complete or not args.submit) else ([], [])
    runlog.write_json(run_dir / "summary.json", {"rows": rows, "targets": targets, "replication": replication,
                                                 "estimated": est, "rus": rus})
    report = run_dir / "hardware_v1_replication.md"
    write_report(report, rows, targets, replication, results, est, not args.submit, backend.name, run_dir.name)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"{kind}_{backend.name}.md").write_text(report.read_text(encoding="utf-8"), encoding="utf-8")
    for r in rows:
        print(f"{r['circuit']:13} exact {r['exact']:+.3f}  " + "  ".join(f"{m}={r[m]:.4f}" for m in REPORTED))
    for t in targets:
        print(f"{t['id']}: {hv2.verdict_text(t, not args.submit).strip('*')}  {t['detail']}")
    for x in replication:
        print(f"{x['circuit']:13} {x['comparison']:22} 25 Nov: {x['25 Nov']:20} now: {x['now']:20} "
              f"{'same' if x['same'] else 'DIFFERENT'}")
    print(f"\nReport: {report}")


if __name__ == "__main__":
    main()
