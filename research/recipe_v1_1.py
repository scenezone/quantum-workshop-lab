"""Recipe v1.1 = recipe v1 (recipe.py, unchanged) + three physics checks that decide when NOT to extrapolate.

Rules fixed on 26 Nov 2026, before the design replay (v1_1_design_replay.py) was run, from physics only; the form
and k were sent to the reviewer before any replay output existed and are not tuned on it.

Notation, per observable: d(s) = readout-corrected value at fold scale s (1, 3, 5) minus the observable's value on
the fully mixed state. SE comes from the bootstrap replicas of the same counts (multinomial resampling of every
PUB, calibration PUBs included), so correlations between scales (shared readout matrix) are carried through.

1. decay      Incoherent noise only moves the signal toward the fully mixed value, never away from it:
              d(1), d(3), d(5) have the same sign, and |d(s_next)| - |d(s)| <= k * SE(|d(s_next)| - |d(s)|)
              for both steps (1->3 and 3->5).
2. alive      If the signal at the largest scale is lost in shot noise, the extrapolation is a guess:
              |d(5)| > k * SE(d(5)).
3. one_exp    Depolarizing / Pauli noise gives a single decay rate, so the two step ratios agree:
              |d(3)/d(1) - d(5)/d(3)| <= k * SE(d(3)/d(1) - d(5)/d(3)), SE over the bootstrap replicas whose
              ratios are finite.

If any rule fails, v1.1 reports the scale-1 readout-corrected value (no extrapolation, no clipping) with a flag
naming the failed rules. If all pass, v1.1 reports exactly what recipe v1 reports.
"""
from __future__ import annotations

import numpy as np

import recipe
from mitigation import extrapolate

VERSION = "v1.1"
K = 2.0
RULES = ("decay", "alive", "one_exp")


def checks(d: list[float], boot_d: np.ndarray, k: float = K) -> dict[str, bool]:
    """{rule: passed} for one observable. d = [d1, d3, d5]; boot_d has shape (replicas, 3)."""
    d = np.asarray(d, dtype=float)
    b = np.asarray(boot_d, dtype=float)
    same_sign = bool(np.all(d > 0) or np.all(d < 0))
    steps_ok = all(
        abs(d[i + 1]) - abs(d[i]) <= k * np.std(np.abs(b[:, i + 1]) - np.abs(b[:, i]), ddof=1) for i in (0, 1))
    alive = abs(d[2]) > k * np.std(b[:, 2], ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        diff = d[1] / d[0] - d[2] / d[1]
        boot_diff = b[:, 1] / b[:, 0] - b[:, 2] / b[:, 1]
    finite = boot_diff[np.isfinite(boot_diff)]
    one_exp = bool(np.isfinite(diff) and len(finite) > 1 and abs(diff) <= k * np.std(finite, ddof=1))
    return {"decay": same_sign and steps_ok, "alive": bool(alive), "one_exp": one_exp}


def estimate(obs, scaled: list[float], boot_scaled: np.ndarray, k: float = K) -> tuple[float, str, list[str]]:
    """(value, branch, failed rules). scaled = readout-corrected values at scales 1/3/5; boot_scaled = replicas."""
    d = [v - obs.asymptote for v in scaled]
    boot_d = np.asarray(boot_scaled, dtype=float) - obs.asymptote
    failed = [r for r, ok in checks(d, boot_d, k).items() if not ok]
    if failed:
        return scaled[0], "flag:" + "+".join(failed), failed
    est = {f"readout_zne_{f}": extrapolate(f, scaled, obs)[0] for f in ("linear", "expg")}
    value, branch = recipe.estimate({}, obs, est, scaled)
    return value, branch, []
