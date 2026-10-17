from qiskit import Transpile
from qiskit_aer import AerSimulator

from app.config import get_settings
from app.errors import AppError
from app.quantum.circuits import build_circuit,get_metadata

def run_simulation(experiment_id: str,shots: int)->dict:
    settings = get_settings()
    if not 1 <= shots <= settings.max_simulation_shots:
        raise AppError("Invalid number of shots.")

    circuit = build_circuit(experiment_id)
    backend = AerSimulator()
    compiled = Transpile(circuit,backend)

    try:
        result = backend.run(compiled,shots=shots).result()
        counts = result.get_counts(0)
    except Exception as exc:
        raise AppError(f"Simulation failed.") from exc

    return {
        "experiment_id": experiment_id,
        "backend": "aer_simulator",
        "backend_name": "Qiskit Aer",
        "shots": shots,
        "counts": dict(counts),
        "observed_probabilities": normalize_counts(dict(counts), shots),
        "ideal_probabilities": get_metadata(experiment_id)["ideal_probabilities"],
        "provider_job_id": None,
        "tracking_id": None,
    }

def normalize_counts(counts:dict[str,int],shots:int)->dict[str,float]:
    total = sum(counts.values()) or shots
    return {key: value / total for key, value in counts.items()}
