"""Design replay for recipe v1.1 on every saved hardware round (no new jobs, 0 RU). DESIGN DATA, NOT EVIDENCE.

Question: do the three v1.1 rules (recipe_v1_1.py, fixed before this replay) flag the cases where recipe v1 failed
on hardware, and leave the good cases alone?

Independent case = device + calibration day + circuit. ibm_fez rounds 1 and 2 (24 Nov, 15 minutes apart) are one
case per circuit; ibm_marrakesh 25 Nov and 26 Nov are separate cases. 8 + 2 + 2 = 12 cases.

Class of one observable in one round, with w = observable range width and e = |v1 - exact| / w:
  failure    v1 clearly worse than none, or e > 0.10
  good       v1 clearly better than none and e < 0.04
  ambiguous  otherwise
A case takes the worst class over its observables and rounds; it counts as flagged if v1.1 flags any of them.
"Clearly" = error gap > sqrt(sigma_a^2 + sigma_b^2), sigmas from 500 bootstrap replicas (seed 7), as in Parts F/G.
v1.1's bootstrap error uses the flag decided on the real data (the reported estimator, conditional on the flag).
"""
from __future__ import annotations

import hashlib
import math
import warnings
from pathlib import Path

import numpy as np

import recipe
import recipe_v1_1
import runlog
from baseline import to_probs
from hardware import resample
from mitigation import SCALE_KEYS, apply_readout_correction, confusion_matrix, extrapolate, tasks
from mitigation_v2 import tasks as v2_tasks

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
RUNS = HERE / "results" / "runs"
BOOTSTRAP = 500
SEED = 7
FAIL_E, GOOD_E = 0.10, 0.04
ROUNDS = (  # (case group = device + calibration day, round label, run folder, key of the v1 job in results.json)
    ("ibm_fez 24 Nov", "r1", "20261124-104424_hardware-round1", "recipe"),
    ("ibm_fez 24 Nov", "r2", "20261124-105849_hardware-round2", "recipe"),
    ("ibm_marrakesh 25 Nov", "25N", "20261125-145032_hardware-v2", "recipe_v1"),
    ("ibm_marrakesh 26 Nov", "26N", "20261126-120458_hardware-v1-replication", "recipe_v1"),
)
RANK = {"good": 0, "ambiguous": 1, "failure": 2}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def corrected(task, counts: dict) -> dict[str, list[float]]:
    """Readout-corrected value at scales 1/3/5 for every observable of the task."""
    per_basis = {}
    for basis, keys in counts.items():
        zero, one = to_probs(keys["cal0"]), to_probs(keys["cal1"])
        n = len(next(iter(zero)))
        m = confusion_matrix(zero, one, n)
        per_basis[basis] = [apply_readout_correction(to_probs(keys[k]), m, n) for k in SCALE_KEYS]
    return {o.label: [o.value(p) for p in per_basis[o.basis]] for o in task.observables}


def v1_value(o, vals: list[float]) -> tuple[float, str]:
    est = {f"readout_zne_{f}": extrapolate(f, vals, o)[0] for f in ("linear", "expg")}
    return recipe.estimate({}, o, est, vals)


def verdict(err_a: float, std_a: float, err_b: float, std_b: float) -> str:
    gap, sigma = err_b - err_a, math.hypot(std_a, std_b)
    return "clearly better" if gap > sigma else ("clearly worse" if -gap > sigma else "no clear difference")


def classify(v1_vs_none: str, e: float) -> str:
    if v1_vs_none == "clearly worse" or e > FAIL_E:
        return "failure"
    if v1_vs_none == "clearly better" and e < GOOD_E:
        return "good"
    return "ambiguous"


