"""Hardware comparison (PREREGISTRATION.md A7): no mitigation vs our recipe vs IBM resilience levels 1 and 2.

Circuits: Bell and GHZ-5 (sanity) plus the 6 held-out circuits. Five jobs, so every job's
quantum_seconds belongs to exactly one method:

  none     1 SamplerV2 job, the compiled circuits only
  recipe   2 SamplerV2 jobs (folded circuits at 1/3/5; readout calibration), analyzed with recipe.py
  ibm_rl1  1 EstimatorV2 job, resilience_level=1 (IBM's measurement mitigation)
  ibm_rl2  1 EstimatorV2 job, resilience_level=2 (IBM's ZNE + gate twirling + measurement mitigation)

Budget: IBM's SamplerV2 requires one shot count for all PUBs of a job, so none and recipe get equal
ESTIMATED quantum seconds as a method total (BUDGET_QS x 8 circuits), not per circuit as in the simulator.
IBM levels get the same shots per PUB as `none` and add their own overhead. Every job's real usage is
read back from IBM and reported; targets compare measured quantum_seconds.

DEFAULT IS A DRY RUN on FakeKingston (local testing mode). It builds every job exactly as it would be
submitted, runs it locally, analyzes it, and estimates the QPU time. In local mode IBM resilience levels
have NO effect, so dry-run IBM numbers equal no mitigation. A dry run is not evidence.

Real hardware needs all of: --submit, a saved IBM Quantum account (QiskitRuntimeService().save_account),
--backend <device>, and --confirm-qpu-seconds N with N at least the plan's estimate. Nothing is sent otherwise.

    .venv/Scripts/python hardware.py                       # dry run, prints the QPU-time plan
    .venv/Scripts/python hardware.py --submit --backend ibm_kingston --confirm-qpu-seconds 400
"""

from __future__ import annotations

import argparse
import itertools
import math
import statistics
import time
import warnings
from pathlib import Path

import numpy as np
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit_ibm_runtime import EstimatorV2, SamplerV2, fake_provider

import recipe
import runlog
from baseline import bell, compile_best_of_seeds, ghz, measured_physical_qubits
from folding import fold
from heldout import PRISM6, RING5, heldout_benchmarks
from mitigation import (
    OPT_LEVEL,
    SCALE_FACTORS,
    SCALE_KEYS,
    TRANSPILE_SEEDS,
    apply_readout_correction,
    calibration_circuits,
    confusion_matrix,
    extrapolate,
    qft_on_basis_state,
    tasks,
    to_probs,
)

warnings.filterwarnings("ignore", category=DeprecationWarning)

BUDGET_QS = 3.0
HW_CIRCUITS = ("Bell", "GHZ-5", "Ising-4", "Mirror-4", "Grover-4-3it", "QFT-6", "QAOA-5-p2", "QAOA-6")
METHODS = ("none", "recipe", "ibm_rl1", "ibm_rl2")
BOOTSTRAP = 500
RL2_OVERHEAD_GUESS = 3.0  # planning guess only (ZNE runs 3 noise factors); the real value is measured


# ------------------------------------------------------- Pauli observables


def pauli_sum(n: int, terms: list[tuple[str, list[int], float]]) -> SparsePauliOp:
    return SparsePauliOp.from_sparse_list(terms, num_qubits=n).simplify()


def projector(bitstring: str, n: int) -> SparsePauliOp:
    """|b><b| on qubits 0..n-1, b written big-endian like Qiskit counts."""
    signs = [1 if bitstring[::-1][i] == "0" else -1 for i in range(n)]
    terms = []
    for k in range(n + 1):
        for subset in itertools.combinations(range(n), k):
            terms.append(("Z" * k, list(subset), math.prod(signs[i] for i in subset) / 2**n))
    return pauli_sum(n, terms)


def cut_operator(n: int, edges) -> SparsePauliOp:
    terms = [("", [], 0.5 * len(edges))] + [("ZZ", [i, j], -0.5) for i, j in edges]
    return pauli_sum(n, terms)


