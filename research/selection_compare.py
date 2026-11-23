"""Compare two seed-selection strategies for the transpiler, without error mitigation.

  A ("gates"): fewest two-qubit gates, then lowest depth
  B ("esp"):   highest estimated success probability (ESP) from the backend's calibration data

Both choose among the same 20 compiled candidates using compile-time information only. Each pick
is then simulated (one run per distinct circuit, shot record split into `repeats` disjoint chunks)
and scored by TVD (counts circuits) or approximation ratio (QAOA).

Caveat: on a fake backend the simulator's noise model is built from the same calibration data
ESP is computed from, so ESP agreeing with the measured error is partly circular. It shows the
formula is consistent, not that ESP predicts errors on real hardware. That needs hardware runs.

    .venv/Scripts/python selection_compare.py
    .venv/Scripts/python selection_compare.py --backends FakeKingston FakeSherbrooke --levels 2 3
"""

from __future__ import annotations

import argparse
import math
import shutil
import statistics
import warnings
from collections import Counter
from pathlib import Path

from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import fake_provider

import runlog
from baseline import (
    SELECTION,
    benchmarks,
    compile_with_seed,
    expected_cut,
    ideal_distribution,
    max_cut,
    measured_physical_qubits,
    to_probs,
    tvd,
    with_measurements,
)

warnings.filterwarnings("ignore", category=DeprecationWarning)

SIM_SEED_BASE = 20_000  # disjoint from the other scripts' simulator seeds
STRATEGIES = ("gates", "esp")


def score(bench, ideal: dict[str, float], probs: dict[str, float]) -> float:
    if bench.is_qaoa:
        return expected_cut(probs, bench.edges) / max_cut(bench.circuit.num_qubits, bench.edges)
    return tvd(ideal, probs)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--backends", nargs="+", default=["FakeKingston"])
    parser.add_argument("--levels", type=int, nargs="+", default=[2])
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--shots", type=int, default=4000)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    seeds = list(range(1, args.seeds + 1))

    run_dir = runlog.new_run(
        "selection",
        config={**{k: v for k, v in vars(args).items() if k != "out"}, "transpiler_seeds": seeds,
                "simulator_seed_base": SIM_SEED_BASE},
        method=[
            "No error mitigation.",
            "For each circuit and level, compile once per transpiler seed. Strategy A picks the fewest two-qubit "
            "gates (then depth, then seed); strategy B picks the highest ESP (then fewer 2q gates, depth, seed). "
            "ESP = product of (1 - calibrated error) over all gates and measurements.",
            "Each distinct pick is simulated once with shots x repeats shots (memory=True); the shot record is "
            "split into `repeats` disjoint chunks. Metric per chunk: TVD vs the exact distribution, or "
            "approximation ratio for QAOA.",
            "Caveat: the fake backend's noise model comes from the same calibration data as ESP, so agreement "
            "between ESP and measured error is partly circular; hardware runs are needed to test prediction.",
        ],
    )

    raw: dict = {}
    rows: list[dict] = []
    sim_seed = SIM_SEED_BASE
    for backend_name in args.backends:
        backend = getattr(fake_provider, backend_name)()
        simulator = AerSimulator.from_backend(backend)
        raw[backend_name] = {}
        for bench in benchmarks():
            ideal = ideal_distribution(bench)
            measured_qc = with_measurements(bench)
            for level in args.levels:
                candidates = [compile_with_seed(measured_qc, backend, level, s) for s in seeds]
                picks = {s: min(candidates, key=SELECTION[s]) for s in STRATEGIES}
                same = picks["gates"].seed == picks["esp"].seed
                results = {}
                for strategy in STRATEGIES if not same else ("gates",):
                    sim_seed += 1
                    memory = simulator.run(
                        picks[strategy].circuit, shots=args.shots * args.repeats, seed_simulator=sim_seed, memory=True
                    ).result().get_memory()
                    chunks = [dict(Counter(memory[i * args.shots : (i + 1) * args.shots])) for i in range(args.repeats)]
                    results[strategy] = [score(bench, ideal, to_probs(c)) for c in chunks]
                    raw[backend_name].setdefault(bench.name, {}).setdefault(str(level), {})[strategy] = {
                        "seed": picks[strategy].seed,
                        "simulator_seed": sim_seed,
                        "physical_qubits": measured_physical_qubits(picks[strategy].circuit),
                        "counts": chunks,
                    }
                if same:
                    results["esp"] = results["gates"]

                row = {"backend": backend_name, "circuit": bench.name, "level": level, "same_pick": same,
                       "metric": "approx_ratio" if bench.is_qaoa else "tvd"}
                for s in STRATEGIES:
                    p = picks[s]
                    row.update({
                        f"{s}_seed": p.seed, f"{s}_2q": p.two_qubit_gates, f"{s}_depth": p.depth,
                        f"{s}_esp": p.esp, f"{s}_mean": statistics.mean(results[s]),
                        f"{s}_std": statistics.stdev(results[s]),
                    })
                rows.append(row)
                print(
                    f"{backend_name:15} {bench.name:10} L{level}  A: 2q={row['gates_2q']:<3} ESP={row['gates_esp']:.3f} "
                    f"{row['metric']}={row['gates_mean']:.3f}   B: 2q={row['esp_2q']:<3} ESP={row['esp_esp']:.3f} "
                    f"{row['metric']}={row['esp_mean']:.3f}{'   (same pick)' if same else ''}",
                    flush=True,
                )

    runlog.write_json(run_dir / "counts.json", raw)
    for backend_name in args.backends:
        report = run_dir / f"selection_{backend_name}.md"
        write_markdown([r for r in rows if r["backend"] == backend_name], backend_name, args, run_dir, report)
        shutil.copy(report, args.out / report.name)
    print(f"\nWrote {run_dir}; latest reports copied to {args.out}")


