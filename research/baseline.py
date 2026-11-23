"""Baseline: 14 benchmark circuits (10 core + 4 deep) on noisy fake IBM backends, no error mitigation.

For every backend, circuit and transpiler optimization level (0-3):
  * transpile with N seeds and keep the best (fewest two-qubit gates, then lowest depth),
  * simulate the best compiled circuit R times with different simulator seeds,
  * report mean and spread of the error metric.

Error metric: total variation distance (TVD) to the exact distribution for counts circuits
(Hellinger fidelity as secondary), approximation ratio for QAOA.

Everything runs locally on Qiskit Aer; no IBM account or hardware time is used.
Run from the research folder with its own venv (see README.md):
    .venv/Scripts/python baseline.py
"""

from __future__ import annotations

import argparse
import csv
import math
import shutil
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit, transpile
from qiskit.circuit.library import QFTGate
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import fake_provider

import runlog

DEFAULT_BACKENDS = ("FakeSherbrooke", "FakeKingston")
OPT_LEVELS = (0, 1, 2, 3)
REPORT_LEVEL = 2  # Qiskit's default level, used for the main tables
SIM_SEED = 1234
# An outcome counts as "expected" if the ideal circuit gives it at least this probability.
EXPECTED_THRESHOLD = 0.05


@dataclass
class Benchmark:
    name: str
    circuit: QuantumCircuit  # no measurements
    measured: list[int]  # qubits to measure, in classical-bit order
    note: str
    edges: list[tuple[int, int]] = field(default_factory=list)  # MaxCut graph (QAOA only)

    @property
    def is_qaoa(self) -> bool:
        return bool(self.edges)


# ---------------------------------------------------------------- circuits


def bell() -> Benchmark:
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    return Benchmark("Bell", qc, [0, 1], "(|00>+|11>)/sqrt2")


def ghz(n: int) -> Benchmark:
    qc = QuantumCircuit(n)
    qc.h(0)
    for i in range(n - 1):
        qc.cx(i, i + 1)
    return Benchmark(f"GHZ-{n}", qc, list(range(n)), f"|{'0' * n}> + |{'1' * n}>")


def _mcz(qc: QuantumCircuit, qubits: list[int]) -> None:
    *controls, target = qubits
    qc.h(target)
    qc.mcx(controls, target)
    qc.h(target)


def grover(n: int, marked: str, iterations: int | None = None) -> Benchmark:
    """Grover search for one marked bitstring (written big-endian, like Qiskit counts).

    Defaults to the optimal number of iterations, floor(pi/4 * sqrt(2^n)).
    """
    if iterations is None:
        iterations = math.floor(math.pi / 4 * math.sqrt(2**n))
    qubits = list(range(n))
    zeros = [i for i, bit in enumerate(reversed(marked)) if bit == "0"]
    qc = QuantumCircuit(n)
    qc.h(qubits)
    for _ in range(iterations):
        if zeros:
            qc.x(zeros)
        _mcz(qc, qubits)  # oracle: flip the phase of |marked>
        if zeros:
            qc.x(zeros)
        qc.h(qubits)  # diffuser: reflect about the uniform superposition
        qc.x(qubits)
        _mcz(qc, qubits)
        qc.x(qubits)
        qc.h(qubits)
    return Benchmark(f"Grover-{n}", qc, qubits, f"marked {marked}, {iterations} iteration(s)")


def qft(n: int, k: int) -> Benchmark:
    """Prepare the Fourier state of k, then inverse-QFT it; the ideal answer is exactly k."""
    qc = QuantumCircuit(n)
    for j in range(n):
        qc.h(j)
        qc.p(2 * math.pi * k * 2**j / 2**n, j)
    qc.append(QFTGate(n).inverse(), range(n))
    return Benchmark(f"QFT-{n}", qc, list(range(n)), f"inverse QFT -> {k:0{n}b}")


def bernstein_vazirani(secret: str) -> Benchmark:
    n = len(secret)
    ancilla = n
    qc = QuantumCircuit(n + 1)
    qc.x(ancilla)
    qc.h(range(n + 1))
    for i, bit in enumerate(reversed(secret)):
        if bit == "1":
            qc.cx(i, ancilla)
    qc.h(range(n))
    return Benchmark(f"BV-{n}", qc, list(range(n)), f"secret {secret}")