def estimator_specs() -> dict[str, tuple]:
    """Unmeasured circuit and Pauli observables (same order as the task's observables)."""
    ising, mirror, grover43, qaoa5, qaoa6 = heldout_benchmarks()
    qft6 = qft_on_basis_state(6, 43)
    return {
        "Bell": (bell().circuit, [pauli_sum(2, [("ZZ", [0, 1], 1.0)])]),
        "GHZ-5": (ghz(5).circuit, [pauli_sum(5, [("XXXXX", list(range(5)), 1.0)])]),
        "Ising-4": (ising.circuit, [pauli_sum(4, [("Z", [j], 0.25) for j in range(4)])]),
        "Mirror-4": (mirror.circuit, [projector("0000", 4)]),
        "Grover-4-3it": (grover43.circuit, [projector("0110", 4)]),
        "QFT-6": (qft6, [pauli_sum(6, [(b, [j], 1.0)]) for b in "XY" for j in range(6)]),
        "QAOA-5-p2": (qaoa5.circuit, [cut_operator(5, RING5)]),
        "QAOA-6": (qaoa6.circuit, [cut_operator(6, PRISM6)]),
    }


# ------------------------------------------------------------------ plan


def build_plan(backend, budget_qs: float, circuits: tuple[str, ...] = HW_CIRCUITS) -> dict:
    rep_delay = getattr(backend.configuration(), "default_rep_delay", 250e-6) or 250e-6
    all_tasks = {t.name: t for t in tasks("train") + tasks("test") if t.name in circuits}
    specs = estimator_specs()
    plan = {"rep_delay_s": rep_delay, "tasks": {}}
    for name in circuits:
        task = all_tasks[name]
        unitary, paulis = specs[name]
        for obs, op in zip(task.observables, paulis, strict=True):
            sv_value = Statevector(unitary).expectation_value(op).real
            assert abs(sv_value - obs.exact) < 1e-9, f"{name} {obs.label}: Pauli form {sv_value} != {obs.exact}"
        entry = {"task": task, "sampler": {}, "estimator": None}
        for basis, logical in task.circuits.items():
            best, _, _ = compile_best_of_seeds(logical, backend, OPT_LEVEL, TRANSPILE_SEEDS)
            circuits = {k: fold(best.circuit, s) for k, s in zip(SCALE_KEYS, SCALE_FACTORS)}
            circuits.update(calibration_circuits(backend.num_qubits, measured_physical_qubits(best.circuit)))
            durations = {k: c.estimate_duration(backend.target, unit="s") for k, c in circuits.items()}
            entry["sampler"][basis] = {"circuits": circuits, "durations": durations, "seed": best.seed}
        isa = compile_best_of_seeds(unitary, backend, OPT_LEVEL, TRANSPILE_SEEDS)[0].circuit
        entry["estimator"] = {
            "circuit": isa,
            "observables": [op.apply_layout(isa.layout) for op in paulis],
            "duration": isa.estimate_duration(backend.target, unit="s"),
        }
        plan["tasks"][name] = entry
    plan["shots"] = uniform_shots(plan, budget_qs)
    return plan


def uniform_shots(plan: dict, budget_qs: float) -> dict[str, int]:
    """Shots per PUB for each job. IBM's SamplerV2 needs one shot count per job, so budgets are equal
    per METHOD TOTAL (budget_qs x number of circuits), not per circuit as in the simulator.

    recipe: scale-factor PUBs get n_s shots, calibration PUBs n_c = 0.375 n_s, which puts 20% of the
    recipe's shots on calibration (2 n_c = 0.2 (3 n_s + 2 n_c)).
    """
    rep = plan["rep_delay_s"]
    total = budget_qs * len(plan["tasks"])
    s = [b for e in plan["tasks"].values() for b in e["sampler"].values()]
    none = int(total / sum(b["durations"]["s1"] + rep for b in s))
    per_ns = sum(
        sum(b["durations"][k] + rep for k in SCALE_KEYS)
        + 0.375 * (b["durations"]["cal0"] + b["durations"]["cal1"] + 2 * rep)
        for b in s
    )
    n_s = int(total / per_ns)
    return {"none": none, "recipe_scales": n_s, "recipe_cal": int(0.375 * n_s), "ibm": none}


def estimated_qpu_seconds(plan: dict) -> dict[str, float]:
    rep, shots = plan["rep_delay_s"], plan["shots"]
    est = {m: 0.0 for m in METHODS}
    for entry in plan["tasks"].values():
        for s in entry["sampler"].values():
            d = s["durations"]
            est["none"] += shots["none"] * (d["s1"] + rep)
            est["recipe"] += sum(shots["recipe_scales"] * (d[k] + rep) for k in SCALE_KEYS)
            est["recipe"] += sum(shots["recipe_cal"] * (d[k] + rep) for k in ("cal0", "cal1"))
        base = shots["ibm"] * (entry["estimator"]["duration"] + rep)
        est["ibm_rl1"] += base * 1.1  # plus IBM's own readout calibration; planning guess
        est["ibm_rl2"] += base * RL2_OVERHEAD_GUESS
    return est


