"""Simulator mitigation methods at an equal QPU-time budget, with raw counts saved for re-analysis.

Methods (our own implementations, NOT Qiskit Runtime resilience levels, which have no effect on
fake backends):

  none                 all of the budget on the circuit
  readout              tensored per-qubit readout correction; CAL_FRACTION of the shots on calibration
  zne_<fit>            native folding at scales 1/3/5 (folding.py), equal shots per scale, extrapolated
  readout_zne_<fit>    calibration first, every folded circuit readout-corrected BEFORE extrapolation
  recipe               the pre-registered recipe (recipe.py, PREREGISTRATION.md Part B), if frozen

  <fit>: richardson | linear | exp (known asymptote) | expg (exp, but falls back to linear when the
         result leaves the observable's physical range)

Budget: every method gets the same ESTIMATED QUANTUM SECONDS per circuit (default 3.0 s), where
estimated QPU time = Σ shots × (circuit duration + default repetition delay). Shots are derived
from that, so longer (folded) circuits get fewer shots.

Two stages:
  1. simulate: compile (level 2, best of 20 seeds), run every distinct circuit ONCE with all the
     shots it needs (memory=True), split the shot record into disjoint chunks per repeat and method.
     Saves manifest.json, counts.json and circuits.qpy in results/runs/<id>_mitigation-<set>/.
  2. analyze: compute every method from counts.json, write the report, evaluate targets (test set).

    .venv/Scripts/python mitigation.py --set train          # 14 training circuits
    .venv/Scripts/python mitigation.py --set test           # 6 held-out circuits (PREREGISTRATION.md)
    .venv/Scripts/python mitigation.py --analyze results/runs/<id>_mitigation-train
"""

from __future__ import annotations

import argparse
import csv
import math
import shutil
import statistics
import warnings
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from mitiq.zne.inference import ExpFactory, LinearFactory, RichardsonFactory
from qiskit import ClassicalRegister, QuantumCircuit, qpy
from qiskit.circuit.library import QFTGate
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import fake_provider

import runlog
from baseline import (
    DEEP_SET,
    RING4,
    TRIANGLE,
    bell,
    bernstein_vazirani,
    compile_best_of_seeds,
    expected_cut,
    ghz,
    grover,
    measured_physical_qubits,
    qaoa_maxcut,
    to_probs,
)
from folding import fold, two_qubit_count
from heldout import PRISM6, RING5, heldout_benchmarks

warnings.filterwarnings("ignore", category=DeprecationWarning)

OPT_LEVEL = 2
TRANSPILE_SEEDS = list(range(1, 21))
SIM_SEED_BASE = {"train": 10_000, "test": 30_000}  # disjoint from the other scripts' simulator seeds
SCALE_FACTORS = [1, 3, 5]
SCALE_KEYS = [f"s{s}" for s in SCALE_FACTORS]
CAL_FRACTION = 0.2  # share of each readout method's SHOTS spent on calibration
DEFAULT_BUDGET_QS = 3.0  # estimated quantum seconds per circuit per method
DEEP_MIN_2Q = 13  # "deep" = more than 12 two-qubit gates (PREREGISTRATION.md A3)
GROUPS = ("none", "readout", "zne", "readout_zne")  # data groups: each gets its own budget
FITS = ("richardson", "linear", "exp", "expg")
BASE_METHODS = ("none", "readout", *(f"zne_{f}" for f in FITS), *(f"readout_zne_{f}" for f in FITS))
REFERENCE = "readout_zne_linear"  # F in PREREGISTRATION.md A2

# Shot fractions per circuit key within each data group (divided equally over measurement bases).
SHOT_FRACTIONS = {
    "none": {"s1": 1.0},
    "readout": {"s1": 1 - CAL_FRACTION, "cal0": CAL_FRACTION / 2, "cal1": CAL_FRACTION / 2},
    "zne": {k: 1 / len(SCALE_KEYS) for k in SCALE_KEYS},
    "readout_zne": {
        **{k: (1 - CAL_FRACTION) / len(SCALE_KEYS) for k in SCALE_KEYS},
        "cal0": CAL_FRACTION / 2,
        "cal1": CAL_FRACTION / 2,
    },
}