def _qaoa_circuit(n: int, edges: list[tuple[int, int]], gammas: list[float], betas: list[float]) -> QuantumCircuit:
    qc = QuantumCircuit(n)
    qc.h(range(n))
    for gamma, beta in zip(gammas, betas):
        for i, j in edges:
            qc.rzz(2 * gamma, i, j)
        qc.rx(2 * beta, range(n))
    return qc


def cut_value(bits: str, edges: list[tuple[int, int]]) -> int:
    value = bits[::-1]  # value[i] is qubit i
    return sum(value[i] != value[j] for i, j in edges)


def expected_cut(probs: dict[str, float], edges: list[tuple[int, int]]) -> float:
    return sum(p * cut_value(bits, edges) for bits, p in probs.items())


def max_cut(n: int, edges: list[tuple[int, int]]) -> int:
    return max(cut_value(format(x, f"0{n}b"), edges) for x in range(2**n))


def _ideal_cut(n: int, edges: list[tuple[int, int]], gammas, betas) -> float:
    return expected_cut(Statevector(_qaoa_circuit(n, edges, list(gammas), list(betas))).probabilities_dict(), edges)


def qaoa_maxcut(n: int, edges: list[tuple[int, int]], label: str, p: int = 1) -> Benchmark:
    """QAOA for MaxCut with p layers, angles optimized on the ideal simulator.

    p=1: grid search. p=2: Nelder-Mead started from the p=1 optimum repeated in both layers
    (deterministic, no random starts).
    """
    best = (-1.0, 0.0, 0.0)
    for gamma in np.linspace(0, math.pi, 25)[1:]:
        for beta in np.linspace(0, math.pi / 2, 25)[1:]:
            cut = _ideal_cut(n, edges, [gamma], [beta])
            if cut > best[0]:
                best = (cut, gamma, beta)
    cut, gamma, beta = best
    gammas, betas = [gamma], [beta]
    if p == 2:
        from scipy.optimize import minimize

        result = minimize(
            lambda x: -_ideal_cut(n, edges, x[:2], x[2:]),
            x0=[gamma, gamma, beta, beta],
            method="Nelder-Mead",
            options={"xatol": 1e-4, "fatol": 1e-6, "maxiter": 2000},
        )
        gammas, betas = list(result.x[:2]), list(result.x[2:])
    elif p != 1:
        raise ValueError("only p=1 and p=2 are supported")
    qc = _qaoa_circuit(n, edges, gammas, betas)
    angles = ", ".join(f"gamma{i + 1}={g:.3f} beta{i + 1}={b:.3f}" for i, (g, b) in enumerate(zip(gammas, betas)))
    note = f"{label}, p={p}, max cut {max_cut(n, edges)}, {angles}"
    name = f"QAOA-{n}" if p == 1 else f"QAOA-{n}-p{p}"
    return Benchmark(name, qc, list(range(n)), note, edges)


RING4 = [(0, 1), (1, 2), (2, 3), (3, 0)]
TRIANGLE = [(0, 1), (1, 2), (0, 2)]
# Added 21 Nov 2026 to find where ZNE starts to pay off (deeper or wider than the core set).
DEEP_SET = ("GHZ-7", "Grover-4", "QFT-5", "QAOA-4-p2")


def benchmarks() -> list[Benchmark]:
    return [
        bell(),
        ghz(3),
        ghz(5),
        grover(2, "11"),
        grover(3, "101"),
        qft(3, 5),
        qft(4, 11),
        bernstein_vazirani("1011"),
        qaoa_maxcut(3, TRIANGLE, "MaxCut triangle"),
        qaoa_maxcut(4, RING4, "MaxCut 4-ring"),
        # deep set
        ghz(7),
        grover(4, "1011", iterations=2),
        qft(5, 21),
        qaoa_maxcut(4, RING4, "MaxCut 4-ring", p=2),
    ]


# ----------------------------------------------------------------- metrics


def ideal_distribution(b: Benchmark) -> dict[str, float]:
    probs = Statevector(b.circuit).probabilities_dict(qargs=b.measured)
    return {k: v for k, v in probs.items() if v > 1e-12}


def with_measurements(b: Benchmark) -> QuantumCircuit:
    qc = b.circuit.copy()
    creg = ClassicalRegister(len(b.measured), "c")
    qc.add_register(creg)
    qc.measure(b.measured, creg)
    return qc