# ----------------------------------------------------------------- execute


def job_usage(job) -> float | None:
    """Measured quantum seconds from IBM, or None (local jobs have no usage).

    The charged seconds in the job's metrics come first: on 24 Nov 2026 `job.usage()` returned 0 for two short
    jobs whose metrics show 2 s and 7 s charged (see results/hardware_usage.md)."""
    for getter in (lambda: job.metrics()["usage"]["qpu_charge_time_seconds"],
                   lambda: job.metrics()["usage"]["quantum_seconds"], lambda: job.usage()):
        try:
            value = getter()
            if value is not None:
                return float(value)
        except Exception:
            continue
    return None


def job_rus(job) -> float | None:
    """Usage in IBM Resource Units (1 RU = 1 minute of QPU time), or None if not reported."""
    try:
        value = job.usage(resource_units=True)
        return None if value is None else float(value)
    except Exception:
        return None


def job_metrics(job) -> dict | None:
    """IBM's full metrics record for a job (usage, timestamps, ...), saved verbatim for the audit trail."""
    try:
        return job.metrics()
    except Exception:
        return None


LOCAL_ONE_PUB_PER_JOB = False  # set for dry runs: local Aer fails on multi-PUB jobs of 156-qubit circuits


def _sampler_job(mode, items: list[tuple[str, str, str, object]], shots: int) -> tuple[dict, dict]:
    """Run one SamplerV2 job (one shot count for every PUB); return counts and job info."""
    start = time.time()
    pubs = [(circuit, None, shots) for *_, circuit in items]
    if LOCAL_ONE_PUB_PER_JOB:
        jobs = [SamplerV2(mode=mode).run([pub]) for pub in pubs]
        result = [job.result()[0] for job in jobs]
        job = jobs[0]
    else:
        job = SamplerV2(mode=mode).run(pubs)
        result = job.result()
    counts: dict = {}
    for (name, basis, key, _), pub_result in zip(items, result):
        counts.setdefault(name, {}).setdefault(basis, {})[key] = pub_result.data.c.get_counts()
    info = {"job_id": job.job_id(), "quantum_seconds": None if LOCAL_ONE_PUB_PER_JOB else job_usage(job),
            "rus": None if LOCAL_ONE_PUB_PER_JOB else job_rus(job),
            "metrics": None if LOCAL_ONE_PUB_PER_JOB else job_metrics(job),
            "wall_s": time.time() - start, "shots": shots}
    print(f"job {job.job_id()} ({len(items)} PUBs x {shots} shots) done; quantum_seconds={info['quantum_seconds']} "
          f"RUs={info['rus']}", flush=True)
    return counts, info


def _estimator_job(mode, plan: dict, level: int) -> dict:
    names = list(plan["tasks"])
    estimator = EstimatorV2(mode=mode, options={"resilience_level": level})
    precision = 1 / math.sqrt(plan["shots"]["ibm"])
    pubs = [(e["circuit"], e["observables"], None, precision) for e in (plan["tasks"][n]["estimator"] for n in names)]
    start = time.time()
    job = estimator.run(pubs)
    result = job.result()  # wait: the next job is only submitted after this one finishes
    values = {n: {"evs": [float(x) for x in r.data.evs], "stds": [float(x) for x in r.data.stds]}
              for n, r in zip(names, result)}
    info = {"job_id": job.job_id(), "quantum_seconds": job_usage(job), "rus": job_rus(job), "metrics": job_metrics(job),
            "wall_s": time.time() - start, "resilience_level": level}
    print(f"ibm level {level} job {job.job_id()} done; quantum_seconds={info['quantum_seconds']} RUs={info['rus']}", flush=True)
    return {"jobs": [info], "quantum_seconds": info["quantum_seconds"], "rus": info["rus"], "values": values}