METHOD_TEXT = [
    "Our own implementations on Qiskit Aer with the fake backend's noise model; NOT Qiskit Runtime "
    "resilience levels (those have no effect on fake backends).",
    f"Compilation: optimization level {OPT_LEVEL}, best of {len(TRANSPILE_SEEDS)} transpiler seeds under the "
    "chosen selection strategy (compile-time information only, never measured error).",
    "Budget: every method gets the same estimated quantum seconds per circuit, including calibration and all "
    "ZNE scale factors. Estimated QPU time = sum of shots x (circuit duration from backend gate durations + "
    "default repetition delay). Shots per circuit are derived from the budget.",
    f"readout: per-qubit (tensored) confusion matrices from all-0 and all-1 calibration circuits on the "
    f"circuit's physical qubits ({int(CAL_FRACTION * 100)}% of the method's shots). Not clipped.",
    f"zne: native unitary folding of the transpiled circuit (G -> G (G^-1 G)^k, no re-optimization) at scale "
    f"factors {SCALE_FACTORS}; two-qubit count verified to scale exactly. Equal shots per scale factor. "
    "Extrapolation with mitiq 1.1.0: Richardson, linear least squares, exponential with a known asymptote "
    "(the observable's value on the fully mixed state), or guarded exponential (expg): exponential, falling "
    "back to linear when the result is outside the observable's physical range.",
    "readout_zne: calibration as in readout; every folded circuit's distribution is readout-corrected, then "
    "extrapolated as in zne.",
    "Repeats: every distinct circuit is simulated once with all shots it needs (memory=True); the shot record "
    "is split into disjoint chunks, one per repeat and method, in a fixed order.",
    "Metric: RMSE of fixed observables vs exact values from the noise-free statevector, per repeat; mean +- "
    "std over repeats.",
]


# ------------------------------------------------------------- observables


@dataclass
class Observable:
    label: str
    basis: str  # key into Task.circuits
    value: Callable[[dict[str, float]], float]
    low: float  # physical range of the observable
    high: float
    exact: float = 0.0
    asymptote: float = 0.0  # value on the fully mixed state (used by exponential extrapolation)


@dataclass
class Task:
    name: str
    note: str
    circuits: dict[str, QuantumCircuit]  # measured logical circuits, one per measurement basis
    observables: list[Observable]
    group: str = "core"


def parity(probs: dict[str, float], clbits: list[int] | None = None) -> float:
    """<product of Z> over the given classical bits (all bits if None)."""
    total = 0.0
    for bits, p in probs.items():
        selected = bits[::-1] if clbits is None else [bits[::-1][i] for i in clbits]
        total += p * (-1) ** sum(b == "1" for b in selected)
    return total


def magnetization(probs: dict[str, float]) -> float:
    """(1/n) Σ <Z_j>."""
    n = len(next(iter(probs)))
    return sum(parity(probs, [j]) for j in range(n)) / n


def probability(bitstring: str) -> Callable[[dict[str, float]], float]:
    return lambda probs: probs.get(bitstring, 0.0)


def measure_in_basis(circuit: QuantumCircuit, qubits: list[int], basis: str) -> QuantumCircuit:
    """Rotate each qubit so that measuring Z measures `basis` (Z, X or Y), then measure."""
    qc = circuit.copy()
    for q in qubits:
        if basis == "X":
            qc.h(q)
        elif basis == "Y":
            qc.sdg(q)
            qc.h(q)
    creg = ClassicalRegister(len(qubits), "c")
    qc.add_register(creg)
    qc.measure(qubits, creg)
    return qc


def exact_distribution(measured: QuantumCircuit) -> dict[str, float]:
    unitary_part = measured.remove_final_measurements(inplace=False)
    qubits = [measured.find_bit(i.qubits[0]).index for i in measured.data if i.operation.name == "measure"]
    return Statevector(unitary_part).probabilities_dict(qargs=qubits)


def qft_on_basis_state(n: int, k: int) -> QuantumCircuit:
    """QFT applied to |k>: a product state whose qubit phases encode k."""
    qc = QuantumCircuit(n)
    for j in range(n):
        if (k >> j) & 1:
            qc.x(j)
    qc.append(QFTGate(n), range(n))
    return qc


def _single(bench, basis: str, label: str, value, low: float, high: float, note: str, group: str) -> Task:
    circuits = {basis: measure_in_basis(bench.circuit, bench.measured, basis)}
    return Task(bench.name, note, circuits, [Observable(label, basis, value, low, high)], group)


def _qft_task(n: int, k: int, group: str) -> Task:
    qc = qft_on_basis_state(n, k)
    qubits = list(range(n))
    circuits = {basis: measure_in_basis(qc, qubits, basis) for basis in ("X", "Y")}
    observables = [
        Observable(f"{basis}{j}", basis, lambda p, j=j: parity(p, [j]), -1.0, 1.0)
        for basis in ("X", "Y")
        for j in qubits
    ]
    return Task(f"QFT-{n}", f"input |{k}> = |{k:0{n}b}>, <X_j> and <Y_j> on every qubit", circuits, observables, group)


