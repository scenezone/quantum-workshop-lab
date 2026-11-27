"""When does recipe v1 fail, and why did Draper-adder-4 under-correct? Offline, 0 RU. EXPLORATORY, POST HOC.

No IBM calls. Part A and B1 read only the saved hardware counts (every v1 round); Part B2 runs local Aer
simulations on FakeMarrakesh. Nothing here is a pre-registered test: it was asked for after all hardware work
ended (27 Nov 2026), it uses rounds that are already reported, and its thresholds are descriptive.

Notation, per observable (as in recipe v1): d(s) = readout-corrected value at fold scale s minus the fully mixed
value; D0 = exact - fully mixed (the noise-free d). Signs are normalised so that D0 > 0.

  r       = ln(d1/d3) / 2           decay per unit of fold scale, between scales 1 and 3 (needs no exact value)
  kappa   = ln(D0/d1) / r           how much the base circuit (s = 1) loses, in units of r. Recipe v1's exponential
                                    assumes kappa = 1: the base circuit is one unit of the same noise folding adds.
  shape   = ln(d5/d3) / ln(d3/d1)   1 = one clean exponential; > 1 decay speeds up with scale; < 1 slows down
  lambda3 = ln(D0/d3) / ln(D0/d1)   effective noise amplification of the scale-3 circuit (assumed 3), same for 5

Recipe v1's "exp" branch is guarded: when the exponential fit leaves the physical range it silently uses the
linear fit instead (recipe.estimate still labels it "exp"). This script labels those records "exp→linear".

If kappa > 1 the folds amplify the noise less than assumed and v1 under-corrects by about 1 - exp(-(kappa-1) r);
if kappa < 1, it over-corrects. kappa and lambda use the exact value, so they explain an error after the fact; r is
the only one of these numbers a user could compute on an unknown circuit.

    .venv/Scripts/python failure_analysis.py              # everything (simulation part: ~30-40 min)
    .venv/Scripts/python failure_analysis.py --no-sim     # hardware parts only (~2 min)
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import math
import time
import warnings
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

import heldout_v12
import runlog
from baseline import to_probs
from hardware import resample
from mitigation import _fit, apply_readout_correction, confusion_matrix, extrapolate
from mitigation import tasks as v1_tasks
from mitigation_v2 import tasks as v2_tasks
from v1_1_design_replay import ROUNDS as V11_ROUNDS
from v1_1_design_replay import corrected
from v1_1_design_replay import v1_value as _v1_value

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
RUNS = HERE / "results" / "runs"
BOOTSTRAP = 500
SEED = 7
ROUNDS = V11_ROUNDS + (("ibm_marrakesh 26 Nov 22:57", "v12", "20261126-225723_hardware-v1-2", "recipe_v1"),)
NO_SIGNAL = 0.1  # |D0| below this fraction of the range width: nothing for ZNE to extrapolate
R_BINS = (0.0, 0.1, 0.2, math.inf)
DRAPER, CDKM = "Draper-adder-4", "CDKM-adder-3"


# ------------------------------------------------------------------ shared numbers


def decay_numbers(d: list[float], d0: float) -> dict[str, float]:
    """r, kappa, shape, lambda3, lambda5 for sign-normalised d (d0 > 0); nan where undefined."""
    nan = float("nan")
    out = dict.fromkeys(("r", "kappa", "shape", "lambda3", "lambda5"), nan)
    d1, d3, d5 = d
    if d1 > d3 > 0:
        out["r"] = math.log(d1 / d3) / 2
        if d0 > d1:
            out["kappa"] = math.log(d0 / d1) / out["r"]
            out["lambda3"] = math.log(d0 / d3) / math.log(d0 / d1)
            if d5 > 0:
                out["lambda5"] = math.log(d0 / d5) / math.log(d0 / d1)
        if d5 > 0:
            out["shape"] = math.log(d5 / d3) / math.log(d3 / d1)
    return out


def v1_value(o, vals: list[float]) -> tuple[float, str, float]:
    """(recipe v1 value, branch, raw exponential fit). Branch "exp→linear" = the guard fell back to linear."""
    v1, branch = _v1_value(o, vals)
    try:
        raw = _fit("exp", vals, o.asymptote)
    except Exception:
        raw = float("nan")
    if branch == "exp" and extrapolate("expg", vals, o)[1] != "ok":
        branch = "exp→linear"
    return v1, branch, raw


def fmt(x: float, nd: int = 2) -> str:
    return "–" if not math.isfinite(x) else f"{x:.{nd}f}"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ------------------------------------------------------------------ Part A: every hardware record


def all_tasks() -> dict:
    return {t.name: t for t in v1_tasks("train") + v1_tasks("test") + v2_tasks("test") + heldout_v12.tasks()}


def mode_of(rec: dict) -> str:
    if rec["no_signal"]:
        return "M0 no signal (exact ≈ fully mixed)"
    if rec["branch"] == "linear":
        return "M1 no clean decay (linear branch)"
    if rec["branch"] == "exp→linear":
        return "M2 exp fit left the range; guard switched to linear"
    return "M3 folds amplify less than assumed (under)" if rec["signed"] < 0 else \
        "M4 folds amplify more than assumed (over)"


def hardware_records(by_name: dict) -> list[dict]:
    rng = np.random.default_rng(SEED)
    records = []
    for group, label, run, key in ROUNDS:
        res = runlog.read_json(RUNS / run / "results.json")
        for name, counts in res[key]["counts"].items():
            task = by_name[name]
            vals = corrected(task, counts)
            boot = {o.label: [] for o in task.observables}
            for _ in range(BOOTSTRAP):
                fake = {b: {k: resample(c, rng) for k, c in keys.items()} for b, keys in counts.items()}
                for lab, v in corrected(task, fake).items():
                    boot[lab].append(v)
            for o in task.observables:
                w, d0 = o.high - o.low, o.exact - o.asymptote
                sign = 1.0 if d0 >= 0 else -1.0
                dn = [sign * (v - o.asymptote) for v in vals[o.label]]
                v1, branch, exp_raw = v1_value(o, vals[o.label])
                clipped = min(max(exp_raw, o.low), o.high) if math.isfinite(exp_raw) else float("nan")
                nums = decay_numbers(dn, abs(d0))
                bn = sign * (np.array(boot[o.label]) - o.asymptote)
                boot_nums = [decay_numbers(list(row), abs(d0)) for row in bn]
                se = {}
                for k in ("r", "kappa"):
                    xs = np.array([b[k] for b in boot_nums])
                    xs = xs[np.isfinite(xs)]
                    se[k] = float(np.std(xs, ddof=1)) if len(xs) > 1 else float("nan")
                rec = {"group": group, "round": label, "circuit": name, "observable": o.label, "width": w,
                       "exact": o.exact, "asymptote": o.asymptote, "d0": abs(d0), "dn": dn,
                       "se_d": [float(x) for x in np.std(bn, axis=0, ddof=1)],
                       "keep1": dn[0] / abs(d0) if abs(d0) > 0 else float("nan"),
                       "v1": v1, "branch": branch, "exp_raw": exp_raw, "e": abs(v1 - o.exact) / w,
                       "clipped": clipped, "e_if_clipped": abs(clipped - o.exact) / w,
                       "signed": sign * (v1 - o.exact) / w, "no_signal": abs(d0) < NO_SIGNAL * w,
                       **nums, "se_r": se["r"], "se_kappa": se["kappa"]}
                rec["mode"] = mode_of(rec)
                records.append(rec)
        print(f"Part A: {group} {label} done")
    return records


def r_bins(records: list[dict]) -> list[dict]:
    exp = [r for r in records if r["branch"].startswith("exp") and math.isfinite(r["r"])]
    out = []
    for lo, hi in zip(R_BINS, R_BINS[1:]):
        sel = [r for r in exp if lo <= r["r"] < hi]
        es = [r["e"] for r in sel]
        out.append({"lo": lo, "hi": hi, "n": len(sel), "median_e": float(np.median(es)) if es else float("nan"),
                    "max_e": max(es) if es else float("nan"), "over_004": sum(e > 0.04 for e in es),
                    "over_010": sum(e > 0.10 for e in es),
                    "worst": max(sel, key=lambda r: r["e"])["circuit"] if sel else "–"})
    rho = spearmanr([r["r"] for r in exp], [abs(r["signed"]) * r["width"] / r["d0"] for r in exp])
    return out, {"n": len(exp), "spearman": float(rho.statistic), "p": float(rho.pvalue)}


# ------------------------------------------------------------------ Part B1: Draper (and CDKM) on hardware


def z_components(dists: list[dict[str, float]], answer: str) -> list[dict]:
    """Sign-normalised <Z_S> at scales 1/3/5 for every non-empty subset S of the measured bits."""
    n = len(answer)
    rows = []
    for weight in range(1, n + 1):
        for subset in itertools.combinations(range(n), weight):
            ideal = (-1) ** sum(int(answer[::-1][i]) for i in subset)
            z = [ideal * sum(p * (-1) ** sum(int(b[::-1][i]) for i in subset) for b, p in dist.items())
                 for dist in dists]
            exp0 = float("nan")
            if all(x > 0 for x in z):
                slope, icpt = np.polyfit([1, 3, 5], np.log(z), 1)
                exp0 = math.exp(icpt)
            rows.append({"bits": subset, "weight": weight, "z": z, "exp0": exp0,
                         **decay_numbers(z, 1.0)})
    return rows


def free_asymptote(vals: list[float]) -> tuple[float, float]:
    """Three-point fit f(s) = a + B q^s with a free asymptote: (f(0), a)."""
    f1, f3, f5 = vals
    q2 = (f5 - f3) / (f3 - f1)
    if not 0 < q2 < 1:
        return float("nan"), float("nan")
    q = math.sqrt(q2)
    b = (f3 - f1) / (q * (q2 - 1))
    a = f1 - b * q
    return a + b, a


def draper_hardware(by_name: dict) -> dict:
    res = runlog.read_json(RUNS / "20261126-225723_hardware-v1-2" / "results.json")
    out = {}
    for name in (DRAPER, CDKM):
        task = by_name[name]
        (o,) = task.observables
        keys = res["recipe_v1"]["counts"][name]["Z"]
        zero, one = to_probs(keys["cal0"]), to_probs(keys["cal1"])
        n = len(next(iter(zero)))
        m = confusion_matrix(zero, one, n)
        dists = [apply_readout_correction(to_probs(keys[k]), m, n) for k in ("s1", "s3", "s5")]
        none = to_probs(res["none"]["counts"][name]["Z"]["s1"])
        answer = o.label[2:-1]
        comps = z_components(dists, answer)
        recombined = (1 + sum(c["exp0"] if math.isfinite(c["exp0"]) else c["z"][0] for c in comps)) / 2 ** n
        vals = [o.value(p) for p in dists]
        f0_free, a_free = free_asymptote(vals)
        bit_err = [[sum(p for b, p in dist.items() if b[::-1][i] != answer[::-1][i]) for i in range(n)]
                   for dist in dists]
        out[name] = {"answer": answer, "vals": vals, "none": o.value(none), "v1": v1_value(o, vals)[0],
                     "components": comps, "component_extrapolation": recombined,
                     "free_asymptote_f0": f0_free, "free_asymptote_a": a_free, "bit_error": bit_err,
                     **decay_numbers([v - o.asymptote for v in vals], o.exact - o.asymptote)}
    return out


# ------------------------------------------------------------------ Part B2: simulation


SIM_SHOTS = 200_000
DETUNING_DRAWS = 16
SIM_CIRCUITS = (DRAPER, CDKM, "W-4", "Toffoli-3")


def sim_models(backend):
    """(label, description, function(base circuit) -> 3 circuits at scales 1/3/5, noise model)."""
    from qiskit.circuit import Delay
    from qiskit.circuit.library import CPhaseGate, RXGate, RZGate, UnitaryGate
    from qiskit.transpiler import PassManager
    from qiskit.transpiler.passes import ALAPScheduleAnalysis, PadDelay
    from qiskit_aer.noise import NoiseModel, RelaxationNoisePass

    from folding import fold

    target = backend.target
    markov = NoiseModel.from_backend(backend, readout_error=False)
    schedule = PassManager([ALAPScheduleAnalysis(target=target), PadDelay(target=target)])
    t1 = [backend.qubit_properties(q).t1 for q in range(backend.num_qubits)]
    t2 = [min(backend.qubit_properties(q).t2, 2 * t1[q]) for q in range(backend.num_qubits)]
    relax = PassManager([RelaxationNoisePass(t1s=t1, t2s=t2, dt=backend.dt, op_types=Delay)])

    def after(circuit, gate_name, matrix_for):
        out = circuit.copy_empty_like()
        for ins in circuit.data:
            out.append(ins)
            if ins.operation.name == gate_name:
                for qubits, matrix in matrix_for(ins.qubits):
                    out.append(UnitaryGate(matrix, label="coherent"), qubits)
        return out

    def plain(base):
        return [[fold(base, s) for s in (1, 3, 5)]]

    def idle(base):
        return [[relax.run(schedule.run(fold(base, s))) for s in (1, 3, 5)]]

    def coherent(gate_name, matrix_for):
        return lambda base: [[after(fold(base, s), gate_name, matrix_for) for s in (1, 3, 5)]]

    def detuned(sigma_hz):
        def build(base):
            scheduled = [schedule.run(fold(base, s)) for s in (1, 3, 5)]
            active = sorted({scheduled[0].find_bit(q).index for ins in scheduled[0].data for q in ins.qubits})
            rng = np.random.default_rng(SEED)
            draws = []
            for _ in range(DETUNING_DRAWS):
                omega = {q: 2 * math.pi * sigma_hz * rng.normal() for q in active}
                draws.append([relax.run(_with_detuning(c, omega, target, backend.dt, RZGate, UnitaryGate))
                              for c in scheduled])
            return draws
        return build

    rx = lambda eps: lambda qubits: [(qubits, RXGate(eps).to_matrix())]  # noqa: E731
    cp = lambda phi: lambda qubits: [(qubits, CPhaseGate(phi).to_matrix())]  # noqa: E731
    lz = lambda phi: lambda qubits: [([q], RZGate(phi).to_matrix()) for q in qubits]  # noqa: E731
    return [
        ("Markovian", "FakeMarrakesh gate errors + T1/T2 during gates (the standard Aer model)", plain, markov),
        ("Markovian + idle", "as above, plus T1/T2 on every idle period (circuits scheduled ALAP)", idle, markov),
        ("+ idle + slow detuning 10 kHz", "plus a random static frequency offset per qubit (σ = 10 kHz, "
         f"{DETUNING_DRAWS} draws averaged): low-frequency dephasing", detuned(10e3), markov),
        ("+ idle + slow detuning 25 kHz", "same, σ = 25 kHz", detuned(25e3), markov),
        ("+ sx over-rotation 0.05", "Markovian plus a coherent RX(0.05) after every physical sx pulse: "
         "cancels inside each folded sx·sx†·sx", coherent("sx", rx(0.05)), markov),
        ("+ sx over-rotation 0.10", "same, RX(0.10)", coherent("sx", rx(0.10)), markov),
        ("+ CZ phase error 0.05", "Markovian plus a coherent CPhase(0.05) after every CZ: adds up inside each "
         "folded CZ·CZ·CZ", coherent("cz", cp(0.05)), markov),
        ("+ CZ local-Z error 0.05", "Markovian plus RZ(0.05) on both qubits after every CZ: adds up inside folds",
         coherent("cz", lz(0.05)), markov),
    ]


def _with_detuning(circuit, omega, target, dt, RZGate, UnitaryGate):
    """After every gate or delay, rotate each qubit by omega[q] x duration (a static frequency offset)."""
    out = circuit.copy_empty_like()
    for ins in circuit.data:
        out.append(ins)
        name = ins.operation.name
        if name in ("measure", "barrier", "rz"):
            continue
        qubits = [circuit.find_bit(q).index for q in ins.qubits]
        if name == "delay":
            seconds = ins.operation.duration * (dt if ins.operation.unit == "dt" else 1)
        else:
            seconds = target[name][tuple(qubits)].duration
        for qb, q in zip(ins.qubits, qubits):
            out.append(UnitaryGate(RZGate(omega[q] * seconds).to_matrix(), label="detuning"), [qb])
    return out


def simulate(by_name: dict) -> list[dict]:
    from qiskit_aer import AerSimulator
    from qiskit_ibm_runtime import fake_provider

    from baseline import compile_best_of_seeds
    from mitigation import OPT_LEVEL, TRANSPILE_SEEDS

    backend = fake_provider.FakeMarrakesh()
    models = sim_models(backend)
    rows = []
    for name in SIM_CIRCUITS:
        (o,) = by_name[name].observables
        (logical,) = by_name[name].circuits.values()
        best = compile_best_of_seeds(logical, backend, OPT_LEVEL, TRANSPILE_SEEDS)[0]
        answer = o.label[2:-1] if o.label.startswith("P(") and set(o.label[2:-1]) <= {"0", "1"} else None
        for label, description, build, noise in models:
            start = time.perf_counter()
            sim = AerSimulator(method="density_matrix", noise_model=noise)
            draws = build(best.circuit)
            shots = SIM_SHOTS // len(draws)
            vals, bit_err = np.zeros(3), None
            for i, circuits in enumerate(draws):
                result = sim.run(circuits, shots=shots, seed_simulator=SEED + i).result()
                probs = [{k: v / shots for k, v in result.get_counts(j).items()} for j in range(3)]
                vals += [o.value(p) for p in probs]
                if answer:
                    errs = np.array([sum(p for b, p in probs[0].items() if b[::-1][q] != answer[::-1][q])
                                     for q in range(len(answer))])
                    bit_err = errs if bit_err is None else bit_err + errs
            vals = list(vals / len(draws))
            v1, branch, exp_raw = v1_value(o, vals)
            rows.append({"circuit": name, "model": label, "description": description, "seed": best.seed,
                         "ops": dict(best.circuit.count_ops()), "vals": vals, "v1": v1, "branch": branch, "exp_raw": exp_raw,
                         "e": abs(v1 - o.exact) / (o.high - o.low),
                         "bit_error_s1": None if bit_err is None else list(bit_err / len(draws)),
                         **decay_numbers([v - o.asymptote for v in vals], o.exact - o.asymptote)})
            print(f"Part B2: {name:15} {label:32} v1 {v1:.3f} kappa {fmt(rows[-1]['kappa'])} "
                  f"shape {fmt(rows[-1]['shape'])} ({time.perf_counter() - start:.0f} s)")
    return rows


# ------------------------------------------------------------------ report


def write_report(path: Path, run_id: str, records: list[dict], bins, rho, hw: dict, sim: list[dict] | None,
                 hashes: dict) -> None:
    L = ["# When does recipe v1 fail, and why did Draper under-correct? (0 RU)", "",
         f"Run `{run_id}`. Saved hardware counts and local simulation only; no IBM calls.", "",
         "> **EXPLORATORY, POST HOC.** Asked for after hardware work ended. It re-reads rounds that are already "
         "reported and tests no pre-registered target. Thresholds below are descriptive, not tuned rules.", "",
         "Files: " + ", ".join(f"`{n}` SHA-256 `{h[:16]}…`" for n, h in hashes.items()), "",
         "Notation (sign-normalised so the noise-free d is positive): d(s) = readout-corrected value at fold "
         "scale s minus the fully mixed value; D0 = exact minus fully mixed. "
         "**r** = ln(d1/d3)/2, the decay per unit of fold scale (computable without the answer). "
         "**κ** = ln(D0/d1)/r, how much the base circuit loses in units of r; v1 assumes κ = 1. "
         "**shape** = ln(d5/d3)/ln(d3/d1), 1 for one clean exponential. "
         "**λ3, λ5** = ln(D0/d(s))/ln(D0/d1), the noise amplification the scale-3 and scale-5 circuits really "
         "achieved (v1 assumes 3 and 5). κ and λ use the exact answer, so they explain errors after the fact.", ""]

    # Part A
    L += ["## A. Every hardware record: what kind of failure", "",
          f"{len(records)} observable × round records from {len({(r['group'], r['circuit']) for r in records})} "
          "cases (5 rounds). e = |v1 − exact| / range width; signed < 0 means v1 is below the answer "
          "(under-corrected).", "",
          "| Mode | Records | e > 0.10 | 0.04 < e ≤ 0.10 | Cases with e > 0.04 |", "|---|---|---|---|---|"]
    modes = sorted({r["mode"] for r in records})
    for m in modes:
        sel = [r for r in records if r["mode"] == m]
        bad = sorted({f"{r['circuit']} {r['observable']} ({r['round']})" for r in sel if r["e"] > 0.04})
        L.append(f"| {m} | {len(sel)} | {sum(r['e'] > 0.10 for r in sel)} | "
                 f"{sum(0.04 < r['e'] <= 0.10 for r in sel)} | {', '.join(bad) or '–'} |")
    L += ["", "Modes: M0 |D0| < 0.1 × width. M1 v1 used its linear branch (d not same-sign and decreasing). "
          "M2 the exponential fit landed outside the physical range and v1's guard silently used the linear fit "
          "instead. M3/M4 exponential branch with a usable decay, split by the "
          "sign of the error: below the answer means the folds amplified the noise less than v1 assumed (κ > 1), "
          "above means more (κ < 1).", "",
          "### A.1 Every record", "",
          "| Round | Circuit | Obs | D0 | d(1) / d(3) / d(5) | kept at s=1 | r ± SE | κ ± SE | shape | λ3 / λ5 | "
          "v1 (branch) | exact | signed err | Mode |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in records:
        L.append(f"| {r['group']} {r['round']} | {r['circuit']} | {r['observable']} | {r['d0']:.3f} | "
                 f"{' / '.join(f'{x:+.3f}' for x in r['dn'])} | {fmt(r['keep1'])} | "
                 f"{fmt(r['r'], 3)} ± {fmt(r['se_r'], 3)} | {fmt(r['kappa'])} ± {fmt(r['se_kappa'])} | "
                 f"{fmt(r['shape'])} | {fmt(r['lambda3'])} / {fmt(r['lambda5'])} | {r['v1']:+.3f} ({r['branch']}) | "
                 f"{r['exact']:+.3f} | {r['signed']:+.3f} | {r['mode'][:2]} |")
    fb = [r for r in records if r["branch"] == "exp→linear"]
    L += ["", "### A.2 The guard's switch to linear (mode M2)", "",
          "Post hoc what-if, not a recipe change: the same exponential fit clipped to the physical range "
          "instead of replaced by the linear fit.", "",
          "| Round | Circuit | Obs | Exp. fit | Linear (what v1 reported) | Exp. clipped | Exact | e v1 | e clipped |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in fb:
        L.append(f"| {r['group']} {r['round']} | {r['circuit']} | {r['observable']} | {r['exp_raw']:+.3f} | "
                 f"{r['v1']:+.3f} | {r['clipped']:+.3f} | "
                 f"{r['exact']:+.3f} | {r['e']:.3f} | {r['e_if_clipped']:.3f} |")
    L += ["", "### A.3 A warning sign you can see without the answer: r", "",
          f"Records where v1 took its exponential branch, including M2 (n = {rho['n']}). "
          "Spearman correlation of r with the relative error "
          f"|v1 − exact| / D0: **{rho['spearman']:.2f}** (p = {rho['p']:.1g}; records are not independent: QFT-6 "
          "contributes 20 observables from 2 rounds).", "",
          "| r (decay per unit scale) | Records | Median e | Max e | e > 0.04 | e > 0.10 | Worst |",
          "|---|---|---|---|---|---|---|"]
    for b in bins:
        hi = "∞" if not math.isfinite(b["hi"]) else f"{b['hi']:.1f}"
        L.append(f"| {b['lo']:.1f} – {hi} | {b['n']} | {fmt(b['median_e'], 3)} | {fmt(b['max_e'], 3)} | "
                 f"{b['over_004']} | {b['over_010']} | {b['worst']} |")
    kap = [r["kappa"] for r in records if r["branch"].startswith("exp") and math.isfinite(r["kappa"])]
    L += ["", f"κ over the same records: median {np.median(kap):.2f}, interquartile range "
          f"{np.percentile(kap, 25):.2f} – {np.percentile(kap, 75):.2f}. Because the error is about "
          "1 − exp(−(κ − 1) r), the same κ spread hurts little when r is small and a lot when r is large.", ""]

    # Part B1
    d = hw[DRAPER]
    c = hw[CDKM]
    L += ["## B. Why Draper-adder-4 under-corrected (0.805 vs 1.0)", "",
          "### B.1 What the hardware counts rule out", "",
          "Draper and CDKM ran in the same round (26 Nov 22:57, `ibm_marrakesh`), both with 70 CZ.", "",
          "| | Draper-adder-4 | CDKM-adder-3 |", "|---|---|---|",
          f"| Readout-corrected P at scales 1 / 3 / 5 | {' / '.join(f'{x:.3f}' for x in d['vals'])} | "
          f"{' / '.join(f'{x:.3f}' for x in c['vals'])} |",
          f"| No mitigation (the round's `none` job) | {d['none']:.3f} | {c['none']:.3f} |",
          f"| Recipe v1 | **{d['v1']:.3f}** | {c['v1']:.3f} |",
          f"| shape (1 = clean exponential) | {fmt(d['shape'])} | {fmt(c['shape'])} |",
          f"| Free-asymptote fit a + B·q^s: f(0) (asymptote a) | {fmt(d['free_asymptote_f0'], 3)} "
          f"({fmt(d['free_asymptote_a'], 3)}) | {fmt(c['free_asymptote_f0'], 3)} ({fmt(c['free_asymptote_a'], 3)}) |",
          f"| Each Z-string component extrapolated alone, then recombined | {d['component_extrapolation']:.3f} | "
          f"{c['component_extrapolation']:.3f} |",
          f"| r per unit scale | {fmt(d['r'], 3)} | {fmt(c['r'], 3)} |",
          f"| κ (base-circuit loss / fold loss per unit) | **{fmt(d['kappa'])}** | {fmt(c['kappa'])} |",
          f"| Effective amplification of scale 3 / scale 5 (assumed 3 / 5) | **{fmt(d['lambda3'])} / "
          f"{fmt(d['lambda5'])}** | {fmt(c['lambda3'])} / {fmt(c['lambda5'])} |", "",
          "Per Z-string component (Draper; z = sign-normalised ⟨Z_S⟩, 1 when noise-free):", "",
          "| Bits S | Weight | z(1) / z(3) / z(5) | shape | κ | Exp. extrapolation to s = 0 |", "|---|---|---|---|---|---|"]
    for comp in d["components"]:
        L.append(f"| {comp['bits']} | {comp['weight']} | {' / '.join(f'{x:.3f}' for x in comp['z'])} | "
                 f"{fmt(comp['shape'])} | {fmt(comp['kappa'])} | {fmt(comp['exp0'], 3)} |")
    L += ["", "Error rate per measured bit (readout-corrected; clbit 0 = least significant bit of the sum):", "",
          "| Scale | " + " | ".join(f"clbit {i}" for i in range(len(d["answer"]))) + " |",
          "|---|" + "---|" * len(d["answer"])]
    for s, row in zip((1, 3, 5), d["bit_error"]):
        L.append(f"| {s} | " + " | ".join(f"{x:.3f}" for x in row) + " |")

    # Part B2
    if sim:
        L += ["", "### B.2 Which kind of noise produces this signature (simulation, FakeMarrakesh)", "",
              "Same compilation as the hardware round (level 2, best of 20 seeds on FakeMarrakesh; the hardware "
              "layout was not saved, so the qubits may differ). Readout errors off (v1 corrects them). "
              f"{SIM_SHOTS} shots per circuit, density-matrix simulator.", ""]
        for name in SIM_CIRCUITS:
            rows = [r for r in sim if r["circuit"] == name]
            L += [f"**{name}** ({', '.join(f'{k} {v}' for k, v in rows[0]['ops'].items() if k != 'measure')})", "",
                  "| Noise model | P at 1 / 3 / 5 | v1 (branch) | Exp. fit | κ | shape | λ3 / λ5 |",
                  "|---|---|---|---|---|---|---|"]
            for r in rows:
                L.append(f"| {r['model']} | {' / '.join(f'{x:.3f}' for x in r['vals'])} | {r['v1']:.3f} "
                         f"({r['branch']}) | {fmt(r['exp_raw'], 3)} | {fmt(r['kappa'])} | {fmt(r['shape'])} | "
                         f"{fmt(r['lambda3'])} / {fmt(r['lambda5'])} |")
            L.append("")
        L += ["Noise models:", ""] + [f"- **{r['model']}**: {r['description']}" for r in sim
                                      if r["circuit"] == SIM_CIRCUITS[0]]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-sim", action="store_true", help="skip the simulation part (B2)")
    args = parser.parse_args()
    hashes = {n: sha(HERE / n) for n in ("failure_analysis.py", "recipe.py", "folding.py")}
    run_dir = runlog.new_run("failure-analysis", config={
        "rounds": [{"case_group": g, "round": lab, "run": run, "v1_key": key} for g, lab, run, key in ROUNDS],
        "bootstrap": BOOTSTRAP, "seed": SEED, "no_signal": NO_SIGNAL, "r_bins": list(R_BINS[:-1]),
        "simulation": None if args.no_sim else {"backend": "FakeMarrakesh", "shots": SIM_SHOTS,
                                                 "detuning_draws": DETUNING_DRAWS, "circuits": list(SIM_CIRCUITS)},
        "file_sha256": hashes, "qpu": "none (saved data and local simulation only)"}, method=[
        "Exploratory, post hoc: classify every saved v1 hardware record by failure mode; decay rate r, kappa, "
        "shape and effective fold amplification per record.",
        "Draper-adder-4 deep dive on its saved counts: free-asymptote fit, per-Z-string extrapolation, bit errors.",
        "Simulation on FakeMarrakesh of the four v1.2 circuits under Markovian, idle, slow-detuning and coherent "
        "noise, to see which noise reproduces the hardware signature."])
    by_name = all_tasks()
    records = hardware_records(by_name)
    bins, rho = r_bins(records)
    hw = draper_hardware(by_name)
    sim = None if args.no_sim else simulate(by_name)
    runlog.write_json(run_dir / "summary.json", {"records": records, "r_bins": bins, "r_vs_error": rho,
                                                 "draper_hardware": hw, "simulation": sim})
    report = run_dir / "failure_analysis.md"
    write_report(report, run_dir.name, records, bins, rho, hw, sim, hashes)
    print(f"Report: {report}")


if __name__ == "__main__":
    main()