def run_jobs(plan: dict, mode, order: list[str], max_usage: float | None = None, on_progress=None) -> dict:
    """Run methods in `order`, ONE JOB AT A TIME (each finishes before the next is sent).

    Five jobs for a full round: none, recipe (scales), recipe (calibration), IBM level 1, IBM level 2.
    Stops before the next method once the measured usage so far reaches `max_usage` (PREREGISTRATION.md Part E).
    """
    shots = plan["shots"]
    items = {"none": [], "scales": [], "cal": []}
    for name, entry in plan["tasks"].items():
        for basis, s in entry["sampler"].items():
            items["none"].append((name, basis, "s1", s["circuits"]["s1"]))
            items["scales"] += [(name, basis, k, s["circuits"][k]) for k in SCALE_KEYS]
            items["cal"] += [(name, basis, k, s["circuits"][k]) for k in ("cal0", "cal1")]

    results: dict = {}
    spent = 0.0
    for method in order:
        if max_usage is not None and spent >= max_usage:
            print(f"STOP: measured usage {spent:.1f} reached the cap {max_usage}; not submitting {method} or later.")
            break
        if method == "none":
            counts, info = _sampler_job(mode, items["none"], shots["none"])
            results["none"] = {"jobs": [info], "quantum_seconds": info["quantum_seconds"], "rus": info["rus"],
                               "counts": counts}
        elif method == "recipe":
            scale_counts, scale_info = _sampler_job(mode, items["scales"], shots["recipe_scales"])
            cal_counts, cal_info = _sampler_job(mode, items["cal"], shots["recipe_cal"])
            for name, bases in cal_counts.items():
                for basis, keys in bases.items():
                    scale_counts[name][basis].update(keys)
            usage = [scale_info["quantum_seconds"], cal_info["quantum_seconds"]]
            rus = [scale_info["rus"], cal_info["rus"]]
            results["recipe"] = {"jobs": [scale_info, cal_info], "counts": scale_counts,
                                 "quantum_seconds": None if None in usage else sum(usage),
                                 "rus": None if None in rus else sum(rus)}
        elif method in ("ibm_rl1", "ibm_rl2"):
            if LOCAL_ONE_PUB_PER_JOB:
                # Dry run: local mode cannot simulate Estimator observables laid out on all 156 qubits, and
                # ignores resilience levels anyway. Build and check the PUBs, but do not execute them.
                for e in (entry["estimator"] for entry in plan["tasks"].values()):
                    assert all(op.num_qubits == e["circuit"].num_qubits for op in e["observables"])
                results[method] = {"jobs": [], "quantum_seconds": None, "rus": None, "values": None,
                                   "note": "not executed in dry run; PUBs built and checked"}
                continue
            results[method] = _estimator_job(mode, plan, int(method[-1]))
        else:
            raise ValueError(f"unknown method {method}")
        # Cap in seconds. Prefer RUs x 60 (1 RU = 1 min): IBM's usage() seconds are rounded and reported 0
        # for a short Sampler job in the smoke run, while its RUs were 0.0327 (about 2 s).
        rus = results[method].get("rus")
        spent += rus * 60 if rus is not None else (results[method]["quantum_seconds"] or 0.0)
        if on_progress:
            on_progress(results)  # save raw results after every method, before anything can fail
    return results


# ----------------------------------------------------------------- analyze


def sampler_estimates(task, counts_by_key: dict, method: str) -> list[float]:
    """Observable estimates from Sampler counts: 'none' uses s1 only, 'recipe' runs the recipe."""
    if method == "none":
        dist = {b: to_probs(counts_by_key[b]["s1"]) for b in counts_by_key}
        return [o.value(dist[o.basis]) for o in task.observables]
    corrected = {}
    for basis, keys in counts_by_key.items():
        zero, one = to_probs(keys["cal0"]), to_probs(keys["cal1"])
        n = len(next(iter(zero)))
        matrix = confusion_matrix(zero, one, n)
        corrected[basis] = [apply_readout_correction(to_probs(keys[k]), matrix, n) for k in SCALE_KEYS]
    values = []
    for o in task.observables:
        scaled = [o.value(p) for p in corrected[o.basis]]
        estimates = {f"readout_zne_{fit}": extrapolate(fit, scaled, o)[0] for fit in ("linear", "expg")}
        values.append(recipe.estimate({}, o, estimates, scaled)[0])
    return values


def resample(counts: dict[str, int], rng: np.random.Generator) -> dict[str, int]:
    keys = list(counts)
    total = sum(counts.values())
    draws = rng.multinomial(total, np.array([counts[k] for k in keys]) / total)
    return {k: int(c) for k, c in zip(keys, draws) if c}


