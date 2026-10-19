from copy import deepcopy

from qiskit import QuantumCircuit

from app.content.curriculum import EXPERIMENTS
from app.errors import NotFoundError


def get_metadata(experiment_id: str) -> dict:
    metadata = EXPERIMENTS.get(experiment_id)
    if metadata is None:
        raise NotFoundError("Unknown experiment.")
    return deepcopy(metadata)


def build_circuit(experiment_id: str) -> QuantumCircuit:
    metadata = get_metadata(experiment_id)
    qc = QuantumCircuit(metadata["qubits"], metadata["classical_bits"], name=str(experiment_id))
    single = {"H": qc.h, "X": qc.x, "Y": qc.y, "Z": qc.z, "S": qc.s, "T": qc.t}
    multi = {"CX": qc.cx, "CZ": qc.cz, "CCX": qc.ccx, "SWAP": qc.swap}
    for gate in metadata["gates"]:
        name, qubits = gate["name"], gate["qubits"]
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
    return qc


def all_experiments() -> list[dict]:
    return [get_metadata(experiment_id) for experiment_id in EXPERIMENTS]