def to_probs(counts: dict[str, int]) -> dict[str, float]:
    shots = sum(counts.values())
    return {k: v / shots for k, v in counts.items()}


def tvd(p: dict[str, float], q: dict[str, float]) -> float:
    """Total variation distance: 0 = identical, 1 = no overlap."""
    keys = set(p) | set(q)
    return 0.5 * sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in keys)


def hellinger_fidelity(p: dict[str, float], q: dict[str, float]) -> float:
    """1 = identical distributions, 0 = no overlap."""
    return sum(math.sqrt(p[k] * q[k]) for k in set(p) & set(q)) ** 2


def shot_noise_tvd(
    ideal: dict[str, float], shots: int, rng: np.random.Generator, repeats: int = 200
) -> float:
    """Mean TVD from finite shots alone (zero hardware noise), averaged over many samples."""
    keys = list(ideal)
    weights = np.array([ideal[k] for k in keys])
    samples = rng.multinomial(shots, weights / weights.sum(), size=repeats)
    return float(np.mean([tvd(ideal, {k: c / shots for k, c in zip(keys, s)}) for s in samples]))


def _is_2q(instruction) -> bool:
    return instruction.operation.num_qubits == 2 and instruction.operation.name != "barrier"


def two_qubit_stats(qc: QuantumCircuit) -> tuple[int, int]:
    count = sum(1 for instruction in qc.data if _is_2q(instruction))
    return count, qc.depth(filter_function=_is_2q)


def measured_physical_qubits(compiled: QuantumCircuit) -> list[int]:
    """Physical qubit measured into each classical bit, in classical-bit order."""
    mapping = {}
    for instruction in compiled.data:
        if instruction.operation.name == "measure":
            clbit = compiled.find_bit(instruction.clbits[0]).index
            mapping[clbit] = compiled.find_bit(instruction.qubits[0]).index
    return [mapping[i] for i in sorted(mapping)]


# ---------------------------------------------------------------- compiling


def gate_error(target, name: str, qargs: tuple[int, ...]) -> float | None:
    """Calibrated error of one gate on specific physical qubits, or None if unknown."""
    if name not in target.operation_names:
        return None
    props = target[name].get(qargs)
    if props is None and len(qargs) == 2:
        props = target[name].get(qargs[::-1])
    return None if props is None or props.error is None else props.error


def estimated_success_probability(compiled: QuantumCircuit, target) -> float:
    """ESP: product of (1 - error) over every gate and measurement, from calibration data only."""
    esp = 1.0
    for instruction in compiled.data:
        name = instruction.operation.name
        if name in ("barrier", "delay"):
            continue
        error = gate_error(target, name, tuple(compiled.find_bit(q).index for q in instruction.qubits))
        if error:
            esp *= 1 - error
    return esp


@dataclass
class Compiled:
    circuit: QuantumCircuit
    seed: int
    two_qubit_gates: int
    depth: int
    two_qubit_depth: int
    esp: float


def compile_with_seed(qc: QuantumCircuit, backend, level: int, seed: int) -> Compiled:
    compiled = transpile(qc, backend, optimization_level=level, seed_transpiler=seed)
    count_2q, depth_2q = two_qubit_stats(compiled)
    esp = estimated_success_probability(compiled, backend.target)
    return Compiled(compiled, seed, count_2q, compiled.depth(), depth_2q, esp)


# Seed-selection strategies. Both use compile-time information only, never a measured error.
SELECTION = {
    "gates": lambda c: (c.two_qubit_gates, c.depth, c.seed),  # A: fewest 2q gates, then depth
    "esp": lambda c: (-c.esp, c.two_qubit_gates, c.depth, c.seed),  # B: highest ESP
}


def compile_best_of_seeds(qc: QuantumCircuit, backend, level: int, seeds: list[int], strategy: str = "gates"):
    """Compile with every seed and keep the best one under `strategy` (see SELECTION)."""
    start = time.perf_counter()
    candidates = [compile_with_seed(qc, backend, level, s) for s in seeds]
    elapsed = time.perf_counter() - start
    best = min(candidates, key=SELECTION[strategy])
    return best, candidates, elapsed