def rmse(values: list[float], exact: list[float]) -> float:
    return math.sqrt(statistics.mean((v - e) ** 2 for v, e in zip(values, exact)))


def analyze(plan: dict, results: dict) -> list[dict]:
    rng = np.random.default_rng(7)
    rows = []
    for name, entry in plan["tasks"].items():
        task = entry["task"]
        exact = [o.exact for o in task.observables]
        row = {"circuit": name, "two_qubit_gates": sum(
            sum(1 for i in s["circuits"]["s1"].data if i.operation.num_qubits == 2) for s in entry["sampler"].values())}
        for method in ("none", "recipe"):
            if method not in results:  # not run (smoke run, or stopped at the usage cap)
                row[method] = row[f"{method}_std"] = float("nan")
                continue
            counts = results[method]["counts"][name]
            row[method] = rmse(sampler_estimates(task, counts, method), exact)
            boots = []
            for _ in range(BOOTSTRAP):
                fake = {b: {k: resample(c, rng) for k, c in keys.items()} for b, keys in counts.items()}
                boots.append(rmse(sampler_estimates(task, fake, method), exact))
            row[f"{method}_std"] = statistics.stdev(boots)
        for method in ("ibm_rl1", "ibm_rl2"):
            if method not in results or results[method]["values"] is None:  # not run, or dry run
                row[method] = row[f"{method}_std"] = float("nan")
                continue
            v = results[method]["values"][name]
            row[method] = rmse(v["evs"], exact)
            boots = [rmse([rng.normal(m, s) for m, s in zip(v["evs"], v["stds"])], exact) for _ in range(BOOTSTRAP)]
            row[f"{method}_std"] = statistics.stdev(boots)
        rows.append(row)
    return rows


def evaluate(rows: list[dict], qpu: dict[str, float], unit: str = "quantum s") -> list[dict]:
    def clearly_better(r, a, b):
        return r[b] - r[a] > math.hypot(r[f"{a}_std"], r[f"{b}_std"])

    deep = [r for r in rows if r["two_qubit_gates"] > 12]
    wins_rl2 = sum(r["recipe"] < r["ibm_rl2"] for r in rows)
    mean_rec = statistics.mean(r["recipe"] for r in deep) if deep else float("nan")
    mean_rl1 = statistics.mean(r["ibm_rl1"] for r in deep) if deep else float("nan")
    beats_none = sum(clearly_better(r, "recipe", "none") for r in rows)
    return [
        {"id": "H1 vs IBM level 2", "passed": wins_rl2 >= 5 and qpu["recipe"] <= qpu["ibm_rl2"],
         "detail": f"recipe lower RMSE on {wins_rl2}/{len(rows)}; usage ({unit}) recipe {qpu['recipe']:.3f} vs level 2 {qpu['ibm_rl2']:.3f}"},
        {"id": "H2 vs IBM level 1 (deep)", "passed": bool(deep) and mean_rec <= 0.85 * mean_rl1,
         "detail": f"mean over {len(deep)} deep: recipe {mean_rec:.4f} vs 0.85 x level 1 {0.85 * mean_rl1:.4f}"},
        {"id": "H3 beats no mitigation", "passed": beats_none >= 6,
         "detail": f"recipe clearly better than none on {beats_none}/{len(rows)}"},
    ]


