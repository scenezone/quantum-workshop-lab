"""Recipe v1.2 = recipe v1 (recipe.py, unchanged) + rules "decay" and "alive" of recipe_v1_1.py (PREREGISTRATION.md
Part H). Rule "one_exp" is dropped; nothing else changes (same code, same k = 2, same bootstrap SEs).

POST HOC: the choice to drop "one_exp" was made on 26 Nov 2026 after the v1.1 design replay
(`20261126-223700_v1-1-design-replay`), where it flagged 3 of 8 good cases on ibm_marrakesh. So the replay is
design data for v1.2 and cannot count as evidence; only the Part H round on new circuits can.

If decay or alive fails, v1.2 reports the scale-1 readout-corrected value (no extrapolation, no clipping) with a
flag naming the failed rules. If both pass, v1.2 reports exactly what recipe v1 reports.
"""
from __future__ import annotations

import numpy as np

import recipe
import recipe_v1_1
from mitigation import extrapolate

VERSION = "v1.2"
K = recipe_v1_1.K  # 2.0
RULES = ("decay", "alive")


def estimate(obs, scaled: list[float], boot_scaled: np.ndarray, k: float = K) -> tuple[float, str, list[str]]:
    """(value, branch, failed rules). scaled = readout-corrected values at scales 1/3/5; boot_scaled = replicas."""
    d = [v - obs.asymptote for v in scaled]
    boot_d = np.asarray(boot_scaled, dtype=float) - obs.asymptote
    result = recipe_v1_1.checks(d, boot_d, k)
    failed = [r for r in RULES if not result[r]]
    if failed:
        return scaled[0], "flag:" + "+".join(failed), failed
    est = {f"readout_zne_{f}": extrapolate(f, scaled, obs)[0] for f in ("linear", "expg")}
    value, branch = recipe.estimate({}, obs, est, scaled)
    return value, branch, []
