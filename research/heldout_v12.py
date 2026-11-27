"""New circuits for the recipe v1.2 hardware round (PREREGISTRATION.md Part H).

Chosen on 26 Nov 2026 from exact (noise-free) values and compiled two-qubit counts on FakeMarrakesh (level 2, best
of 20 seeds) ONLY. No candidate was simulated with noise or run on hardware before Part H was written. None of
these families appears in any earlier run (simulator or hardware). Each circuit has one observable, the
probability of the ideal answer (exact 1), far from its fully mixed value.

  shallow (expected good)
    W-4             W state on 4 qubits (RY + CRY/CX cascade); P(exactly one excitation); fully mixed 0.25; 6 CZ
    Toffoli-3       X on q0, q1, then CCX(q0, q1, q2); P(111); fully mixed 0.125; 7 CZ
  deep (~60+ CZ, expected failure-prone)
    CDKM-adder-3    Cuccaro ripple-carry full adder (qiskit CDKMRippleCarryAdder), a = 5, b = 6, carry-in 0;
                    measured: sum register b and carry-out, answer 11 = 1011; fully mixed 0.0625; 70 CZ
    Draper-adder-4  QFT adder (qiskit DraperQFTAdder, kind "fixed"), a = 11, b = 7, sum mod 16 = 2 in register b;
                    answer 0010; fully mixed 0.0625; 70 CZ
"""
from __future__ import annotations

import math

from qiskit import QuantumCircuit
from qiskit.circuit.library import CDKMRippleCarryAdder, DraperQFTAdder

from baseline import Benchmark
from mitigation import Task, _single, exact_distribution, probability

NAMES = ("W-4", "Toffoli-3", "CDKM-adder-3", "Draper-adder-4")
SHALLOW = ("W-4", "Toffoli-3")
DEEP = ("CDKM-adder-3", "Draper-adder-4")


def _load(qc: QuantumCircuit, qubits, value: int) -> None:
    for i, q in enumerate(qubits):
        if value >> i & 1:
            qc.x(q)


def w_state(n: int = 4) -> Benchmark:
    qc = QuantumCircuit(n)
    qc.x(0)
    for i in range(n - 1):
        qc.cry(2 * math.acos(math.sqrt(1 / (n - i))), i, i + 1)
        qc.cx(i + 1, i)
    return Benchmark(f"W-{n}", qc, list(range(n)), f"W state on {n} qubits")


def toffoli() -> Benchmark:
    qc = QuantumCircuit(3)
    qc.x([0, 1])
    qc.ccx(0, 1, 2)
    return Benchmark("Toffoli-3", qc, [0, 1, 2], "CCX with both controls 1")


def cdkm_adder(n: int = 3, a: int = 5, b: int = 6) -> Benchmark:
    add = CDKMRippleCarryAdder(n, kind="full")  # qubits: carry-in, a (n), b (n), carry-out
    qc = QuantumCircuit(add.num_qubits)
    _load(qc, range(1, 1 + n), a)
    _load(qc, range(1 + n, 1 + 2 * n), b)
    qc.compose(add, inplace=True)
    return Benchmark(f"CDKM-adder-{n}", qc.decompose(reps=3), list(range(1 + n, 2 + 2 * n)),
                     f"Cuccaro adder {a} + {b}, measured sum register and carry-out")


def draper_adder(n: int = 4, a: int = 11, b: int = 7) -> Benchmark:
    add = DraperQFTAdder(n, kind="fixed")  # qubits: a (n), b (n); b <- a + b mod 2^n
    qc = QuantumCircuit(add.num_qubits)
    _load(qc, range(n), a)
    _load(qc, range(n, 2 * n), b)
    qc.compose(add, inplace=True)
    return Benchmark(f"Draper-adder-{n}", qc.decompose(reps=3), list(range(n, 2 * n)),
                     f"QFT adder {a} + {b} mod {2 ** n}, measured register b")


def one_excitation(probs: dict[str, float]) -> float:
    return sum(p for k, p in probs.items() if k.count("1") == 1)


def tasks() -> list[Task]:
    out = [_single(w_state(), "Z", "P(1 exc.)", one_excitation, 0.0, 1.0, "P(exactly one excitation)", "v12")]
    for bench in (toffoli(), cdkm_adder(), draper_adder()):
        measured = _single(bench, "Z", "tmp", probability(""), 0.0, 1.0, "", "v12").circuits["Z"]
        dist = exact_distribution(measured)
        answer = max(dist, key=dist.get)
        out.append(_single(bench, "Z", f"P({answer})", probability(answer), 0.0, 1.0, f"P({answer})", "v12"))
    for task in out:
        exact = {b: exact_distribution(qc) for b, qc in task.circuits.items()}
        for obs in task.observables:
            n = len(next(iter(exact[obs.basis])))
            obs.exact = obs.value(exact[obs.basis])
            obs.asymptote = obs.value({format(i, f"0{n}b"): 1 / 2**n for i in range(2**n)})
    return out
