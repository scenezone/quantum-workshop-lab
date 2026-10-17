from qiskit import QuantumCircuit
from app.errors import NotFoundError


CIRCUIT_BUILDERS = {
    "superposition": lambda: _superposition(),
    "bell_entanglement": lambda: _bell(),
    "interference": lambda: _interference(),
}

METADATA = {
    "superposition": {
        "title": "Superposition",
        "qubits": 1,
        "ideal_probabilities": {"0": 0.5, "1": 0.5},
        "description": "One Hadamard gate creates an equal superposition.",
    },
    "bell_entanglement": {
        "title": "Bell-State Entanglement",
        "qubits": 2,
        "ideal_probabilities": {"00": 0.5, "01": 0.0, "10": 0.0, "11": 0.5},
        "description": "Hadamard plus CNOT creates a maximally entangled Bell state.",
    },
    "interference": {
        "title": "Quantum Interference",
        "qubits": 1,
        "ideal_probabilities": {"0": 1.0, "1": 0.0},
        "description": "Two Hadamard gates interfere constructively for |0⟩.",
    },
}

def _superposition() -> QuantumCircuit:
    qc = QuantumCircuit(1, 1, name="superposition")
    qc.h(0)
    qc.measure(0, 0)
    return qc


def _bell() -> QuantumCircuit:
    qc = QuantumCircuit(2, 2, name="bell_entanglement")
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    return qc


def _interference() -> QuantumCircuit:
    qc = QuantumCircuit(1, 1, name="interference")
    qc.h(0)
    qc.h(0)
    qc.measure(0, 0)
    return qc

def build_circuit(experiment_id: str)-> QuantumCircuit:
    builder = CIRCUIT_BUILDERS.get(experiment_id)
    if not builder:
        raise NotFoundError("Unknown experiments.")
    return builder()

def get_metadata(experiment_id: str)->dict:
    metadata = METADATA.get(experiment_id)
    if metadata is None:
        raise NotFoundError("Unknown experiments.")
    return metadata

def all_experiments() -> list[dict]:
    return [
        {"experiment_id":experiment_id,**metadata}
        for experiment_id, metadata in METADATA.items()
    ]