def replay_round(group: str, label: str, run: str, key: str, by_name: dict, rng: np.random.Generator) -> list[dict]:
    res = runlog.read_json(RUNS / run / "results.json")
    records = []
    for name, counts in res[key]["counts"].items():
        task = by_name[name]
        none_counts = res["none"]["counts"][name]
        vals = corrected(task, counts)
        boot_vals = {o.label: [] for o in task.observables}
        boot_none = {o.label: [] for o in task.observables}
        for _ in range(BOOTSTRAP):
            fake = {b: {k: resample(c, rng) for k, c in keys.items()} for b, keys in counts.items()}
            for lab, v in corrected(task, fake).items():
                boot_vals[lab].append(v)
            for o in task.observables:
                boot_none[o.label].append(o.value(to_probs(resample(none_counts[o.basis]["s1"], rng))))
        for o in task.observables:
            v, bv = vals[o.label], np.array(boot_vals[o.label])
            d = [x - o.asymptote for x in v]
            rules = recipe_v1_1.checks(d, bv - o.asymptote)
            v11, branch11, failed = recipe_v1_1.estimate(o, v, bv)
            v1, branch1 = v1_value(o, v)
            none = o.value(to_probs(none_counts[o.basis]["s1"]))
            boot_v1_err = [abs(v1_value(o, list(row))[0] - o.exact) for row in bv]
            boot_v11_err = [abs(row[0] - o.exact) for row in bv] if failed else boot_v1_err
            err = {"none": abs(none - o.exact), "v1": abs(v1 - o.exact), "v11": abs(v11 - o.exact)}
            std = {"none": float(np.std([abs(x - o.exact) for x in boot_none[o.label]], ddof=1)),
                   "v1": float(np.std(boot_v1_err, ddof=1)), "v11": float(np.std(boot_v11_err, ddof=1))}
            w = o.high - o.low
            v1_vs_none = verdict(err["v1"], std["v1"], err["none"], std["none"])
            e = err["v1"] / w
            bd = bv - o.asymptote
            records.append({
                "case": f"{group} | {name}", "group": group, "round": label, "circuit": name, "observable": o.label,
                "exact": o.exact, "asymptote": o.asymptote, "width": w, "scaled": v, "d": d,
                "se_d": [float(np.std(bd[:, i], ddof=1)) for i in range(3)],
                "rules": rules, "failed_rules": failed, "flagged": bool(failed),
                "none": none, "v1": v1, "v1_branch": branch1, "v11": v11, "v11_branch": branch11,
                "err": err, "std": std, "e": e,
                "v1_vs_none": v1_vs_none, "class": classify(v1_vs_none, e),
                "v11_vs_none": verdict(err["v11"], std["v11"], err["none"], std["none"]),
                "v11_vs_v1": verdict(err["v11"], std["v11"], err["v1"], std["v1"]),
            })
    return records


def cases_from(records: list[dict]) -> list[dict]:
    cases = {}
    for r in records:
        c = cases.setdefault(r["case"], {"case": r["case"], "group": r["group"], "circuit": r["circuit"],
                                         "records": []})
        c["records"].append(r)
    out = []
    for c in cases.values():
        recs = c["records"]
        worst = max(recs, key=lambda r: RANK[r["class"]])
        c["class"] = worst["class"]
        c["flagged"] = any(r["flagged"] for r in recs)
        c["rules_fired"] = sorted({rule for r in recs for rule in r["failed_rules"]})
        c["v11_clearly_worse_than_none"] = any(r["v11_vs_none"] == "clearly worse" for r in recs)
        out.append(c)
    return out


def tally(cases: list[dict]) -> dict:
    t = {}
    for cls in ("failure", "ambiguous", "good"):
        group = [c for c in cases if c["class"] == cls]
        t[cls] = {"total": len(group), "flagged": sum(c["flagged"] for c in group),
                  "cases": [c["case"] for c in group], "flagged_cases": [c["case"] for c in group if c["flagged"]]}
    t["v11_clearly_worse_than_none"] = [c["case"] for c in cases if c["v11_clearly_worse_than_none"]]
    return t


