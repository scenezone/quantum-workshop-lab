"""Mitigation recipe v2 (PREREGISTRATION.md Part F). Recipe v1 (recipe.py) is unchanged and still frozen.

Why v2: on ibm_fez (24 Nov 2026, rounds 1 and 2) recipe v1 lost badly to IBM resilience level 2 on deep
circuits. On Grover-4-3it the readout-corrected values at scales 1/3/5 were 0.544 / 0.203 / 0.077 (exact 0.961,
fully mixed 0.062): at scale 5 the signal was gone, the exponential fit left the range and the fallback to
linear returned 0.625. v2 changes exactly three things, agreed with the reviewer on 24 Nov 2026:

  1. Pauli twirling of every CZ (twirl.py), TWIRLS random instances per scale factor, counts pooled.
  2. Smaller scale factors: 1, 1.5, 2, by folding two-qubit gates only (twirl.fold_2q); the ACTUAL scales
     (1 + 2F/n) are used in the fit.
  3. Clipping: the final estimate is clipped to the observable's physical range, instead of falling back to
     linear when the exponential leaves it.

Everything else is v1: readout calibration (20% of shots), readout correction of each scale before
extrapolation, and the same branch rule on measured values only. With d_s = value(s) - asymptote:
exponential (known asymptote) if d has one sign, |d| decreases with scale and |d_1| >= DELTA x range width;
otherwise linear. Then clip.
"""

from __future__ import annotations

import math

from mitiq.zne.inference import ExpFactory, LinearFactory

VERSION = "v2"
FROZEN = False  # set True when Part F is written, before the v2 held-out circuits are simulated
DELTA = 0.1  # same as v1
SCALES = (1.0, 1.5, 2.0)  # nominal; actual scales from twirl.fold_2q_series (strictly increasing)
TWIRLS = 8  # random twirl instances per scale factor (per repeat in the simulator)
CAL_FRACTION = 0.2  # same as v1


def _linear(scales: list[float], values: list[float]) -> float:
    return float(LinearFactory.extrapolate(scales, values))


def _exp(scales: list[float], values: list[float], asymptote: float) -> float:
    try:
        return float(ExpFactory.extrapolate(scales, values, asymptote=asymptote))
    except Exception:
        return float(ExpFactory.extrapolate(scales, values, asymptote=asymptote, avoid_log=True))


def estimate(obs, scales: list[float], values: list[float]) -> tuple[float, str]:
    """(zero-noise estimate, branch) from readout-corrected values at the actual scales (ascending)."""
    d = [v - obs.asymptote for v in values]
    width = obs.high - obs.low
    same_sign = all(x > 0 for x in d) or all(x < 0 for x in d)
    decaying = all(abs(d[i]) > abs(d[i + 1]) for i in range(len(d) - 1))
    far = abs(d[0]) >= DELTA * width
    branch = "linear"
    value = float("nan")
    if same_sign and decaying and far:
        try:
            value, branch = _exp(scales, values, obs.asymptote), "exp"
        except Exception:
            value = float("nan")
    if not math.isfinite(value):
        value, branch = _linear(scales, values), "linear"
    clipped = min(max(value, obs.low), obs.high)
    return clipped, branch + ("+clip" if clipped != value else "")