def verdict(row: dict) -> str:
    if row["same_pick"]:
        return "same circuit"
    gap = row["gates_mean"] - row["esp_mean"]
    if row["metric"] == "approx_ratio":
        gap = -gap  # higher ratio is better
    if abs(gap) <= math.hypot(row["gates_std"], row["esp_std"]):
        return "no difference (within spread)"
    return "B (ESP) better" if gap > 0 else "A (gates) better"


def write_markdown(rows: list[dict], backend_name: str, args, run_dir: Path, path: Path) -> None:
    lines = [
        f"# Seed selection: gates vs ESP ({backend_name}, no mitigation)",
        "",
        f"Run `{run_dir.name}` · {args.seeds} transpiler seeds · {args.shots} shots × {args.repeats} repeats. "
        "Raw counts and the method are in the run folder.",
        "",
        "- **A (gates):** fewest two-qubit gates, then lowest depth.",
        "- **B (ESP):** highest estimated success probability from calibration data.",
        "",
        "Metric: TVD (lower is better) or, for QAOA, approximation ratio (higher is better); mean ± std over "
        "repeats. \"Within spread\" means the gap is smaller than the combined std.",
        "",
        "> **Caveat:** on a fake backend the noise model is built from the same calibration data as ESP, so ESP "
        "picking better layouts here is partly circular. It shows the formula is consistent, not that it predicts "
        "real-hardware error. That has to be confirmed on hardware.",
        "",
        "| Circuit | Opt | A: 2q / depth / ESP | B: 2q / depth / ESP | A metric | B metric | Verdict |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['circuit']} | {r['level']} | {r['gates_2q']} / {r['gates_depth']} / {r['gates_esp']:.3f} | "
            f"{r['esp_2q']} / {r['esp_depth']} / {r['esp_esp']:.3f} | {r['gates_mean']:.3f} ± {r['gates_std']:.3f} | "
            f"{r['esp_mean']:.3f} ± {r['esp_std']:.3f} | {verdict(r)} |"
        )
    tally = Counter(verdict(r) for r in rows)
    lines += ["", "## Tally", "", "| Verdict | Circuits |", "|---|---|"]
    lines += [f"| {v} | {n} |" for v, n in tally.most_common()]
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
