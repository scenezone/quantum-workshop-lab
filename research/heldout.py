"""Held-out circuits: the test set for the pre-registered targets (PREREGISTRATION.md).

Defined on 23 Nov 2026, before any of them was simulated. They were not used to design the
mitigation recipe; the recipe is designed only on the training circuits in baseline.py.
They are deeper than the training set and include two families the training set does not have
(Trotterized Ising dynamics and mirror circuits).
"""

from __future__ import annotations

import math

import numpy as np
from qiskit import QuantumCircuit

from baseline import Benchmark, grover, qaoa_maxcut

RING5 = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)]
# Triangular prism: two triangles joined by three rungs (3-regular, 6 nodes, 9 edges).
PRISM6 = [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3), (0, 3), (1, 4), (2, 5)]
MIRROR_SEED = 2026


def ising_trotter(n: int = 4, steps: int = 6, j: float = 1.0, h: float = 1.0, dt: float = 0.3) -> Benchmark:
    """Transverse-field Ising chain, first-order Trotter steps from |0...0>."""
    qc = QuantumCircuit(n)
    for _ in range(steps):
        for q in range(n - 1):
            qc.rzz(2 * j * dt, q, q + 1)
        qc.rx(2 * h * dt, range(n))
    return Benchmark(f"Ising-{n}", qc, list(range(n)), f"TFIM chain, {steps} Trotter steps, dt={dt}, J=h=1")


def mirror(n: int = 4, layers: int = 4, seed: int = MIRROR_SEED) -> Benchmark:
    """Random brickwork of U and CZ layers, then its exact inverse. Ideal output is |0...0>.

    A barrier separates the halves so the transpiler cannot cancel them against each other.
    """
    rng = np.random.default_rng(seed)
    forward = QuantumCircuit(n)
    for layer in range(layers):
        for q in range(n):
            theta, phi, lam = rng.uniform(0, 2 * math.pi, 3)
            forward.u(theta, phi, lam, q)
        start = layer % 2
        for q in range(start, n - 1, 2):
            forward.cz(q, q + 1)
    qc = forward.copy()
    qc.barrier()
    qc.compose(forward.inverse(), inplace=True)
    return Benchmark(f"Mirror-{n}", qc, list(range(n)), f"{layers} random U+CZ layers then inverse, seed {seed}")


def heldout_benchmarks() -> list[Benchmark]:
    """Counts-style circuits of the held-out set (QFT-6 is built in mitigation.py as an X/Y task)."""
    g = grover(4, "0110", iterations=3)
    g.name = "Grover-4-3it"  # distinct from the training Grover-4 (marked 1011, 2 iterations)
    return [
        ising_trotter(),
        mirror(),
        g,
        qaoa_maxcut(5, RING5, "MaxCut 5-ring", p=2),
        qaoa_maxcut(6, PRISM6, "MaxCut prism", p=1),
    ]


HELDOUT_NAMES = ("Ising-4", "Mirror-4", "Grover-4-3it", "QFT-6", "QAOA-5-p2", "QAOA-6")
