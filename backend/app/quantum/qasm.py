"""Convert an OpenQASM 2 program into the builder's validated gate list."""

import math
import re

from qiskit import qasm2

from app.errors import InvalidInputError
from app.quantum.catalog import MAX_CUSTOM_GATES, MAX_CUSTOM_QUBITS

INCLUDE = re.compile(r'include\s+"([^"]*)"\s*;')
ONE_PARAM = {"rx": "RX", "ry": "RY", "rz": "RZ", "cp": "CP", "cu1": "CP"}
NO_PARAM = {
    "h": "H",
    "x": "X",
    "y": "Y",
    "z": "Z",
    "s": "S",
    "t": "T",
    "sx": "SX",
    "cx": "CX",
    "cz": "CZ",
    "swap": "SWAP",
    "ccx": "CCX",
}
IGNORED = {"barrier", "id"}


def _angle(value) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise InvalidInputError("Gate angles must be numeric constants.") from exc
    if not math.isfinite(number):
        raise InvalidInputError("Gate angles must be finite.")
    # Equivalent rotation in [-π, π], within the builder's ±2π limit.
    return round(math.remainder(number, 2 * math.pi), 12)


def import_qasm(source: str) -> dict:
    for name in INCLUDE.findall(source):
        if name != "qelib1.inc":
            raise InvalidInputError('Only include "qelib1.inc" is supported.')
    try:
        # An empty include path means the parser never reads files from disk. The legacy
        # instructions add the gates Qiskit exports with qelib1.inc, such as p, sx, and cp.
        circuit = qasm2.loads(
            source, include_path=(), custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS
        )
    except qasm2.QASM2ParseError as exc:
        raise InvalidInputError(
            f"Could not parse this OpenQASM 2 program: {str(exc)[:200]}"
        ) from exc

    if not 1 <= circuit.num_qubits <= MAX_CUSTOM_QUBITS:
        raise InvalidInputError(f"The builder supports 1 to {MAX_CUSTOM_QUBITS} qubits.")

    gates: list[dict] = []
    measured = False
    for instruction in circuit.data:
        name = instruction.operation.name
        qubits = [circuit.find_bit(qubit).index for qubit in instruction.qubits]
        params = instruction.operation.params
        if name in IGNORED:
            continue
        if name == "measure":
            measured = True
            continue
        if measured:
            raise InvalidInputError(
                "Gates after a measurement are not supported; the builder measures every qubit at the end."
            )
        if name in NO_PARAM:
            gates.append({"name": NO_PARAM[name], "qubits": qubits})
        elif name in ONE_PARAM:
            gates.append({"name": ONE_PARAM[name], "qubits": qubits, "angle": _angle(params[0])})
        elif name in {"u", "u3", "U"}:
            theta, phi, lam = (_angle(value) for value in params)
            gates.append({"name": "U", "qubits": qubits, "angle": theta, "phi": phi, "lam": lam})
        elif name in {"p", "u1"}:
            # P(λ) equals U(0, 0, λ) exactly.
            gates.append(
                {"name": "U", "qubits": qubits, "angle": 0.0, "phi": 0.0, "lam": _angle(params[0])}
            )
        else:
            raise InvalidInputError(f"The gate '{name}' is not available in the circuit builder.")
        if len(gates) > MAX_CUSTOM_GATES:
            raise InvalidInputError(f"The builder supports at most {MAX_CUSTOM_GATES} gates.")
    return {"qubits": circuit.num_qubits, "gates": gates}