def run_repeats(
    simulator: AerSimulator, compiled: QuantumCircuit, shots: int, repeats: int, seed: int = SIM_SEED
) -> list[dict[str, int]]:
    """Raw counts of `repeats` independent runs (simulator seeds seed, seed+1, ...)."""
    result = simulator.run([compiled] * repeats, shots=shots, seed_simulator=seed).result()
    return [dict(result.get_counts(i)) for i in range(repeats)]


def score(b: Benchmark, ideal: dict[str, float], runs: list[dict], best_cut: int) -> dict:
    tvds = [tvd(ideal, r) for r in runs]
    hfs = [hellinger_fidelity(ideal, r) for r in runs]
    row = {
        "tvd_mean": statistics.mean(tvds),
        "tvd_std": statistics.stdev(tvds) if len(tvds) > 1 else 0.0,
        "hf_mean": statistics.mean(hfs),
        "hf_std": statistics.stdev(hfs) if len(hfs) > 1 else 0.0,
        "approx_ratio_mean": "",
        "approx_ratio_std": "",
    }
    if b.is_qaoa:
        ratios = [expected_cut(r, b.edges) / best_cut for r in runs]
        row["approx_ratio_mean"] = statistics.mean(ratios)
        row["approx_ratio_std"] = statistics.stdev(ratios) if len(ratios) > 1 else 0.0
    return row


# -------------------------------------------------------------------- main


def run_backend(
    backend_name: str, shots: int, seeds: list[int], repeats: int, raw: dict | None = None
) -> list[dict]:
    """Run every benchmark at every level. Raw counts go into `raw[circuit][level]` if given."""
    backend = getattr(fake_provider, backend_name)()
    simulator = AerSimulator.from_backend(backend)
    rng = np.random.default_rng(SIM_SEED)
    rows: list[dict] = []

    for b in benchmarks():
        ideal = ideal_distribution(b)
        best_cut = max_cut(b.circuit.num_qubits, b.edges) if b.is_qaoa else 0
        ideal_ratio = expected_cut(ideal, b.edges) / best_cut if b.is_qaoa else ""
        floor = shot_noise_tvd(ideal, shots, rng)
        measured_qc = with_measurements(b)
        logical_2q, _ = two_qubit_stats(transpile(b.circuit, basis_gates=["cx", "u"], optimization_level=0))

        for level in OPT_LEVELS:
            best, candidates, transpile_s = compile_best_of_seeds(measured_qc, backend, level, seeds)
            seed_2q = [c.two_qubit_gates for c in candidates]
            seed_depth = [c.depth for c in candidates]
            start = time.perf_counter()
            counts = run_repeats(simulator, best.circuit, shots, repeats)
            runs = [to_probs(c) for c in counts]
            simulate_s = time.perf_counter() - start
            if raw is not None:
                raw.setdefault(b.name, {})[str(level)] = {
                    "best_seed": best.seed,
                    "physical_qubits": measured_physical_qubits(best.circuit),
                    "simulator_seeds": [SIM_SEED + i for i in range(repeats)],
                    "counts": counts,
                }

            row = {
                "backend": backend_name,
                "circuit": b.name,
                "qubits": b.circuit.num_qubits,
                "opt_level": level,
                "logical_cx": logical_2q,
                "best_seed": best.seed,
                "two_qubit_gates": best.two_qubit_gates,
                "depth": best.depth,
                "two_qubit_depth": best.two_qubit_depth,
                "seed_2q_min": min(seed_2q),
                "seed_2q_median": statistics.median(seed_2q),
                "seed_2q_max": max(seed_2q),
                "seed_depth_median": statistics.median(seed_depth),
                "esp": best.esp,
                **score(b, ideal, runs, best_cut),
                "ideal_approx_ratio": ideal_ratio,
                "shot_noise_tvd": floor,
                "physical_qubits": " ".join(map(str, measured_physical_qubits(best.circuit))),
                "transpile_s_all_seeds": transpile_s,
                "simulate_s": simulate_s,
                "note": b.note,
            }
            rows.append(row)
            metric = (
                f"ratio={row['approx_ratio_mean']:.3f}" if b.is_qaoa else f"TVD={row['tvd_mean']:.3f}"
            )
            print(
                f"{backend_name:<15} {b.name:<9} L{level}  2q={best.two_qubit_gates:<3} "
                f"(seeds {min(seed_2q)}-{max(seed_2q)})  depth={best.depth:<4} {metric}"
            )
    return rows