def _cut_task(bench, edges, label: str, group: str) -> Task:
    return _single(bench, "Z", "<cut>", lambda pr, e=edges: expected_cut(pr, e), 0.0, float(len(edges)),
                   f"expected cut ({label})", group)


def train_tasks() -> list[Task]:
    def grp(name: str) -> str:
        return "deep" if name in DEEP_SET else "core"

    out = [_single(bell(), "Z", "ZZ", parity, -1.0, 1.0, "<ZZ>", "core")]
    for n in (3, 5, 7):
        # Z-parity of an odd GHZ state is 0 whatever the noise, so it says nothing; X-parity is 1.
        g = ghz(n)
        out.append(_single(g, "X", "X" * n, parity, -1.0, 1.0, f"X-parity <X^{n}>", grp(g.name)))
    for n, marked, iterations in ((2, "11", None), (3, "101", None), (4, "1011", 2)):
        g = grover(n, marked, iterations)
        out.append(_single(g, "Z", f"P({marked})", probability(marked), 0.0, 1.0,
                           f"P({marked}), {g.note.split(', ')[1]}", grp(g.name)))
    out += [_qft_task(3, 5, "core"), _qft_task(4, 11, "core"), _qft_task(5, 21, "deep")]
    out.append(_single(bernstein_vazirani("1011"), "Z", "P(1011)", probability("1011"), 0.0, 1.0, "P(1011)", "core"))
    for n, edges, label, p in ((3, TRIANGLE, "triangle", 1), (4, RING4, "4-ring", 1), (4, RING4, "4-ring", 2)):
        q = qaoa_maxcut(n, edges, f"MaxCut {label}", p)
        out.append(_cut_task(q, edges, f"{label}, p={p}", grp(q.name)))
    return out


def test_tasks() -> list[Task]:
    """Held-out set, PREREGISTRATION.md A3."""
    ising, mirror, grover43, qaoa5, qaoa6 = heldout_benchmarks()
    return [
        _single(ising, "Z", "M", magnetization, -1.0, 1.0, "magnetization (1/4) sum <Z_j>", "heldout"),
        _single(mirror, "Z", "P(0000)", probability("0000"), 0.0, 1.0, "P(0000)", "heldout"),
        _single(grover43, "Z", "P(0110)", probability("0110"), 0.0, 1.0, "P(0110), 3 iterations", "heldout"),
        _qft_task(6, 43, "heldout"),
        _cut_task(qaoa5, RING5, "5-ring, p=2", "heldout"),
        _cut_task(qaoa6, PRISM6, "prism, p=1", "heldout"),
    ]


def tasks(which: str) -> list[Task]:
    out = {"train": train_tasks, "test": test_tasks}[which]()
    for task in out:
        exact = {basis: exact_distribution(qc) for basis, qc in task.circuits.items()}
        for obs in task.observables:
            n = len(next(iter(exact[obs.basis])))
            uniform = {format(i, f"0{n}b"): 1 / 2**n for i in range(2**n)}
            obs.exact = obs.value(exact[obs.basis])
            obs.asymptote = obs.value(uniform)
    return out


# ------------------------------------------------------- readout mitigation


def calibration_circuits(num_qubits: int, physical: list[int]) -> dict[str, QuantumCircuit]:
    circuits = {}
    for key, prepare_one in (("cal0", False), ("cal1", True)):
        qc = QuantumCircuit(num_qubits, len(physical))
        if prepare_one:
            qc.x(physical)
        qc.measure(physical, list(range(len(physical))))
        circuits[key] = qc
    return circuits


def confusion_matrix(zero_probs: dict[str, float], one_probs: dict[str, float], n: int) -> np.ndarray:
    """Tensored confusion matrix A[measured, prepared], indexed like int(bitstring, 2)."""
    full = np.array([[1.0]])
    for clbit in range(n - 1, -1, -1):  # most significant bit first, to match int(bitstring, 2)
        p10 = sum(p for bits, p in zero_probs.items() if bits[::-1][clbit] == "1")
        p01 = sum(p for bits, p in one_probs.items() if bits[::-1][clbit] == "0")
        full = np.kron(full, np.array([[1 - p10, p01], [p10, 1 - p01]]))
    return full


