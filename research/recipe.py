"""Mitigation recipe v1 (PREREGISTRATION.md Part B).

Designed on the training circuits only (run 20261123-111818_mitigation-train), then frozen before
the held-out set was simulated. Do not change it after freezing; changes go into a new version
with a new pre-registration entry.

Data: the readout+ZNE data group (calibration shots, then scale factors 1/3/5, all readout-corrected),
so the recipe spends exactly the same budget as every other method.

Per observable, using only measured values (never the exact answer):
  d_s = (readout-corrected value at scale s) - asymptote, where the asymptote is the observable's
  value on the fully mixed state.
  Use guarded exponential extrapolation if the values look like an exponential decay toward the
  asymptote:
    1. d_1, d_3, d_5 all have the same sign,
    2. |d_1| > |d_3| > |d_5|  (decaying toward the asymptote), and
    3. |d_1| >= DELTA x (physical range width)  (far enough from the asymptote to fit a decay).
  Otherwise use linear extrapolation.
  Guarded exponential itself falls back to linear when its result leaves the physical range.
"""

from __future__ import annotations

VERSION = "v1"
FROZEN = True  # frozen 23 Nov 2026, before the held-out run
DELTA = 0.1


def estimate(features: dict, obs, method_estimates: dict[str, float], scaled: list[float]) -> tuple[float, str]:
    """(zero-noise estimate, which branch was used) for one observable in one repeat."""
    d = [v - obs.asymptote for v in scaled]
    width = obs.high - obs.low
    same_sign = all(x > 0 for x in d) or all(x < 0 for x in d)
    decaying = abs(d[0]) > abs(d[1]) > abs(d[2])
    far = abs(d[0]) >= DELTA * width
    if same_sign and decaying and far:
        return method_estimates["readout_zne_expg"], "exp"
    return method_estimates["readout_zne_linear"], "linear"
