import math
from copy import deepcopy

from qiskit import QuantumCircuit
from qiskit.quantum_info import Pauli, Statevector, partial_trace

from app.content.curriculum import EXPERIMENTS
from app.errors import AppError, NotFoundError
from app.quantum.catalog import CUSTOM_GATES, MEASUREMENT_BASES


def get_metadata(experiment_id: str) -> dict:
    metadata = EXPERIMENTS.get(experiment_id)
    if metadata is None:
        raise NotFoundError("Unknown experiment.")
    return deepcopy(metadata)


def validate_bases(bases: list[str] | None, qubit_count: int) -> list[str] | None:
    """Return None for the default all-Z measurement, otherwise a checked basis list."""
    if bases is None:
        return None
    if len(bases) != qubit_count or any(basis not in MEASUREMENT_BASES for basis in bases):
        raise AppError("Provide one measurement basis (Z, X, or Y) for each qubit.")
    return None if all(basis == "Z" for basis in bases) else list(bases)


def rotate_to_basis(qc: QuantumCircuit, qubit: int, basis: str) -> None:
    """Map the chosen basis onto Z so a computational-basis measurement reads it."""
    if basis == "X":
        qc.h(qubit)
    elif basis == "Y":
        qc.sdg(qubit)
        qc.h(qubit)


def build_circuit(experiment_id: str, bases: list[str] | None = None) -> QuantumCircuit:
    metadata = get_metadata(experiment_id)
    qc = QuantumCircuit(metadata["qubits"], metadata["classical_bits"], name=str(experiment_id))
    rotated: set[int] = set()
    for gate in metadata["gates"]:
        if gate["name"] == "Measure" and bases:
            for qubit in gate["qubits"]:
                if qubit not in rotated:
                    rotate_to_basis(qc, qubit, bases[qubit])
                    rotated.add(qubit)
        apply_gate(qc, gate)
    return qc


def apply_gate(qc: QuantumCircuit, gate: dict) -> None:
    name, qubits = gate["name"], gate["qubits"]
    single = {"H": qc.h, "X": qc.x, "Y": qc.y, "Z": qc.z, "S": qc.s, "T": qc.t}
    multi = {"CX": qc.cx, "CZ": qc.cz, "CCX": qc.ccx, "SWAP": qc.swap}
    if name in single:
        single[name](*qubits)
    elif name in multi:
        multi[name](*qubits)
    elif name == "CP":
        qc.cp(gate["angle"], *qubits)
    elif name == "Measure":
        qc.measure(qubits, gate["classical_bits"])
    else:
        raise ValueError(f"Unsupported approved gate: {name}")


def apply_custom_gate(qc: QuantumCircuit, gate: dict) -> None:
    spec = CUSTOM_GATES.get(gate["name"])
    if spec is None:
        raise ValueError("Unsupported custom gate.")
    method = getattr(qc, spec["method"])
    if spec["params"] == 3:
        method(gate["angle"], gate["phi"], gate["lam"], *gate["qubits"])
    elif spec["params"] == 1:
        method(gate["angle"], *gate["qubits"])
    else:
        method(*gate["qubits"])


def build_custom_circuit(
    qubit_count: int, gates: list[dict], bases: list[str] | None = None, measure: bool = True
) -> QuantumCircuit:
    circuit = QuantumCircuit(qubit_count, qubit_count, name="custom_workshop_circuit")
    for gate in gates:
        apply_custom_gate(circuit, gate)
    if measure:
        for qubit, basis in enumerate(bases or ["Z"] * qubit_count):
            rotate_to_basis(circuit, qubit, basis)
        circuit.measure(range(qubit_count), range(qubit_count))
    return circuit


def custom_statevector(qubit_count: int, gates: list[dict]) -> Statevector:
    return Statevector.from_instruction(build_custom_circuit(qubit_count, gates, measure=False))


def ideal_measured_probabilities(circuit: QuantumCircuit) -> dict[str, float] | None:
    """Ideal classical-register probabilities for a circuit whose measurements are final.

    Keys follow Qiskit's displayed bit order (highest classical bit first). Returns None
    when a classical bit is never measured, because its value would be undefined here.
    """
    measured: dict[int, int] = {}
    for instruction in circuit.data:
        if instruction.operation.name == "measure":
            qubit = circuit.find_bit(instruction.qubits[0]).index
            clbit = circuit.find_bit(instruction.clbits[0]).index
            measured[clbit] = qubit
    if sorted(measured) != list(range(circuit.num_clbits)):
        return None
    state = Statevector.from_instruction(circuit.remove_final_measurements(inplace=False))
    # probabilities_dict puts qargs[0] in the rightmost key position, matching clbit 0.
    probabilities = state.probabilities_dict(qargs=[measured[clbit] for clbit in sorted(measured)])
    return {
        outcome: round(float(probability), 12)
        for outcome, probability in sorted(probabilities.items())
        if probability > 1e-12
    }


def amplitude_rows(state: Statevector) -> list[dict]:
    width = state.num_qubits
    return [
        {
            "outcome": format(index, f"0{width}b"),
            "real": float(amplitude.real),
            "imag": float(amplitude.imag),
            "probability": float(abs(amplitude) ** 2),
            "phase_degrees": math.degrees(math.atan2(amplitude.imag, amplitude.real)),
        }
        for index, amplitude in enumerate(state.data)
        if abs(amplitude) > 1e-12
    ]


def state_evolution(experiment_id: str) -> dict:
    metadata = get_metadata(experiment_id)
    circuit = QuantumCircuit(metadata["qubits"])
    steps = [_state_snapshot(circuit, 0, "Start", "All qubits start in |0>.")]
    for index, gate in enumerate(metadata["gates"], 1):
        if gate["name"] == "Measure":
            continue
        apply_gate(circuit, gate)
        label = gate.get("label") or gate["name"]
        steps.append(_state_snapshot(circuit, index, label, gate["explanation"]))
    return {"experiment_id": experiment_id, "qubits": metadata["qubits"], "steps": steps}


def custom_state_evolution(qubit_count: int, gates: list[dict]) -> dict:
    circuit = QuantumCircuit(qubit_count)
    steps = [_state_snapshot(circuit, 0, "Start", "All qubits start in |0>.")]
    for index, gate in enumerate(gates, 1):
        apply_custom_gate(circuit, gate)
        spec = CUSTOM_GATES[gate["name"]]
        operands = ", ".join(f"q{qubit}" for qubit in gate["qubits"])
        steps.append(
            _state_snapshot(circuit, index, gate["name"], f"{spec['label']} on {operands}.")
        )
    return {"experiment_id": "custom", "qubits": qubit_count, "steps": steps}


def _state_snapshot(circuit: QuantumCircuit, step: int, gate: str, explanation: str) -> dict:
    state = Statevector.from_instruction(circuit)
    vectors = []
    for qubit in range(circuit.num_qubits):
        others = [index for index in range(circuit.num_qubits) if index != qubit]
        reduced = partial_trace(state, others) if others else state
        x = float(reduced.expectation_value(Pauli("X")).real)
        y = float(reduced.expectation_value(Pauli("Y")).real)
        z = float(reduced.expectation_value(Pauli("Z")).real)
        vectors.append(
            # A length below 1 means this qubit is entangled with the others.
            {"qubit": qubit, "x": x, "y": y, "z": z, "length": math.sqrt(x * x + y * y + z * z)}
        )
    return {"step": step, "gate": gate, "explanation": explanation, "qubits": vectors}


def all_experiments() -> list[dict]:
    return [get_metadata(experiment_id) for experiment_id in EXPERIMENTS]
