"""Recipe v2 building blocks: two-qubit partial folding (small scale factors) and Pauli twirling of CZ gates.

Both act on already-transpiled (ISA) circuits for CZ devices (Heron) and never re-route or re-optimize two-qubit
gates, so inserted CZ pairs are never cancelled.

fold_2q(circuit, scale)
    Folds two-qubit gates only (CZ -> CZ (CZ CZ)^k; single-qubit gates are not folded, as in IBM's gate-folding
    ZNE). To reach a non-odd scale such as 1.5, an evenly spaced subset of the CZ gates is folded once:
    F = round((scale - 1) / 2 * n) extra folds for n CZ gates, so the ACTUAL scale is 1 + 2F/n. The actual
    scale is returned and used in the extrapolation, not the nominal one.

twirl(circuit, rng)
    For every CZ, a random two-qubit Pauli B is inserted before it and A = CZ B CZ after it, so A CZ B = CZ up to
    a global phase: the circuit's operator is unchanged, but averaged over random instances the noise of each
    CZ becomes a Pauli (stochastic) channel. Coherent errors stop adding up coherently, which is what zero-noise
    extrapolation assumes. Paulis are written as x (X) and rz(pi) (Z); afterwards consecutive single-qubit
    gates are merged (Optimize1qGatesDecomposition on rz/sx/x), which touches no two-qubit gate.

Order used by recipe v2: fold_2q, then twirl (every CZ, including folded copies, gets its own Paulis), then merge.

    .venv/Scripts/python twirl.py      # self-checks + coherent-noise demonstration
"""

from __future__ import annotations

import math

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import RZGate, XGate
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import Optimize1qGatesDecomposition

TWO_QUBIT = "cz"
ONE_QUBIT_BASIS = ["rz", "sx", "x"]
_MERGE = PassManager([Optimize1qGatesDecomposition(basis=ONE_QUBIT_BASIS)])


def _is_2q(instruction) -> bool:
    return instruction.operation.num_qubits == 2 and instruction.operation.name != "barrier"


def two_qubit_count(circuit: QuantumCircuit) -> int:
    return sum(1 for i in circuit.data if _is_2q(i))


def _extra_folds(scale: float, n: int) -> int:
    return math.floor((scale - 1) / 2 * n + 0.5)  # round half up (Python's round() rounds 0.5 to 0)


