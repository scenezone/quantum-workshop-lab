import math

from qiskit import transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from app.config import get_settings
from app.errors import AppError
from app.quantum.circuits import build_circuit, get_metadata


def run_simulation(experiment_id: str, shots: int) -> dict:
    settings = get_settings()
    if not 1 <= shots <= settings.max_simulator_shots:
        raise AppError("Invalid number of shots.")
    circuit = build_circuit(experiment_id)
    backend = AerSimulator()
    try:
        compiled = transpile(circuit, backend)
        result = backend.run(compiled, shots=shots).result()
        counts = dict(result.get_counts(0))
        state = Statevector.from_instruction(circuit.remove_final_measurements(inplace=False))
        amplitudes = [{
            "outcome": format(index, f"0{circuit.num_qubits}b"),
            "real": float(amplitude.real),
            "imag": float(amplitude.imag),
            "probability": float(abs(amplitude) ** 2),
            "phase_degrees": math.degrees(math.atan2(amplitude.imag, amplitude.real)),
        } for index, amplitude in enumerate(state.data) if abs(amplitude) > 1e-12]
    except Exception as exc:
        raise AppError("Simulation failed.") from exc
    return {
        "experiment_id": experiment_id, "backend": "aer_simulator",
        "backend_name": "Qiskit Aer", "shots": shots, "counts": counts,
        "observed_probabilities": normalize_counts(counts, shots),
        "ideal_probabilities": get_metadata(experiment_id)["ideal_probabilities"],
        "amplitudes": amplitudes, "provider_job_id": None, "tracking_id": None,
    }


def normalize_counts(counts: dict[str, int], shots: int) -> dict[str, float]:
    total = sum(counts.values()) or shots
    return {key: value / total for key, value in counts.items()}
