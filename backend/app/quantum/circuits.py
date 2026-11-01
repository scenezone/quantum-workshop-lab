from copy import deepcopy

from qiskit import QuantumCircuit
from qiskit.quantum_info import Pauli, Statevector, partial_trace

from app.content.curriculum import EXPERIMENTS
from app.errors import NotFoundError

CUSTOM_SINGLE_GATES = {"H": "h", "X": "x", "Y": "y", "Z": "z", "S": "s", "T": "t"}
CUSTOM_ROTATIONS = {"RX": "rx", "RY": "ry", "RZ": "rz"}
CUSTOM_TWO_QUBIT_GATES = {"CX": "cx", "CZ": "cz", "SWAP": "swap"}


def get_metadata(experiment_id: str) -> dict:
    metadata = EXPERIMENTS.get(experiment_id)
    if metadata is None:
        raise NotFoundError("Unknown experiment.")
    return deepcopy(metadata)


def build_circuit(experiment_id: str) -> QuantumCircuit:
    metadata = get_metadata(experiment_id)
    qc = QuantumCircuit(metadata["qubits"], metadata["classical_bits"], name=str(experiment_id))
    for gate in metadata["gates"]:
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


def build_custom_circuit(qubit_count: int, gates: list[dict]) -> QuantumCircuit:
    circuit = QuantumCircuit(qubit_count, qubit_count, name="custom_workshop_circuit")
    for gate in gates:
        name = gate["name"]
        qubits = gate["qubits"]
        if name in CUSTOM_SINGLE_GATES:
            getattr(circuit, CUSTOM_SINGLE_GATES[name])(qubits[0])
        elif name in CUSTOM_ROTATIONS:
            getattr(circuit, CUSTOM_ROTATIONS[name])(gate["angle"], qubits[0])
        elif name in CUSTOM_TWO_QUBIT_GATES:
            getattr(circuit, CUSTOM_TWO_QUBIT_GATES[name])(*qubits)
        else:
            raise ValueError("Unsupported custom gate.")
    circuit.measure(range(qubit_count), range(qubit_count))
    return circuit


def _state_snapshot(circuit: QuantumCircuit, step: int, gate: str, explanation: str) -> dict:
    state = Statevector.from_instruction(circuit)
    vectors = []
    for qubit in range(circuit.num_qubits):
        reduced = partial_trace(
            state, [index for index in range(circuit.num_qubits) if index != qubit]
        )
        vectors.append(
            {
                "qubit": qubit,
                "x": float(reduced.expectation_value(Pauli("X")).real),
                "y": float(reduced.expectation_value(Pauli("Y")).real),
                "z": float(reduced.expectation_value(Pauli("Z")).real),
            }
        )
    return {"step": step, "gate": gate, "explanation": explanation, "qubits": vectors}


def all_experiments() -> list[dict]:
    return [get_metadata(experiment_id) for experiment_id in EXPERIMENTS]