def fold_2q(circuit: QuantumCircuit, scale: float, extra: int | None = None) -> tuple[QuantumCircuit, float]:
    """Fold CZ gates so the CZ count is about `scale` times the original. Returns (circuit, actual scale).

    `extra` (number of extra CZ folds) overrides `scale` when given; see fold_2q_series."""
    if scale < 1:
        raise ValueError("scale must be >= 1")
    gates = [i for i in circuit.data if _is_2q(i)]
    for g in gates:
        if g.operation.name != TWO_QUBIT:
            raise ValueError(f"fold_2q supports {TWO_QUBIT} only, found {g.operation.name}")
    n = len(gates)
    if n == 0:
        return circuit.copy(), 1.0
    if extra is None:
        extra = _extra_folds(scale, n)
    base, rest = divmod(extra, n)
    folded = circuit.copy_empty_like()
    index = 0
    for instruction in circuit.data:
        folded.append(instruction)
        if not _is_2q(instruction):
            continue
        # evenly spaced: gate i gets one extra fold if floor((i+1) r / n) > floor(i r / n)
        folds = base + (((index + 1) * rest) // n > (index * rest) // n)
        for _ in range(2 * folds):
            folded.append(instruction)  # CZ is self-inverse: CZ (CZ CZ)^k
        index += 1
    return folded, 1 + 2 * extra / n


def fold_2q_series(circuit: QuantumCircuit, scales) -> list[tuple[QuantumCircuit, float]]:
    """fold_2q at each nominal scale (ascending), with STRICTLY increasing actual scales.

    With few CZ gates, nominal scales such as 1.5 and 2 can round to the same number of folds (with one CZ
    both round to 1.0, so a fit through them is meaningless). Each step therefore folds at least one more CZ
    than the previous one; for a 1-CZ circuit the actual scales become 1, 3, 5.
    """
    n = two_qubit_count(circuit)
    out, previous = [], None
    for s in scales:
        extra = _extra_folds(s, n)
        if previous is not None and n > 0:
            extra = max(extra, previous + 1)
        out.append(fold_2q(circuit, s, extra))
        previous = extra
    return out


def _pauli_ops(x: int, z: int) -> list:
    """Native gates for the Pauli X^x Z^z (applied Z first, then X; equal to the Pauli up to phase)."""
    return ([RZGate(math.pi)] if z else []) + ([XGate()] if x else [])


def twirl(circuit: QuantumCircuit, rng: np.random.Generator, merge: bool = True) -> QuantumCircuit:
    """One random Pauli-twirled instance of an ISA circuit (every CZ twirled independently)."""
    out = circuit.copy_empty_like()
    for instruction in circuit.data:
        if not _is_2q(instruction):
            out.append(instruction)
            continue
        if instruction.operation.name != TWO_QUBIT:
            raise ValueError(f"twirl supports {TWO_QUBIT} only, found {instruction.operation.name}")
        a, b = instruction.qubits
        xa, za, xb, zb = (int(v) for v in rng.integers(0, 2, 4))
        for op in _pauli_ops(xa, za):
            out.append(op, [a])
        for op in _pauli_ops(xb, zb):
            out.append(op, [b])
        out.append(instruction)
        # CZ (X_a) CZ = X_a Z_b, CZ (Z_a) CZ = Z_a, and symmetrically for b.
        for op in _pauli_ops(xa, za ^ xb):
            out.append(op, [a])
        for op in _pauli_ops(xb, zb ^ xa):
            out.append(op, [b])
    return _MERGE.run(out) if merge else out


def prepare(circuit: QuantumCircuit, scale: float, instances: int, seed: int) -> tuple[list[QuantumCircuit], float]:
    """`instances` twirled copies of the circuit folded to `scale`, plus the actual scale."""
    folded, actual = fold_2q(circuit, scale)
    rng = np.random.default_rng(seed)
    return [twirl(folded, rng) for _ in range(instances)], actual


# ------------------------------------------------------------------ self-checks


def _self_check() -> None:
    from qiskit import transpile
    from qiskit.quantum_info import Operator

    qc = QuantumCircuit(3)
    qc.h(0)
    qc.cx(0, 1)
    qc.ry(0.7, 2)
    qc.cz(1, 2)
    qc.sx(1)
    qc.t(0)
    qc.cx(2, 0)
    qc.rzz(0.4, 0, 1)
    native = transpile(qc, basis_gates=["cz", "sx", "x", "rz"], optimization_level=0)
    n = two_qubit_count(native)
    for scale in (1, 1.5, 2, 3, 5):
        folded, actual = fold_2q(native, scale)
        assert Operator(folded).equiv(Operator(native)), scale
        assert two_qubit_count(folded) == round(actual * n), (scale, actual)
        assert abs(actual - scale) <= 1 / n + 1e-9, (scale, actual)
    rng = np.random.default_rng(1)
    for _ in range(25):
        for scale in (1, 2):
            folded, _ = fold_2q(native, scale)
            t = twirl(folded, rng)
            assert Operator(t).equiv(Operator(native)), "twirled instance changed the operator"
            assert two_qubit_count(t) == two_qubit_count(folded)
    one_cz = transpile(QuantumCircuit(2).compose(QuantumCircuit(2)), basis_gates=["cz"], optimization_level=0)
    one_cz.cz(0, 1)
    series = [a for _, a in fold_2q_series(one_cz, (1, 1.5, 2))]
    assert series == [1.0, 3.0, 5.0], series
    for circuit in (native, one_cz):
        actual = [a for _, a in fold_2q_series(circuit, (1, 1.5, 2))]
        assert all(x < y for x, y in zip(actual, actual[1:])), actual
    print(f"fold_2q: equivalent at scales 1/1.5/2/3/5, CZ count = actual scale x {n}; "
          f"series strictly increasing ({n} CZ: {[round(a, 2) for _, a in fold_2q_series(native, (1, 1.5, 2))]}, "
          f"1 CZ: {series})")
    print("twirl: 50 random instances equivalent to the original; CZ count unchanged")


def _coherent_demo() -> None:
    """Why twirl: a coherent ZZ over-rotation after every CZ, exact density-matrix simulation (no shot noise)."""
    from qiskit import transpile
    from qiskit.circuit.library import RZZGate
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, coherent_unitary_error, depolarizing_error

    theta = 0.12
    noise = NoiseModel()
    noise.add_all_qubit_quantum_error(
        coherent_unitary_error(RZZGate(theta).to_matrix()).compose(depolarizing_error(0.01, 2)), ["cz"])
    sim = AerSimulator(method="density_matrix", noise_model=noise)

    qc = QuantumCircuit(3)
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 2)
    for _ in range(3):  # a deeper GHZ-like circuit: uncompute and recompute
        qc.cx(1, 2)
        qc.cx(0, 1)
        qc.cx(0, 1)
        qc.cx(1, 2)
    qc.h(range(3))
    qc.measure_all()
    native = transpile(qc, basis_gates=["cz", "sx", "x", "rz"], optimization_level=0)
    exact = 1.0  # X-parity of GHZ-3

    def build(scale: float, twirled: bool) -> tuple[list[QuantumCircuit], float]:
        if twirled:
            return prepare(native.remove_final_measurements(inplace=False), scale, 32, seed=11)
        folded, actual = fold_2q(native.remove_final_measurements(inplace=False), scale)
        return [folded], actual

    print(f"\nCoherent-noise demo: RZZ({theta}) over-rotation + 1% depolarizing after every CZ, GHZ-3 X-parity "
          f"(exact {exact}), {two_qubit_count(native)} CZ")
    for twirled in (False, True):
        xs, vs = [], []
        for scale in (1, 1.5, 2, 3):
            circuits, actual = build(scale, twirled)
            measured = []
            for c in circuits:
                c = c.copy()
                c.save_probabilities_dict(qubits=[0, 1, 2], label="p")
                measured.append(c)
            vals = []
            for c in measured:
                probs = sim.run(c).result().data()["p"]
                vals.append(sum(p * (-1) ** bin(int(k)).count("1") for k, p in probs.items()))
            xs.append(actual)
            vs.append(float(np.mean(vals)))
        lin = np.polyfit(xs[:3], vs[:3], 1)[1]
        print(f"  {'twirled  ' if twirled else 'untwirled'} values at scales {[round(x, 2) for x in xs]}: "
              f"{[round(v, 3) for v in vs]}; linear(1,1.5,2) -> {lin:.3f} (error {abs(lin - exact):.3f})")


if __name__ == "__main__":
    _self_check()
    _coherent_demo()
