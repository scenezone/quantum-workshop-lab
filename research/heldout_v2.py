"""Held-out circuits for recipe v2 (PREREGISTRATION.md Part F).

Defined on 24 Nov 2026, before any of them was simulated with noise or run on hardware. Two families that
no earlier run contains, both deep (more than 12 two-qubit gates after compilation), both with an
informative observable (exact value far from its fully-mixed value):

  Heisenberg-4  XXZ chain (J=1, Delta=0.5), 5 first-order Trotter steps of dt=0.25 from the Neel state
                |1010> (qubits 1, 3 flipped); observable: staggered magnetization (1/4) sum_j (-1)^j <Z_j>  (1 at t=0, 0 if fully mixed)
  QPE-4         phase estimation of U = P(2 pi 11/16) on |1>, 4 counting qubits; observable: P(correct
                4-bit phase), exact 1

Only exact (noise-free) values and compiled gate counts were looked at when choosing the parameters.
Heisenberg: 4 steps gave an exact value of 0.001, equal to the fully-mixed value (uninformative, the Ising-4
problem), so 5 steps (exact -0.646) was chosen from a scan of exact values only.
"""

from __future__ import annotations

import math

from qiskit import QuantumCircuit
from qiskit.circuit.library import QFTGate

from baseline import Benchmark

HEIS_J, HEIS_DELTA, HEIS_DT, HEIS_STEPS = 1.0, 0.5, 0.25, 5
QPE_PHASE_NUM, QPE_BITS = 11, 4  # phase = 11/16


def heisenberg(n: int = 4, steps: int = HEIS_STEPS, dt: float = HEIS_DT,
               j: float = HEIS_J, delta: float = HEIS_DELTA) -> Benchmark:
    qc = QuantumCircuit(n)
    qc.x(range(1, n, 2))  # Neel state: qubits 1 and 3 flipped, |1010> in Qiskit order (qubit 0 rightmost)
    for _ in range(steps):
        for start in (0, 1):  # even bonds, then odd bonds
            for q in range(start, n - 1, 2):
                qc.rxx(2 * j * dt, q, q + 1)
                qc.ryy(2 * j * dt, q, q + 1)
                qc.rzz(2 * j * delta * dt, q, q + 1)
    return Benchmark(f"Heisenberg-{n}", qc, list(range(n)),
                     f"XXZ chain J={j}, Delta={delta}, {steps} Trotter steps dt={dt}, from Neel |1010>")


def qpe(bits: int = QPE_BITS, numerator: int = QPE_PHASE_NUM) -> tuple[Benchmark, str]:
    """QPE with `bits` counting qubits (0..bits-1) and one eigenstate qubit (index bits).

    Returns the benchmark and the ideal counting-register bitstring (Qiskit order, qubit 0 rightmost).
    """
    phase = numerator / 2**bits
    qc = QuantumCircuit(bits + 1)
    qc.x(bits)  # |1> is the eigenstate of P(theta) with eigenvalue e^{i theta}
    qc.h(range(bits))
    for k in range(bits):
        qc.cp(2 * math.pi * phase * 2**k, k, bits)
    qc.append(QFTGate(bits).inverse(), range(bits))
    answer = format(numerator, f"0{bits}b")
    return Benchmark(f"QPE-{bits}", qc, list(range(bits)), f"phase {numerator}/{2**bits}, P({answer})"), answer


HELDOUT_V2_NAMES = ("Heisenberg-4", "QPE-4")
