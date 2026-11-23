"""Native unitary folding for ZNE, applied to already-transpiled (ISA) circuits.

Each gate G becomes G (G† G)^k with k = (scale - 1) / 2, so scale 1, 3, 5 multiplies every
gate, and therefore the two-qubit gate count, by exactly 1, 3, 5. Inverses are written in
native gates so the folded circuit runs without re-transpiling. Never re-optimize a folded
circuit: the transpiler would cancel the inserted G† G pairs.

Native inverses used:
    cz, ecr, cx, x, id   self-inverse
    rz(θ)                rz(-θ)  (virtual, noiseless)
    sx                   rz(π) sx rz(π)  (= sx† up to global phase; same noise as one sx)

    .venv/Scripts/python folding.py      # runs the self-checks
"""

from __future__ import annotations

import math

from qiskit import QuantumCircuit
from qiskit.circuit.library import RZGate

SELF_INVERSE = {"cz", "ecr", "cx", "x", "id"}
NOT_FOLDED = {"measure", "barrier", "delay", "reset"}


def _native_inverse(instruction) -> list:
    """Native-gate instructions implementing the inverse of one ISA instruction."""
    op, qubits = instruction.operation, instruction.qubits
    if op.name in SELF_INVERSE:
        return [(op, qubits)]
    if op.name == "rz":
        return [(RZGate(-op.params[0]), qubits)]
    if op.name == "sx":
        return [(RZGate(math.pi), qubits), (op, qubits), (RZGate(math.pi), qubits)]
    raise ValueError(f"No native inverse defined for gate '{op.name}'")


def fold(circuit: QuantumCircuit, scale: int) -> QuantumCircuit:
    """Locally fold every gate of an ISA circuit. `scale` must be a positive odd integer."""
    if scale < 1 or scale % 2 == 0:
        raise ValueError("scale must be a positive odd integer (1, 3, 5, ...)")
    folds = (scale - 1) // 2
    folded = circuit.copy_empty_like()
    for instruction in circuit.data:
        folded.append(instruction)
        if instruction.operation.name in NOT_FOLDED:
            continue
        inverse = _native_inverse(instruction)
        for _ in range(folds):
            for op, qubits in inverse:
                folded.append(op, qubits)
            folded.append(instruction)
    return folded


def two_qubit_count(circuit: QuantumCircuit) -> int:
    return sum(1 for i in circuit.data if i.operation.num_qubits == 2 and i.operation.name != "barrier")


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
    for basis in (["cz", "sx", "x", "rz"], ["ecr", "sx", "x", "rz"]):
        native = transpile(qc, basis_gates=basis, optimization_level=0)
        for scale in (1, 3, 5):
            folded = fold(native, scale)
            assert Operator(folded).equiv(Operator(native)), (basis, scale)
            assert two_qubit_count(folded) == scale * two_qubit_count(native), (basis, scale)
            assert len(folded.data) > len(native.data) or scale == 1
        print(f"basis {basis[0]}: folded circuits at scales 1/3/5 are equivalent; 2q count scales exactly")


if __name__ == "__main__":
    _self_check()
