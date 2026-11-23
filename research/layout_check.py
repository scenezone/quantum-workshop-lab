"""Check which physical qubits the transpiler picks for a circuit, and how noisy they are.

Written to verify the Week 0 claim "on GHZ-5, level 2 beat level 1 because it chose better
qubits". For each backend, optimization level and seed it prints the physical qubits,
their readout errors, the two-qubit gate errors on the couplers used, and the estimated
success probability (ESP = product of (1 - error) over every gate and measurement), next to
the TVD actually measured in simulation.

    .venv/Scripts/python layout_check.py                       # GHZ-5, levels 1 and 2
    .venv/Scripts/python layout_check.py --circuit QFT-4 --levels 1 2 3
"""

from __future__ import annotations

import argparse
import statistics
from pathlib import Path

from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import fake_provider

from baseline import (
    DEFAULT_BACKENDS,
    benchmarks,
    compile_best_of_seeds,
    compile_with_seed,
    estimated_success_probability,
    gate_error,
    ideal_distribution,
    measured_physical_qubits,
    run_repeats,
    to_probs,
    tvd,
    with_measurements,
)

WEEK0_SEED = 11


def describe(compiled, target) -> dict:
    """Error figures for the physical qubits and couplers a compiled circuit actually uses."""
    esp = estimated_success_probability(compiled, target)
    couplers: dict[tuple[int, int], tuple[str, float]] = {}
    for instruction in compiled.data:
        if instruction.operation.num_qubits != 2 or instruction.operation.name == "barrier":
            continue
        qargs = tuple(compiled.find_bit(q).index for q in instruction.qubits)
        couplers[tuple(sorted(qargs))] = (instruction.operation.name, gate_error(target, instruction.operation.name, qargs) or 0.0)
    qubits = measured_physical_qubits(compiled)
    props = target.qubit_properties
    return {
        "qubits": qubits,
        "readout": [gate_error(target, "measure", (q,)) or 0.0 for q in qubits],
        "t1_us": [props[q].t1 * 1e6 if props and props[q].t1 else float("nan") for q in qubits],
        "t2_us": [props[q].t2 * 1e6 if props and props[q].t2 else float("nan") for q in qubits],
        "couplers": couplers,
        "esp": esp,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--circuit", default="GHZ-5")
    parser.add_argument("--levels", type=int, nargs="+", default=[1, 2])
    parser.add_argument("--backends", nargs="+", default=list(DEFAULT_BACKENDS))
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--shots", type=int, default=4000)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()

    bench = next(b for b in benchmarks() if b.name == args.circuit)
    ideal = ideal_distribution(bench)
    measured_qc = with_measurements(bench)
    lines = [
        f"# Layout check: {bench.name}",
        "",
        f"{args.shots} shots × {args.repeats} repeats per row. ESP = estimated success probability "
        "from the backend's calibration data (product of 1 − error over all gates and measurements). "
        "Higher ESP should mean lower TVD.",
        "",
    ]

    for name in args.backends:
        backend = getattr(fake_provider, name)()
        target = backend.target
        simulator = AerSimulator.from_backend(backend)
        lines += [f"## {name}", ""]
        summary = [
            "| Opt | Seed | Physical qubits | 2q gates | Depth | Mean readout err | Mean 2q err | ESP | TVD (mean ± std) |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        details: list[str] = []
        for level in args.levels:
            best, _, _ = compile_best_of_seeds(measured_qc, backend, level, list(range(1, args.seeds + 1)))
            configs = [("Week 0 seed", compile_with_seed(measured_qc, backend, level, WEEK0_SEED)), ("best of seeds", best)]
            for label, comp in configs:
                info = describe(comp.circuit, target)
                tvds = [tvd(ideal, to_probs(c)) for c in run_repeats(simulator, comp.circuit, args.shots, args.repeats)]
                coupler_errors = [err for _, err in info["couplers"].values()]
                summary.append(
                    f"| {level} | {comp.seed} ({label}) | {' '.join(map(str, info['qubits']))} | "
                    f"{comp.two_qubit_gates} | {comp.depth} | {statistics.mean(info['readout']):.4f} | "
                    f"{statistics.mean(coupler_errors) if coupler_errors else 0:.4f} | {info['esp']:.3f} | "
                    f"{statistics.mean(tvds):.3f} ± {statistics.stdev(tvds):.3f} |"
                )
                details += [
                    f"**Level {level}, seed {comp.seed} ({label})**",
                    "",
                    "| Physical qubit | Readout error | T1 (µs) | T2 (µs) |",
                    "|---|---|---|---|",
                    *(
                        f"| {q} | {ro:.4f} | {t1:.0f} | {t2:.0f} |"
                        for q, ro, t1, t2 in zip(info["qubits"], info["readout"], info["t1_us"], info["t2_us"])
                    ),
                    "",
                    "| Coupler | Gate | Error |",
                    "|---|---|---|",
                    *(f"| {a}-{b} | {g} | {e:.4f} |" for (a, b), (g, e) in sorted(info["couplers"].items())),
                    "",
                ]
                print(
                    f"{name:<15} L{level} seed {comp.seed:<3} qubits {info['qubits']}  "
                    f"2q={comp.two_qubit_gates} ESP={info['esp']:.3f} TVD={statistics.mean(tvds):.3f}"
                )
        lines += summary + ["", "### Per-qubit detail", ""] + details

    out = args.out / f"layout_check_{bench.name}.md"
    args.out.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
