"""Noise-scaling robustness of the frozen recipe (PREREGISTRATION.md Part D).

Runs the held-out set at noise scales 0.5, 1.5 and 2.0 (one mitigation.py run each), adds the existing
scale-1.0 run, and evaluates targets N1-N3. Writes its own run folder with links to the child runs.

    .venv/Scripts/python noise_scaling.py
    .venv/Scripts/python noise_scaling.py --reuse results/runs/<a> results/runs/<b> results/runs/<c>
"""

from __future__ import annotations

import argparse
import csv
import math
import shutil
import statistics
from pathlib import Path

import mitigation
import runlog

RESULTS = Path(__file__).parent / "results"
SCALE_ONE_RUN = RESULTS / "runs" / "20261123-112303_mitigation-test"
SCALES = (0.5, 1.5, 2.0)
F = mitigation.REFERENCE


def load(run_dir: Path) -> tuple[float, list[dict], dict]:
    manifest = runlog.read_json(run_dir / "manifest.json")
    rows = list(csv.DictReader(open(run_dir / "mitigation.csv", encoding="utf-8")))
    for r in rows:
        for k, v in r.items():
            try:
                r[k] = float(v)
            except (TypeError, ValueError):
                pass
    targets = runlog.read_json(run_dir / "targets.json")
    return float(manifest["config"].get("noise_scale", 1.0)), rows, targets