def apply_readout_correction(probs: dict[str, float], matrix: np.ndarray, n: int) -> dict[str, float]:
    vector = np.zeros(2**n)
    for bits, p in probs.items():
        vector[int(bits, 2)] = p
    corrected = np.linalg.solve(matrix, vector)
    return {format(i, f"0{n}b"): float(v) for i, v in enumerate(corrected)}


# ----------------------------------------------------------- extrapolation


def _fit(fit: str, values: list[float], asymptote: float) -> float:
    if fit == "richardson":
        return float(RichardsonFactory.extrapolate(SCALE_FACTORS, values))
    if fit == "linear":
        return float(LinearFactory.extrapolate(SCALE_FACTORS, values))
    try:
        return float(ExpFactory.extrapolate(SCALE_FACTORS, values, asymptote=asymptote))
    except Exception:
        return float(ExpFactory.extrapolate(SCALE_FACTORS, values, asymptote=asymptote, avoid_log=True))


def extrapolate(fit: str, values: list[float], obs: Observable) -> tuple[float, str]:
    """Zero-noise estimate and what happened: 'ok', 'failed', or 'fallback' (expg used linear)."""
    if fit == "expg":
        try:
            value = _fit("exp", values, obs.asymptote)
            if math.isfinite(value) and obs.low <= value <= obs.high:
                return value, "ok"
        except Exception:
            pass
        return _fit("linear", values, obs.asymptote), "fallback"
    try:
        value = _fit(fit, values, obs.asymptote)
        return value, "ok" if math.isfinite(value) else "failed"
    except Exception:
        return float("nan"), "failed"


# ---------------------------------------------------------------- simulate


def shot_plan(per_shot_s: dict[str, dict[str, float]], budget_qs: float) -> dict[str, dict[str, dict[str, int]]]:
    """Shots[group][basis][key] so that each group's estimated QPU time is (just under) budget_qs.

    per_shot_s[basis][key] = circuit duration + repetition delay, in seconds.
    """
    m = len(per_shot_s)
    plan: dict[str, dict[str, dict[str, int]]] = {}
    for group, fractions in SHOT_FRACTIONS.items():
        time_per_shot = sum(f / m * per_shot_s[b][k] for b in per_shot_s for k, f in fractions.items())
        total = budget_qs / time_per_shot
        plan[group] = {b: {k: int(total * f / m) for k, f in fractions.items()} for b in per_shot_s}
    return plan