# ------------------------------------------------------------------ report


def _fmt(value, digits: int = 3) -> str:
    return f"{value:.{digits}f}" if isinstance(value, float) else str(value)


def _pct(old: float, new: float) -> str:
    if old == 0:
        return "n/a"
    return f"{(new - old) / old * 100:+.0f}%"


def _primary(r: dict) -> float:
    return r["approx_ratio_mean"] if r["approx_ratio_mean"] != "" else r["tvd_mean"]


def _table(header: list[str], body: list[list[str]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(cells) + " |" for cells in body]
    return lines


def write_backend_markdown(rows: list[dict], backend_name: str, args, path: Path) -> None:
    by_key = {(r["circuit"], r["opt_level"]): r for r in rows}
    circuits = list(dict.fromkeys(r["circuit"] for r in rows))
    counts_circuits = [c for c in circuits if not c.startswith("QAOA")]
    qaoa_circuits = [c for c in circuits if c.startswith("QAOA")]

    lines = [
        f"# Baseline v2: {backend_name} (no error mitigation)",
        "",
        f"Qiskit Aer with the `{backend_name}` noise model · {args.shots} shots per run · "
        f"{len(args.seed_list)} transpiler seeds ({args.seed_list[0]}-{args.seed_list[-1]}), best kept · "
        f"{args.repeats} simulator repeats per configuration (seed {SIM_SEED}+i) · values are mean ± std over repeats.",
        "",
        "Best-of-seeds rule: fewest two-qubit gates, then lowest depth. "
        "Selection uses compile metrics only, never the measured error.",
        "",
        f"## Counts circuits (optimization level {REPORT_LEVEL})",
        "",
    ]
    body = []
    for c in counts_circuits:
        r = by_key[(c, REPORT_LEVEL)]
        body.append(
            [
                c,
                str(r["qubits"]),
                str(r["logical_cx"]),
                str(r["two_qubit_gates"]),
                f"{r['seed_2q_min']}-{r['seed_2q_max']}",
                str(r["depth"]),
                f"{r['tvd_mean']:.3f} ± {r['tvd_std']:.3f}",
                f"{r['hf_mean']:.3f} ± {r['hf_std']:.3f}",
                f"{r['shot_noise_tvd']:.3f}",
            ]
        )
    lines += _table(
        ["Circuit", "Qubits", "Logical CX", "2q gates (best)", "2q over seeds", "Depth", "TVD", "Hellinger F", "Shot-noise TVD"],
        body,
    )
    lines += ["", f"## QAOA (optimization level {REPORT_LEVEL})", ""]
    body = []
    for c in qaoa_circuits:
        r = by_key[(c, REPORT_LEVEL)]
        body.append(
            [
                c,
                str(r["qubits"]),
                str(r["two_qubit_gates"]),
                f"{r['seed_2q_min']}-{r['seed_2q_max']}",
                str(r["depth"]),
                f"{r['approx_ratio_mean']:.3f} ± {r['approx_ratio_std']:.3f}",
                f"{r['ideal_approx_ratio']:.3f}",
                r["note"],
            ]
        )
    lines += _table(
        ["Circuit", "Qubits", "2q gates (best)", "2q over seeds", "Depth", "Approx. ratio (noisy)", "Approx. ratio (ideal)", "Problem"],
        body,
    )

    lines += [
        "",
        "## Effect of optimization level",
        "",
        "Counts circuits only for gates, depth and TVD (QAOA is scored separately). "
        "\"Median-seed\" is what a single random seed typically gives; \"best\" is best of all seeds.",
        "",
    ]
    body = []
    for level in OPT_LEVELS:
        sel = [by_key[(c, level)] for c in counts_circuits]
        q = [by_key[(c, level)] for c in qaoa_circuits]
        body.append(
            [
                str(level),
                str(sum(r["two_qubit_gates"] for r in sel)),
                _fmt(float(sum(r["seed_2q_median"] for r in sel)), 1),
                str(sum(r["depth"] for r in sel)),
                f"{statistics.mean(r['tvd_mean'] for r in sel):.3f}",
                f"{statistics.median(r['tvd_mean'] for r in sel):.3f}",
                f"{statistics.mean(r['approx_ratio_mean'] for r in q):.3f}",
            ]
        )
    lines += _table(
        ["Opt level", "Total 2q (best)", "Total 2q (median seed)", "Total depth", "Mean TVD", "Median TVD", "Mean QAOA ratio"],
        body,
    )

    lines += [
        "",
        "## Per-circuit change",
        "",
        "Primary metric is TVD (lower is better) or, for QAOA, approximation ratio (higher is better). "
        "Percentages are relative changes.",
        "",
    ]
    body = []
    for c in circuits:
        r0, r1, r2, r3 = (by_key[(c, lv)] for lv in OPT_LEVELS)
        body.append(
            [
                c,
                "ratio" if r0["approx_ratio_mean"] != "" else "TVD",
                f"{r0['two_qubit_gates']} → {r2['two_qubit_gates']} ({_pct(r0['two_qubit_gates'], r2['two_qubit_gates'])})",
                f"{r0['depth']} → {r2['depth']} ({_pct(r0['depth'], r2['depth'])})",
                f"{_primary(r0):.3f} → {_primary(r1):.3f} → {_primary(r2):.3f} → {_primary(r3):.3f}",
                f"{_pct(_primary(r0), _primary(r2))}",
                f"{r2['two_qubit_gates']} / {r3['two_qubit_gates']}",
                f"{_primary(r2) - _primary(r3):+.3f}",
            ]
        )
    lines += _table(
        ["Circuit", "Metric", "2q gates L0 → L2", "Depth L0 → L2", "Metric L0 → L1 → L2 → L3", "Metric change L0 → L2", "2q L2 / L3", "Metric L2 − L3"],
        body,
    )

    lines += [
        "",
        "## Level 2 vs level 3: is the difference real?",
        "",
        "\"Outside spread\" means the gap is larger than the combined std of the two (sqrt(std2² + std3²)). "
        "The std only covers simulator repeats, not seed-to-seed layout variation. When both levels use the "
        "same number of two-qubit gates, any gap comes from which physical qubits were picked, not from "
        "level 3's extra optimization.",
        "",
    ]
    body = []
    for c in circuits:
        r2, r3 = by_key[(c, 2)], by_key[(c, 3)]
        key = "approx_ratio" if r2["approx_ratio_mean"] != "" else "tvd"
        gap = r2[f"{key}_mean"] - r3[f"{key}_mean"]
        spread = math.hypot(r2[f"{key}_std"], r3[f"{key}_std"])
        better3 = gap > 0 if key == "tvd" else gap < 0
        if abs(gap) <= spread:
            verdict = "no difference (within spread)"
        elif r3["two_qubit_gates"] < r2["two_qubit_gates"]:
            verdict = f"L3 {'better' if better3 else 'worse'}: fewer 2q gates"
        else:
            verdict = f"L3 {'better' if better3 else 'worse'}: same 2q gates, different qubits"
        body.append(
            [
                c,
                f"{r2[f'{key}_mean']:.3f} ± {r2[f'{key}_std']:.3f}",
                f"{r3[f'{key}_mean']:.3f} ± {r3[f'{key}_std']:.3f}",
                f"{gap:+.3f}",
                f"{spread:.3f}",
                f"{r2['two_qubit_gates']} / {r3['two_qubit_gates']}",
                verdict,
            ]
        )
    lines += _table(["Circuit", "L2", "L3", "L2 − L3", "Combined std", "2q L2 / L3", "Verdict"], body)

    lines += ["", "## All levels", ""]
    body = []
    for r in rows:
        metric = (
            f"ratio {r['approx_ratio_mean']:.3f} ± {r['approx_ratio_std']:.3f}"
            if r["approx_ratio_mean"] != ""
            else f"TVD {r['tvd_mean']:.3f} ± {r['tvd_std']:.3f}"
        )
        body.append(
            [
                r["circuit"],
                str(r["opt_level"]),
                str(r["best_seed"]),
                str(r["two_qubit_gates"]),
                f"{r['seed_2q_min']} / {_fmt(float(r['seed_2q_median']), 1)} / {r['seed_2q_max']}",
                str(r["depth"]),
                metric,
                f"{r['hf_mean']:.3f}",
                r["physical_qubits"],
                f"{r['transpile_s_all_seeds']:.1f}",
            ]
        )
    lines += _table(
        ["Circuit", "Opt", "Best seed", "2q gates", "2q min / median / max over seeds", "Depth", "Primary metric", "Hellinger F", "Physical qubits", "Transpile s (all seeds)"],
        body,
    )
    lines += [
        "",
        "## Column meanings",
        "",
        "- **Logical CX**: CNOTs before mapping to hardware (decomposed to CX + U).",
        "- **2q gates**: two-qubit gates after transpiling (ECR on Eagle, CZ on Heron), including routing SWAPs.",
        "- **TVD**: total variation distance from the exact distribution. 0 is perfect, 1 is completely wrong.",
        "- **Hellinger F**: Hellinger fidelity with the exact distribution. 1 is perfect.",
        "- **Approx. ratio**: expected cut of the measured distribution divided by the maximum cut.",
        "- **Shot-noise TVD**: mean TVD from finite shots alone with zero hardware noise.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_comparison(all_rows: list[dict], backends: list[str], path: Path) -> None:
    by_key = {(r["backend"], r["circuit"], r["opt_level"]): r for r in all_rows}
    circuits = list(dict.fromkeys(r["circuit"] for r in all_rows))
    header = ["Circuit", "Metric"]
    for name in backends:
        header += [f"{name} 2q", f"{name} depth", f"{name} metric"]
    body = []
    for c in circuits:
        first = by_key[(backends[0], c, REPORT_LEVEL)]
        cells = [c, "ratio" if first["approx_ratio_mean"] != "" else "TVD"]
        for name in backends:
            r = by_key[(name, c, REPORT_LEVEL)]
            cells += [str(r["two_qubit_gates"]), str(r["depth"]), f"{_primary(r):.3f}"]
        body.append(cells)
    lines = [
        f"# Backend comparison (optimization level {REPORT_LEVEL}, best of seeds, no mitigation)",
        "",
        "Metric: TVD for counts circuits (lower is better), approximation ratio for QAOA (higher is better). "
        "Per-backend detail is in `baseline_<backend>.md`.",
        "",
        *_table(header, body),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--backends", nargs="+", default=list(DEFAULT_BACKENDS), help="fake backend class names")
    parser.add_argument("--shots", type=int, default=4000)
    parser.add_argument("--seeds", type=int, default=20, help="number of transpiler seeds (1..N)")
    parser.add_argument("--repeats", type=int, default=10, help="simulator repeats per configuration")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.seed_list = list(range(1, args.seeds + 1))
    args.out.mkdir(parents=True, exist_ok=True)

    run_dir = runlog.new_run(
        "baseline",
        config={
            "backends": args.backends,
            "shots": args.shots,
            "transpiler_seeds": args.seed_list,
            "seed_selection": "gates: fewest two-qubit gates, then depth, then seed",
            "repeats": args.repeats,
            "simulator_seed_base": SIM_SEED,
            "optimization_levels": list(OPT_LEVELS),
            "circuits": [b.name for b in benchmarks()],
        },
        method=[
            "No error mitigation.",
            "Each circuit is transpiled with every transpiler seed at each optimization level; the seed with the "
            "fewest two-qubit gates (then lowest depth) is kept. Selection uses compile metrics only.",
            "The kept circuit is simulated on Qiskit Aer with the fake backend's noise model, `repeats` times "
            "with simulator seeds simulator_seed_base + i.",
            "Exact distributions come from the noise-free statevector. Metrics: TVD and Hellinger fidelity "
            "(counts circuits), approximation ratio (QAOA).",
        ],
    )

    all_rows: list[dict] = []
    for name in args.backends:
        raw: dict = {}
        rows = run_backend(name, args.shots, args.seed_list, args.repeats, raw)
        all_rows += rows
        runlog.write_json(run_dir / f"counts_{name}.json", raw)
        write_backend_markdown(rows, name, args, run_dir / f"baseline_{name}.md")

    with open(run_dir / "baseline.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)
    write_comparison(all_rows, args.backends, run_dir / "comparison.md")
    # Latest copies at the top of results/; the run folder keeps the full record.
    for path in run_dir.iterdir():
        if path.suffix in (".md", ".csv"):
            shutil.copy(path, args.out / path.name)
    print(f"\nWrote {run_dir} (raw counts + reports); latest reports copied to {args.out}")


if __name__ == "__main__":
    main()