def clearly_better(r: dict, a: str, b: str) -> bool:
    """a's RMSE is lower than b's by more than the combined std."""
    return r[f"{b}_rmse_mean"] - r[f"{a}_rmse_mean"] > math.hypot(r[f"{a}_rmse_std"], r[f"{b}_rmse_std"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reuse", type=Path, nargs="*", help="existing noise-scaled run folders (skip simulation)")
    parser.add_argument("--repeats", type=int, default=10)
    args = parser.parse_args()

    run_dir = runlog.new_run(
        "noise-scaling",
        config={"scales": list(SCALES), "scale_one_run": SCALE_ONE_RUN.name, "set": "test", "reference": F},
        method=[
            "Held-out set at noise scales 0.5, 1.5, 2.0 (gate and readout errors x scale, capped at 0.5; T1, T2 / "
            "scale); circuits compiled on the unscaled backend; 3.0 estimated quantum seconds per circuit per method; "
            "10 repeats; recipe v1 unchanged. Scale 1.0 is the existing held-out run.",
            "Targets N1-N3 from PREREGISTRATION.md Part D, evaluated mechanically from each child run's mitigation.csv "
            "and targets.json.",
        ],
    )

    children = list(args.reuse or [])
    if not children:
        for scale in SCALES:
            ns = argparse.Namespace(set="test", backend="FakeKingston", budget_qs=mitigation.DEFAULT_BUDGET_QS,
                                    repeats=args.repeats, strategy="gates", noise_scale=scale)
            child = mitigation.simulate(ns)
            mitigation.analyze(child, RESULTS)
            children.append(child)

    runs = {}
    for child in [SCALE_ONE_RUN, *children]:
        scale, rows, targets = load(child)
        runs[scale] = {"dir": child.name, "rows": rows, "targets": {t["id"].split()[0]: t for t in targets["targets"]}}

    def t_pass(scale: float, tid: str) -> bool:
        return bool(runs[scale]["targets"][tid]["passed"])

    n1 = all(t_pass(s, t) for s in (0.5, 1.5) for t in ("T1", "T2", "T3"))
    rows2 = runs[2.0]["rows"]
    worst_rec = max(r["recipe_rmse_mean"] for r in rows2)
    worst_f = max(r[f"{F}_rmse_mean"] for r in rows2)
    worse2 = [r["circuit"] for r in rows2 if clearly_better(r, F, "recipe")]
    n2 = worst_rec <= worst_f and len(worse2) <= 1
    beats_none = {s: sum(clearly_better(r, "recipe", "none") for r in runs[s]["rows"]) for s in SCALES}
    n3 = all(v >= 4 for v in beats_none.values())

    targets = [
        {"id": "N1 robustness", "passed": n1, "detail": "T1/T2/T3 at ×0.5: " + "/".join(
            "PASS" if t_pass(0.5, t) else "FAIL" for t in ("T1", "T2", "T3")) + "; at ×1.5: " + "/".join(
            "PASS" if t_pass(1.5, t) else "FAIL" for t in ("T1", "T2", "T3"))},
        {"id": "N2 high noise (×2.0)", "passed": n2,
         "detail": f"recipe worst {worst_rec:.4f} vs F worst {worst_f:.4f}; recipe clearly worse than F on "
                   f"{len(worse2)} ({', '.join(worse2) or 'none'})"},
        {"id": "N3 still useful", "passed": n3,
         "detail": "recipe clearly better than none on " + ", ".join(f"×{s:g}: {v}/6" for s, v in beats_none.items())},
    ]
    runlog.write_json(run_dir / "summary.json", {"children": {str(s): v["dir"] for s, v in runs.items()},
                                                 "targets": targets})
    write_report(run_dir / "noise_scaling.md", run_dir.name, runs, targets)
    shutil.copy(run_dir / "noise_scaling.md", RESULTS / "noise_scaling.md")
    for t in targets:
        print(f"{t['id']}: {'PASS' if t['passed'] else 'FAIL'}  {t['detail']}")
    print(f"\nReport: {run_dir / 'noise_scaling.md'}")


def write_report(path: Path, run_id: str, runs: dict, targets: list[dict]) -> None:
    scales = sorted(runs)
    circuits = [r["circuit"] for r in runs[1.0]["rows"]]
    lines = [
        "# Noise-scaling robustness (held-out set, simulator)",
        "",
        f"Run `{run_id}`. Recipe v1 unchanged. Noise scale λ multiplies every gate and readout error (capped at 0.5) "
        "and divides T1/T2. Circuits are compiled on the unscaled `FakeKingston`. Budget: 3.0 estimated quantum seconds "
        "per circuit per method. Targets from PREREGISTRATION.md Part D.",
        "",
        "| Target | Result | Detail |",
        "|---|---|---|",
        *(f"| {t['id']} | **{'PASS' if t['passed'] else 'FAIL'}** | {t['detail']} |" for t in targets),
        "",
        "## A6 targets at each noise scale",
        "",
        "| λ | Run | T1 worst case | T2 deep | T3 no harm | O1 median (old) |",
        "|---|---|---|---|---|---|",
    ]
    for s in scales:
        t = runs[s]["targets"]
        lines.append(f"| ×{s:g} | `{runs[s]['dir']}` | " + " | ".join(
            f"{'PASS' if t[k]['passed'] else 'FAIL'}: {t[k]['detail']}" for k in ("T1", "T2", "T3", "O1")) + " |")

    for label, method in (("Recipe", "recipe"), ("F = readout+ZNE (linear)", F), ("No mitigation", "none")):
        lines += ["", f"## {label}: RMSE by noise scale (mean ± std)", "",
                  "| Circuit | " + " | ".join(f"×{s:g}" for s in scales) + " |", "|---|" + "---|" * len(scales)]
        for c in circuits:
            cells = []
            for s in scales:
                r = next(r for r in runs[s]["rows"] if r["circuit"] == c)
                cells.append(f"{r[f'{method}_rmse_mean']:.4f} ± {r[f'{method}_rmse_std']:.4f}")
            lines.append(f"| {c} | " + " | ".join(cells) + " |")

    lines += ["", "## Summary by noise scale", "",
              "| λ | Median RMSE none | Median RMSE F | Median RMSE recipe | Worst F | Worst recipe |",
              "|---|---|---|---|---|---|"]
    for s in scales:
        rows = runs[s]["rows"]
        med = {m: statistics.median(r[f"{m}_rmse_mean"] for r in rows) for m in ("none", F, "recipe")}
        lines.append(f"| ×{s:g} | {med['none']:.4f} | {med[F]:.4f} | {med['recipe']:.4f} | "
                     f"{max(r[f'{F}_rmse_mean'] for r in rows):.4f} | {max(r['recipe_rmse_mean'] for r in rows):.4f} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