def simulate(args) -> Path:
    backend = getattr(fake_provider, args.backend)()
    simulator = AerSimulator.from_backend(backend)
    rep_delay = getattr(backend.configuration(), "default_rep_delay", 250e-6) or 250e-6
    all_tasks = tasks(args.set)
    run_dir = runlog.new_run(
        f"mitigation-{args.set}",
        config={
            "set": args.set,
            "backend": args.backend,
            "budget_estimated_quantum_seconds_per_method": args.budget_qs,
            "repeats": args.repeats,
            "seed_selection": args.strategy,
            "optimization_level": OPT_LEVEL,
            "transpiler_seeds": TRANSPILE_SEEDS,
            "scale_factors": SCALE_FACTORS,
            "calibration_fraction_of_shots": CAL_FRACTION,
            "simulator_seed_base": SIM_SEED_BASE[args.set],
            "rep_delay_s": rep_delay,
            "deep_min_two_qubit_gates": DEEP_MIN_2Q,
            "reference_method": REFERENCE,
        },
        method=METHOD_TEXT,
    )

    raw: dict = {}
    task_info: dict = {}
    qpy_circuits: list[QuantumCircuit] = []
    seed = SIM_SEED_BASE[args.set]
    for task in all_tasks:
        compiled: dict[str, dict[str, QuantumCircuit]] = {}
        info: dict = {}
        for basis, logical in task.circuits.items():
            best, _, _ = compile_best_of_seeds(logical, backend, OPT_LEVEL, TRANSPILE_SEEDS, args.strategy)
            physical = measured_physical_qubits(best.circuit)
            circuits = {k: fold(best.circuit, s) for k, s in zip(SCALE_KEYS, SCALE_FACTORS)}
            gates = {k: two_qubit_count(c) for k, c in circuits.items()}
            assert [gates[k] for k in SCALE_KEYS] == [s * gates["s1"] for s in SCALE_FACTORS], (task.name, gates)
            circuits.update(calibration_circuits(backend.num_qubits, physical))
            compiled[basis] = circuits
            qpy_circuits.append(best.circuit)
            info[basis] = {
                "qpy_index": len(qpy_circuits) - 1,
                "best_seed": best.seed,
                "esp": best.esp,
                "physical_qubits": physical,
                "two_qubit_gates": gates,
                "duration_s": {k: c.estimate_duration(backend.target, unit="s") for k, c in circuits.items()},
            }
        per_shot = {b: {k: d + rep_delay for k, d in info[b]["duration_s"].items()} for b in info}
        plan = shot_plan(per_shot, args.budget_qs)

        raw[task.name] = {}
        for basis, circuits in compiled.items():
            raw[task.name][basis] = {}
            info[basis]["simulator_seeds"] = {}
            for key, circuit in circuits.items():
                per_repeat = {g: plan[g][basis][key] for g in GROUPS if key in plan[g][basis]}
                total = args.repeats * sum(per_repeat.values())
                seed += 1
                info[basis]["simulator_seeds"][key] = seed
                memory = simulator.run(circuit, shots=total, seed_simulator=seed, memory=True).result().get_memory()
                chunks, pos = [], 0
                for _ in range(args.repeats):
                    repeat = {}
                    for group, shots in per_repeat.items():
                        repeat[group] = dict(Counter(memory[pos : pos + shots]))
                        pos += shots
                    chunks.append(repeat)
                raw[task.name][basis][key] = chunks
        task_info[task.name] = {
            "group": task.group,
            "note": task.note,
            "bases": list(task.circuits),
            "observables": [
                {"label": o.label, "basis": o.basis, "exact": o.exact, "asymptote": o.asymptote,
                 "low": o.low, "high": o.high}
                for o in task.observables
            ],
            "shots_per_repeat": plan,
            "circuits": info,
        }
        print(f"simulated {task.name:12} ({len(compiled)} basis circuit{'s' if len(compiled) > 1 else ''})", flush=True)

    with open(run_dir / "circuits.qpy", "wb") as f:
        qpy.dump(qpy_circuits, f)
    runlog.write_json(run_dir / "counts.json", raw)
    runlog.update_manifest(run_dir, tasks=task_info)
    return run_dir


# ----------------------------------------------------------------- analyze


def rmse(errors: list[float]) -> float:
    finite = [e for e in errors if math.isfinite(e)]
    return math.sqrt(statistics.mean(e * e for e in finite)) if finite else float("nan")


def _load_recipe():
    """The frozen recipe (PREREGISTRATION.md Part B), or None before it exists."""
    try:
        import recipe
    except ImportError:
        return None
    return recipe if getattr(recipe, "FROZEN", False) else None