def write_report(path: Path, run_id: str, cases: list[dict], t: dict, hashes: dict) -> None:
    L = [f"# Recipe v1.1 design replay (0 RU)", "",
         f"Run `{run_id}`. Saved hardware data only, no new jobs.", "",
         "> **DESIGN DATA, NOT EVIDENCE.** These are the rounds that motivated v1.1. The rules (recipe_v1_1.py, "
         f"k = {recipe_v1_1.K:g}) were fixed from physics before this replay and are not changed because of it.", "",
         "Files: " + ", ".join(f"`{n}` SHA-256 `{h[:16]}…`" for n, h in hashes.items()), "",
         "## Headline", "",
         "| Class | Cases | Flagged by v1.1 |", "|---|---|---|"]
    for cls in ("failure", "ambiguous", "good"):
        L.append(f"| {cls} | {t[cls]['total']} | {t[cls]['flagged']} |")
    L += ["", f"- Failures flagged: **{t['failure']['flagged']}/{t['failure']['total']}**.",
          f"- Good cases flagged (false alarms): **{t['good']['flagged']}/{t['good']['total']}**.",
          f"- Ambiguous cases flagged: {t['ambiguous']['flagged']}/{t['ambiguous']['total']}.",
          f"- v1.1 clearly worse than none (design analogue of T1): "
          f"**{len(t['v11_clearly_worse_than_none'])}/{len(cases)}**"
          + (f" ({', '.join(t['v11_clearly_worse_than_none'])})" if t["v11_clearly_worse_than_none"] else "") + ".",
          "",
          "Class per observable and round: failure = v1 clearly worse than none or e > 0.10; good = v1 clearly "
          "better than none and e < 0.04; ambiguous = rest (e = |v1 - exact| / range width). A case takes its worst "
          "class and is flagged if any of its observables/rounds is flagged.", "",
          "## Cases", "",
          "| Case | Class | Flagged | Rules fired | Round / observable: err none / v1 / v1.1 (v1.1 vs none) |",
          "|---|---|---|---|---|"]
    for c in sorted(cases, key=lambda c: (-RANK[c["class"]], c["case"])):
        detail = "<br>".join(
            f"{r['round']} {r['observable']}: {r['err']['none']:.3f} / {r['err']['v1']:.3f} / {r['err']['v11']:.3f}"
            f" ({r['v11_vs_none']})" for r in c["records"])
        L.append(f"| {c['case']} | {c['class']} | {'yes' if c['flagged'] else 'no'} | "
                 f"{', '.join(c['rules_fired']) or '-'} | {detail} |")
    L += ["", "## Per observable and round", "",
          "d(s) = readout-corrected value minus fully mixed value; SE = bootstrap std. Rules: decay / alive / "
          "one_exp (✓ pass, ✗ fail).", "",
          "| Case | Rd | Obs | exact | d(1) / d(3) / d(5) | SE(d5) | Rules | v1 (branch) | v1.1 | none | e | "
          "v1 vs none | Class |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in sorted(cases, key=lambda c: c["case"]):
        for r in c["records"]:
            rules = " ".join("✓" if r["rules"][k] else "✗" for k in recipe_v1_1.RULES)
            L.append(f"| {c['circuit']} ({c['group']}) | {r['round']} | {r['observable']} | {r['exact']:+.3f} | "
                     f"{' / '.join(f'{x:+.3f}' for x in r['d'])} | {r['se_d'][2]:.3f} | {rules} | "
                     f"{r['v1']:+.3f} ({r['v1_branch']}) | {r['v11']:+.3f} | {r['none']:+.3f} | {r['e']:.3f} | "
                     f"{r['v1_vs_none']} | {r['class']} |")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def main() -> None:
    hashes = {n: sha(HERE / n) for n in ("recipe_v1_1.py", "recipe.py", "v1_1_design_replay.py")}
    run_dir = runlog.new_run("v1-1-design-replay", config={
        "rounds": [{"case_group": g, "round": lab, "run": run, "v1_key": key} for g, lab, run, key in ROUNDS],
        "k": recipe_v1_1.K, "rules": list(recipe_v1_1.RULES), "bootstrap": BOOTSTRAP, "seed": SEED,
        "class_thresholds": {"failure_e": FAIL_E, "good_e": GOOD_E}, "file_sha256": hashes,
        "qpu": "none (saved data only)"}, method=[
        "Replay of recipe v1.1 (v1 + three physics flag rules, k = 2) on all saved hardware rounds.",
        "Design data, not evidence: these rounds motivated v1.1."])
    by_name = {t.name: t for t in tasks("train") + tasks("test") + v2_tasks("test")}
    rng = np.random.default_rng(SEED)
    records = []
    for g, lab, run, key in ROUNDS:
        records += replay_round(g, lab, run, key, by_name, rng)
        print(f"replayed {g} {lab}")
    cases = cases_from(records)
    t = tally(cases)
    runlog.write_json(run_dir / "summary.json", {"tally": t, "cases": [{k: v for k, v in c.items()} for c in cases]})
    write_report(run_dir / "v1_1_design_replay.md", run_dir.name, cases, t, hashes)
    for cls in ("failure", "ambiguous", "good"):
        print(f"{cls:9}: {t[cls]['flagged']}/{t[cls]['total']} flagged  {t[cls]['flagged_cases']}")
    print("v1.1 clearly worse than none:", t["v11_clearly_worse_than_none"] or "none")
    print(f"Report: {run_dir / 'v1_1_design_replay.md'}")


if __name__ == "__main__":
    main()
