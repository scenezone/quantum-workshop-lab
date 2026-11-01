import math

from qiskit import transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator, noise

from app.config import get_settings
from app.errors import AppError
from app.quantum.circuits import build_circuit, build_custom_circuit, get_metadata

NOISE_PROFILES = {
    "ideal": (0.0, 0.0, 0.0),
    "low": (0.002, 0.01, 0.01),
    "medium": (0.01, 0.04, 0.03),
    "high": (0.03, 0.10, 0.08),
}


def run_simulation(experiment_id: str, shots: int, noise_profile: str = "ideal") -> dict:
    settings = get_settings()
    if not 1 <= shots <= settings.max_simulator_shots:
        raise AppError("Invalid number of shots.")
    if noise_profile not in NOISE_PROFILES:
        raise AppError("Unknown noise profile.")
    circuit = build_circuit(experiment_id)
    backend = AerSimulator(noise_model=build_noise_model(noise_profile))
    try:
        compiled = transpile(circuit, backend)
        result = backend.run(compiled, shots=shots).result()
        counts = dict(result.get_counts(0))
        state = Statevector.from_instruction(circuit.remove_final_measurements(inplace=False))
        amplitudes = [
            {
                "outcome": format(index, f"0{circuit.num_qubits}b"),
                "real": float(amplitude.real),
                "imag": float(amplitude.imag),
                "probability": float(abs(amplitude) ** 2),
                "phase_degrees": math.degrees(math.atan2(amplitude.imag, amplitude.real)),
            }
            for index, amplitude in enumerate(state.data)
            if abs(amplitude) > 1e-12
        ]
    except Exception as exc:
        raise AppError("Simulation failed.") from exc
    return {
        "experiment_id": experiment_id,
        "backend": "aer_simulator",
        "backend_name": "Qiskit Aer",
        "shots": shots,
        "noise_profile": noise_profile,
        "counts": counts,
        "observed_probabilities": normalize_counts(counts, shots),
        "ideal_probabilities": get_metadata(experiment_id)["ideal_probabilities"],
        "amplitudes": amplitudes,
        "provider_job_id": None,
        "tracking_id": None,
    }


def run_custom_simulation(
    qubit_count: int, gates: list[dict], shots: int, noise_profile: str
) -> dict:
    settings = get_settings()
    if not 1 <= shots <= settings.max_simulator_shots:
        raise AppError("Invalid number of shots.")
    if noise_profile not in NOISE_PROFILES:
        raise AppError("Unknown noise profile.")
    circuit = build_custom_circuit(qubit_count, gates)
    ideal_state = Statevector.from_instruction(circuit.remove_final_measurements(inplace=False))
    ideal_probabilities = {
        outcome: float(probability)
        for outcome, probability in ideal_state.probabilities_dict().items()
        if probability > 1e-12
    }
    try:
        backend = AerSimulator(noise_model=build_noise_model(noise_profile))
        compiled = transpile(circuit, backend)
        counts = dict(backend.run(compiled, shots=shots).result().get_counts(0))
    except Exception as exc:
        raise AppError("Simulation failed.") from exc
    return {
        "experiment_id": "custom",
        "backend": "aer_simulator",
        "backend_name": "Qiskit Aer",
        "shots": shots,
        "noise_profile": noise_profile,
        "counts": counts,
        "observed_probabilities": normalize_counts(counts, shots),
        "ideal_probabilities": ideal_probabilities,
        "amplitudes": [
            {
                "outcome": format(index, f"0{qubit_count}b"),
                "real": float(amplitude.real),
                "imag": float(amplitude.imag),
                "probability": float(abs(amplitude) ** 2),
                "phase_degrees": math.degrees(math.atan2(amplitude.imag, amplitude.real)),
            }
            for index, amplitude in enumerate(ideal_state.data)
            if abs(amplitude) > 1e-12
        ],
        "provider_job_id": None,
        "tracking_id": None,
    }


def build_noise_model(profile: str) -> noise.NoiseModel | None:
    one_qubit_error, two_qubit_error, readout_error = NOISE_PROFILES[profile]
    if not any((one_qubit_error, two_qubit_error, readout_error)):
        return None

    model = noise.NoiseModel()
    if one_qubit_error:
        model.add_all_qubit_quantum_error(
            noise.depolarizing_error(one_qubit_error, 1),
            ["h", "x", "y", "z", "s", "t", "rx", "ry", "rz"],
        )
    if two_qubit_error:
        model.add_all_qubit_quantum_error(
            noise.depolarizing_error(two_qubit_error, 2), ["cx", "cz", "cp", "swap"]
        )
        model.add_all_qubit_quantum_error(noise.depolarizing_error(two_qubit_error, 3), ["ccx"])
    if readout_error:
        model.add_all_qubit_readout_error(
            noise.ReadoutError(
                [[1 - readout_error, readout_error], [readout_error, 1 - readout_error]]
            )
        )
    return model


def normalize_counts(counts: dict[str, int], shots: int) -> dict[str, float]:
    total = sum(counts.values()) or shots
    return {key: value / total for key, value in counts.items()}