def analyze(run_dir: Path, out_dir: Path) -> None:
    manifest = runlog.read_json(run_dir / "manifest.json")
    raw = runlog.read_json(run_dir / "counts.json")
    config = manifest["config"]
    repeats = config["repeats"]
    which = config["set"]
    by_name = {t.name: t for t in tasks(which)}
    recipe = _load_recipe()
    methods = list(BASE_METHODS) + (["recipe"] if recipe else [])

    rows, detail = [], []
    guard_stats = {g: Counter() for g in ("zne_expg", "readout_zne_expg")}
    recipe_choices: Counter = Counter()
    for name, info in manifest["tasks"].items():
        task = by_name[name]
        for obs, saved in zip(task.observables, info["observables"]):
            assert abs(obs.exact - saved["exact"]) < 1e-9, f"{name}: observable definition changed since the run"
        bases = info["bases"]
        two_qubit = sum(c["two_qubit_gates"]["s1"] for c in info["circuits"].values())
        features = {
            "two_qubit_gates": two_qubit,
            "esp": statistics.mean(c["esp"] for c in info["circuits"].values()),
            "n_observables": len(task.observables),
        }
        per_repeat_rmse = {m: [] for m in methods}
        estimates = {m: [] for m in methods}
        failures = {m: 0 for m in methods}

        for r in range(repeats):
            def probs(basis: str, key: str, group: str) -> dict[str, float]:
                return to_probs(raw[name][basis][key][r][group])

            def corrected(basis: str, key: str, group: str) -> dict[str, float]:
                zero, one = probs(basis, "cal0", group), probs(basis, "cal1", group)
                measured = probs(basis, key, group)
                n = len(next(iter(measured)))
                return apply_readout_correction(measured, confusion_matrix(zero, one, n), n)

            dist = {
                "none": {b: probs(b, "s1", "none") for b in bases},
                "readout": {b: corrected(b, "s1", "readout") for b in bases},
            }
            est = {m: [o.value(dist[m][o.basis]) for o in task.observables] for m in ("none", "readout")}
            scaled_values = {}
            for group in ("zne", "readout_zne"):
                get = probs if group == "zne" else corrected
                scaled = {b: [get(b, k, group) for k in SCALE_KEYS] for b in bases}
                scaled_values[group] = [[o.value(p) for p in scaled[o.basis]] for o in task.observables]
                for fit in FITS:
                    method = f"{group}_{fit}"
                    values = []
                    for o, vals in zip(task.observables, scaled_values[group]):
                        value, status = extrapolate(fit, vals, o)
                        values.append(value)
                        failures[method] += status == "failed"
                        if fit == "expg":
                            guard_stats[method][status] += 1
                    est[method] = values
            if recipe:
                values = []
                for j, o in enumerate(task.observables):
                    value, choice = recipe.estimate(
                        features, o, {m: est[m][j] for m in est}, scaled_values["readout_zne"][j]
                    )
                    values.append(value)
                    recipe_choices[choice] += 1
                est["recipe"] = values
            for m in methods:
                per_repeat_rmse[m].append(rmse([e - o.exact for e, o in zip(est[m], task.observables)]))
                estimates[m].append(est[m])

        row = {
            "circuit": name,
            "group": info["group"],
            "observable": info["note"],
            "n_observables": len(task.observables),
            "two_qubit_gates": two_qubit,
            "deep": two_qubit >= DEEP_MIN_2Q,
            "esp": features["esp"],
        }
        for m in methods:
            finite = [x for x in per_repeat_rmse[m] if math.isfinite(x)]
            row[f"{m}_rmse_mean"] = statistics.mean(finite) if finite else float("nan")
            row[f"{m}_rmse_std"] = statistics.stdev(finite) if len(finite) > 1 else 0.0
            row[f"{m}_failed"] = failures[m]
        row.update(costs(info, config))
        finite_methods = [m for m in methods if math.isfinite(row[f"{m}_rmse_mean"])]
        row["best"] = min(finite_methods, key=lambda m: row[f"{m}_rmse_mean"])
        rows.append(row)

        shown = ("none", "readout", REFERENCE, "readout_zne_expg") + (("recipe",) if recipe else ())
        for j, obs in enumerate(task.observables):
            cells = [name, obs.label, f"{obs.exact:+.3f}"]
            for m in shown:
                vals = [e[j] for e in estimates[m] if math.isfinite(e[j])]
                cells.append(f"{statistics.mean(vals):+.3f} ± {statistics.stdev(vals):.3f}" if len(vals) > 1 else "n/a")
            detail.append(cells)

    targets = evaluate_targets(rows) if (which == "test" and recipe) else None
    with open(run_dir / "mitigation.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    if targets:
        runlog.write_json(run_dir / "targets.json", targets)
    report = run_dir / "mitigation.md"
    write_markdown(rows, detail, manifest, methods, guard_stats, recipe_choices, targets, report)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"mitigation_{config['backend']}_{which}"
    shutil.copy(report, out_dir / f"{stem}.md")
    shutil.copy(run_dir / "mitigation.csv", out_dir / f"{stem}.csv")
    for r in rows:
        print(f"{r['circuit']:12} 2q={r['two_qubit_gates']:<4} " + "  ".join(
            f"{m}={r[f'{m}_rmse_mean']:.4f}" for m in ("none", "readout", REFERENCE, "readout_zne_expg")
            + (("recipe",) if recipe else ())) + f"  best={r['best']}")
    if targets:
        for t in targets["targets"]:
            print(f"{t['id']}: {'PASS' if t['passed'] else 'FAIL'}  {t['detail']}")
    print(f"\nReport: {report} (latest copy in {out_dir})")


def costs(info: dict, config: dict) -> dict:
    """Shots and estimated QPU time per data group."""
    rep_delay = config["rep_delay_s"]
    out = {}
    for group in GROUPS:
        shots = qpu = gate = 0.0
        for basis, circuit in info["circuits"].items():
            for key, n in info["shots_per_repeat"][group][basis].items():
                shots += n
                gate += n * circuit["duration_s"][key]
                qpu += n * (circuit["duration_s"][key] + rep_delay)
        out[f"{group}_shots"] = int(shots)
        out[f"{group}_est_qpu_s"] = qpu
        out[f"{group}_est_gate_s"] = gate
    return out


# ----------------------------------------------------------------- targets


def evaluate_targets(rows: list[dict]) -> dict:
    """PREREGISTRATION.md A6, evaluated mechanically on the held-out set."""
    rec = {r["circuit"]: r["recipe_rmse_mean"] for r in rows}
    ref = {r["circuit"]: r[f"{REFERENCE}_rmse_mean"] for r in rows}
    worst_rec, worst_ref = max(rec.values()), max(ref.values())
    deep = [r["circuit"] for r in rows if r["deep"]]
    mean_rec = statistics.mean(rec[c] for c in deep) if deep else float("nan")
    mean_ref = statistics.mean(ref[c] for c in deep) if deep else float("nan")
    clearly_worse = [
        r["circuit"] for r in rows
        if r["recipe_rmse_mean"] - r[f"{REFERENCE}_rmse_mean"] > math.hypot(r["recipe_rmse_std"], r[f"{REFERENCE}_rmse_std"])
    ]
    median_change = statistics.median((rec[c] - ref[c]) / ref[c] for c in rec) * 100
    return {
        "reference": REFERENCE,
        "deep_circuits": deep,
        "targets": [
            {"id": "T1 worst case", "passed": worst_rec <= 0.80 * worst_ref,
             "detail": f"recipe worst {worst_rec:.4f} vs 0.80 x F worst {worst_ref:.4f} = {0.80 * worst_ref:.4f}"},
            {"id": "T2 deep circuits", "passed": bool(deep) and mean_rec <= 0.85 * mean_ref,
             "detail": f"mean over {len(deep)} deep: recipe {mean_rec:.4f} vs 0.85 x F {mean_ref:.4f} = {0.85 * mean_ref:.4f}"},
            {"id": "T3 no harm", "passed": len(clearly_worse) <= 1,
             "detail": f"recipe clearly worse than F on {len(clearly_worse)} circuit(s): {', '.join(clearly_worse) or 'none'}"},
            {"id": "O1 old (median -10%)", "passed": median_change <= -10,
             "detail": f"median change vs F {median_change:+.1f}%"},
        ],
    }


# ------------------------------------------------------------------ report


LABEL = {
    "none": "None",
    "readout": "Readout",
    **{f"zne_{f}": f"ZNE ({f})" for f in FITS},
    **{f"readout_zne_{f}": f"Readout+ZNE ({f})" for f in FITS},
    "recipe": "Recipe",
}


def _separated(row: dict, a: str, b: str) -> bool:
    gap = abs(row[f"{a}_rmse_mean"] - row[f"{b}_rmse_mean"])
    return gap > math.hypot(row[f"{a}_rmse_std"], row[f"{b}_rmse_std"])


def write_markdown(rows, detail, manifest, methods, guard_stats, recipe_choices, targets, path: Path) -> None:
    config = manifest["config"]

    def cell(row: dict, m: str) -> str:
        mean = row[f"{m}_rmse_mean"]
        if not math.isfinite(mean):
            return "fit failed"
        text = f"{mean:.4f} ± {row[f'{m}_rmse_std']:.4f}"
        if row[f"{m}_failed"]:
            text += f" ({row[f'{m}_failed']} failed)"
        return f"**{text}**" if row["best"] == m else text

    def esc(text: str) -> str:
        return text.replace("|", "\\|")

    main = ["none", "readout", REFERENCE, "readout_zne_expg"] + (["recipe"] if "recipe" in methods else [])
    lines = [
        f"# Mitigation: {config['backend']}, {config['set']} set (simulator)",
        "",
        f"Run `{manifest['run_id']}` · budget **{config['budget_estimated_quantum_seconds_per_method']} estimated "
        f"quantum seconds per circuit per method** · {config['repeats']} repeats · seed selection "
        f"`{config['seed_selection']}` · pre-registration SHA-256 `{(manifest.get('preregistration_sha256') or 'none')[:12]}…`. "
        "Raw counts, circuits and the full method are in this run's folder.",
        "",
        "**These are our own implementations, not Qiskit Runtime resilience levels.**",
        "",
    ]
    if targets:
        lines += [
            "## Pre-registered targets (PREREGISTRATION.md A6)",
            "",
            f"Reference F = {LABEL[targets['reference']]}. Deep circuits: {', '.join(targets['deep_circuits']) or 'none'}.",
            "",
            "| Target | Result | Detail |",
            "|---|---|---|",
            *(f"| {t['id']} | **{'PASS' if t['passed'] else 'FAIL'}** | {t['detail']} |" for t in targets["targets"]),
            "",
        ]
    lines += [
        "## Method",
        "",
        *(f"- {line}" for line in manifest["method"]),
        "",
        "## Main methods",
        "",
        "RMSE vs exact, mean ± std over repeats; lower is better. Bold = best of all methods for that circuit.",
        "",
        "| Circuit | 2q gates | Observable | " + " | ".join(LABEL[m] for m in main) + " |",
        "|---|---|---|" + "---|" * len(main),
    ]
    for r in rows:
        lines.append(f"| {r['circuit']} | {r['two_qubit_gates']} | {esc(r['observable'])} | "
                     + " | ".join(cell(r, m) for m in main) + " |")

    zne_methods = [m for m in methods if "zne" in m]
    lines += [
        "",
        "## Extrapolation comparison",
        "",
        "| Circuit | 2q | " + " | ".join(LABEL[m] for m in zne_methods) + " |",
        "|---|---|" + "---|" * len(zne_methods),
    ]
    for r in rows:
        lines.append(f"| {r['circuit']} | {r['two_qubit_gates']} | " + " | ".join(cell(r, m) for m in zne_methods) + " |")

    lines += [
        "",
        "Guarded exponential (expg): how often the exponential result was kept vs replaced by linear "
        "(counted per observable and repeat).",
        "",
        "| Method | Exponential kept | Fell back to linear |",
        "|---|---|---|",
        *(f"| {LABEL[m]} | {s['ok']} | {s['fallback']} |" for m, s in guard_stats.items()),
    ]
    if recipe_choices:
        lines += ["", "Recipe choices (per observable and repeat): "
                  + ", ".join(f"{k} {v}" for k, v in recipe_choices.most_common()) + "."]

    lines += [
        "",
        "## Summary",
        "",
        "| Method | Best (circuits) | Median RMSE | Median change vs none | Worst RMSE |",
        "|---|---|---|---|---|",
    ]
    for m in methods:
        finite = [r for r in rows if math.isfinite(r[f"{m}_rmse_mean"])]
        changes = [(r[f"{m}_rmse_mean"] - r["none_rmse_mean"]) / r["none_rmse_mean"] * 100 for r in finite]
        lines.append(
            f"| {LABEL[m]} | {sum(r['best'] == m for r in rows)} of {len(rows)} | "
            f"{statistics.median(r[f'{m}_rmse_mean'] for r in finite):.4f} | {statistics.median(changes):+.0f}% | "
            f"{max(r[f'{m}_rmse_mean'] for r in finite):.4f} |"
        )

    lines += [
        "",
        "## Budget",
        "",
        f"Estimated quantum seconds per method per circuit (target {config['budget_estimated_quantum_seconds_per_method']} s; "
        f"rep delay {config['rep_delay_s'] * 1e6:.0f} µs per shot) and the shots that buys.",
        "",
        "| Circuit | " + " | ".join(f"{g} shots / est. s" for g in GROUPS) + " |",
        "|---|" + "---|" * len(GROUPS),
    ]
    for r in rows:
        lines.append(f"| {r['circuit']} | " + " | ".join(
            f"{r[f'{g}_shots']} / {r[f'{g}_est_qpu_s']:.2f}" for g in GROUPS) + " |")

    shown = ["none", "readout", REFERENCE, "readout_zne_expg"] + (["recipe"] if "recipe" in methods else [])
    lines += [
        "",
        "## Observable estimates (mean ± std over repeats)",
        "",
        "| Circuit | Observable | Exact | " + " | ".join(LABEL[m] for m in shown) + " |",
        "|---|---|---|" + "---|" * len(shown),
        *("| " + " | ".join(d) + " |" for d in detail),
        "",
        "Readout-corrected and extrapolated values can leave the physical range; only expg (and the recipe, if it "
        "uses it) guards against that.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--set", choices=("train", "test"), default="train")
    parser.add_argument("--backend", default="FakeKingston")
    parser.add_argument("--budget-qs", type=float, default=DEFAULT_BUDGET_QS,
                        help="estimated quantum seconds per circuit per method")
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--strategy", choices=("gates", "esp"), default="gates", help="seed selection")
    parser.add_argument("--analyze", type=Path, help="re-analyze an existing run folder (no simulation)")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()

    if args.set == "test" and not args.analyze and _load_recipe() is None:
        parser.error("the held-out set is only run after the recipe is frozen (PREREGISTRATION.md Part B)")
    run_dir = args.analyze if args.analyze else simulate(args)
    analyze(run_dir, args.out)


if __name__ == "__main__":
    main()