def write_report(path: Path, rows, targets, qpu_est, qpu_measured, dry_run: bool, backend_name: str, run_id: str,
                 results: dict | None = None, label: str = ""):
    lines = [
        f"# Hardware comparison: {backend_name}{' (DRY RUN, local simulator)' if dry_run else ''}{label}",
        "",
        f"Run `{run_id}`. Methods: no mitigation, our recipe ({recipe.VERSION}), IBM Runtime resilience levels 1 and 2.",
        "",
    ]
    if results:
        lines += ["## Jobs, in submission order", "",
                  "| Method | Job ID | Quantum seconds (IBM) | Resource Units (IBM) | Wall time s |",
                  "|---|---|---|---|---|"]
        for method, res in results.items():
            for job in res.get("jobs", []):
                qs, ru = job.get("quantum_seconds"), job.get("rus")
                lines.append(f"| {method} | `{job['job_id']}` | {'n/a' if qs is None else f'{qs:.1f}'} | "
                             f"{'n/a' if ru is None else f'{ru:.3f}'} | {job['wall_s']:.0f} |")
        lines += ["", "IBM's full usage metrics for every job are saved verbatim in `results.json` (`metrics`).", ""]
    if dry_run:
        lines += [
            "> **DRY RUN, not evidence.** The Sampler jobs (none, recipe) ran locally on a fake backend, one PUB per "
            "local job. The IBM Estimator jobs were built and checked but not executed: local mode cannot simulate "
            "observables laid out on all 156 qubits, and it ignores resilience levels anyway. Quantum seconds are "
            "estimates.",
            "",
        ]
    lines += [
        "## Quantum seconds",
        "",
        "| Method | Estimated | Measured |",
        "|---|---|---|",
        *(f"| {m} | {qpu_est.get(m, float('nan')):.1f} | {'n/a' if qpu_measured.get(m) is None else f'{qpu_measured[m]:.1f}'} |"
          for m in METHODS),
        "",
        "## RMSE vs exact (± bootstrap std)",
        "",
        "| Circuit | 2q gates | None | Recipe | IBM level 1 | IBM level 2 |",
        "|---|---|---|---|---|---|",
        *(f"| {r['circuit']} | {r['two_qubit_gates']} | " + " | ".join(
            "not run" if math.isnan(r[m]) else f"{r[m]:.4f} ± {r[f'{m}_std']:.4f}" for m in METHODS) + " |"
          for r in rows),
        "",
        "## Pre-registered targets (PREREGISTRATION.md A7)",
        "",
        "| Target | Result | Detail |",
        "|---|---|---|",
        *(f"| {t['id']} | {'n/a (dry run)' if dry_run else ('**PASS**' if t['passed'] else '**FAIL**')} | {t['detail']} |"
          for t in targets),
        "" if targets else "Not evaluated: this run does not contain all four methods (smoke run, or stopped at the usage cap).",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def pick_device(service, candidates: tuple[str, ...] = ("ibm_fez", "ibm_marrakesh")):
    """The least busy operational Heron r2 device among `candidates` (PREREGISTRATION.md Part E)."""
    available = [b for b in service.backends(operational=True, simulator=False) if b.name in candidates]
    if not available:
        raise SystemExit(f"None of {candidates} is available to this account.")
    for b in available:
        print(f"  {b.name}: {b.status().pending_jobs} pending jobs")
    return min(available, key=lambda b: b.status().pending_jobs)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--submit", action="store_true", help="send jobs to real IBM hardware")
    parser.add_argument("--backend", default="FakeKingston",
                        help="fake backend class (dry run), an IBM device name, or 'auto' (least busy of fez/marrakesh)")
    parser.add_argument("--instance", default=None, help="IBM instance CRN, if not the saved account's default")
    parser.add_argument("--confirm-qpu-seconds", type=float, default=0.0,
                        help="required with --submit: QPU seconds you approve spending (>= the estimate)")
    parser.add_argument("--max-usage", type=float, default=None,
                        help="stop submitting further jobs once measured quantum seconds reach this cap")
    parser.add_argument("--order", default="none,recipe,ibm_rl1,ibm_rl2",
                        help="method order; round 2 (drift check) uses ibm_rl2,ibm_rl1,recipe,none")
    parser.add_argument("--round", type=int, default=1, help="round number recorded in the run (Part E)")
    parser.add_argument("--smoke", action="store_true",
                        help="smoke job only: Bell, 1,000 shots, none + IBM level 1; checks both job types and usage")
    parser.add_argument("--budget-qs", type=float, default=BUDGET_QS)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    order = ["none", "ibm_rl1"] if args.smoke else args.order.split(",")
    assert set(order) <= set(METHODS), f"unknown method in --order: {order}"

    if args.submit:
        from qiskit_ibm_runtime import QiskitRuntimeService

        service = QiskitRuntimeService(instance=args.instance) if args.instance else QiskitRuntimeService()
        backend = pick_device(service) if args.backend == "auto" else service.backend(args.backend)
        args.backend = backend.name
        print(f"Device: {backend.name}")
    else:
        backend = getattr(fake_provider, args.backend)()

    plan = build_plan(backend, args.budget_qs, ("Bell",) if args.smoke else HW_CIRCUITS)
    if args.smoke:
        plan["shots"] = {"none": 1000, "recipe_scales": 0, "recipe_cal": 0, "ibm": 1000}
    qpu_est = {m: v for m, v in estimated_qpu_seconds(plan).items() if m in order}
    total = sum(qpu_est.values())
    print("Estimated quantum seconds: " + ", ".join(f"{m} {v:.1f}" for m, v in qpu_est.items()) + f"; total {total:.1f}")

    if args.submit:
        if args.confirm_qpu_seconds < total:
            raise SystemExit(f"Refusing to submit: estimate {total:.1f} s > --confirm-qpu-seconds {args.confirm_qpu_seconds}")
        try:
            print("Account usage:", service.usage())
        except Exception as exc:  # older accounts/plans may not expose usage
            print("Could not read account usage:", exc)

    kind = ("hardware-smoke" if args.smoke else f"hardware-round{args.round}") if args.submit else "hardware-dryrun"
    run_dir = runlog.new_run(
        kind,
        config={"backend": args.backend, "submit": args.submit, "smoke": args.smoke, "round": args.round,
                "order": order, "max_usage": args.max_usage, "budget_qs_per_circuit": args.budget_qs,
                "circuits": list(plan["tasks"]), "recipe_version": recipe.VERSION,
                "estimated_quantum_seconds": qpu_est, "shots_per_pub": plan["shots"], "bootstrap": BOOTSTRAP},
        method=[
            "Five jobs: none (1 SamplerV2 job), recipe (2 SamplerV2 jobs: native folding 1/3/5, and readout "
            "calibration; analyzed with recipe.py), IBM EstimatorV2 resilience_level 1, IBM EstimatorV2 "
            "resilience_level 2.",
            "Compilation: level 2, best of 20 transpiler seeds (fewest two-qubit gates, then depth).",
            "IBM SamplerV2 needs one shot count per job, so none and recipe get equal estimated quantum seconds as "
            "a method total (budget x circuits), not per circuit. IBM levels use the same shots per PUB as none "
            "(precision 1/sqrt(shots)) and add their own overhead. Measured quantum_seconds are read from each job.",
            "RMSE vs exact noise-free values; spread = bootstrap std (Sampler: multinomial resampling of counts; "
            "Estimator: normal draws from the reported std).",
        ],
    )
    if args.submit:
        mode = backend
    else:
        global LOCAL_ONE_PUB_PER_JOB
        LOCAL_ONE_PUB_PER_JOB = True  # dry run only; hardware jobs stay batched as planned
        mode = backend
    def save(res: dict) -> None:
        runlog.write_json(run_dir / "results.json", res)

    results = run_jobs(plan, mode, order, args.max_usage, on_progress=save)
    save(results)
    qpu_measured = {m: results[m]["quantum_seconds"] for m in results}
    complete = all(m in results and (results[m].get("values") is not None or "counts" in results[m]) for m in METHODS)
    rows = analyze(plan, results)
    targets = []
    rus_measured = {m: results[m].get("rus") for m in results}
    if complete or not args.submit:
        # PREREGISTRATION.md Part C (23 Nov, 19:58): compare in RUs if IBM reports them for every method,
        # otherwise in seconds; always one unit for all methods.
        if args.submit and all(rus_measured.get(m) is not None for m in METHODS):
            usage, unit = rus_measured, "RUs"
        else:
            usage = {m: (qpu_measured.get(m) if qpu_measured.get(m) is not None else qpu_est.get(m, float("nan")))
                     for m in METHODS}
            unit = "quantum s"
        targets = evaluate(rows, usage, unit) if not args.smoke else []
    runlog.write_json(run_dir / "summary.json", {"rows": rows, "targets": targets, "qpu_estimated": qpu_est,
                                                 "qpu_measured": qpu_measured, "rus_measured": rus_measured,
                                                 "order": order})
    report = run_dir / "hardware.md"
    label = " (smoke job)" if args.smoke else (f", round {args.round}" if args.submit else "")
    write_report(report, rows, targets, qpu_est, qpu_measured, not args.submit, args.backend, run_dir.name,
                 results, label)
    args.out.mkdir(parents=True, exist_ok=True)
    name = f"hardware_{kind}_{args.backend}.md"
    (args.out / name).write_text(report.read_text(encoding="utf-8"), encoding="utf-8")
    for r in rows:
        print(f"{r['circuit']:12} " + "  ".join(f"{m}={r[m]:.4f}" for m in METHODS))
    print(f"\nReport: {report}")


if __name__ == "__main__":
    main()
