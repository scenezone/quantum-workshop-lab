import logging
import threading

from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator, noise

from app.config import get_settings
from app.errors import AppError
from app.quantum.catalog import DEVICE_PROFILES, NOISE_PRESETS, NOISE_PROFILE_IDS
from app.quantum.circuits import (
    amplitude_rows,
    build_circuit,
    build_custom_circuit,
    get_metadata,
    ideal_measured_probabilities,
    validate_bases,
)

logger = logging.getLogger(__name__)

# Kept for callers that read the preset error rates directly.
NOISE_PROFILES = {key: value["errors"] for key, value in NOISE_PRESETS.items()}
NOISY_ONE_QUBIT = ["h", "x", "y", "z", "s", "sdg", "t", "sx", "rx", "ry", "rz", "u"]
NOISY_TWO_QUBIT = ["cx", "cz", "cp", "swap"]

_device_simulators: dict[str, AerSimulator] = {}
_device_lock = threading.Lock()


def validate_request(shots: int, noise_profile: str) -> None:
    if not 1 <= shots <= get_settings().max_simulator_shots:
        raise AppError("Invalid number of shots.")
    if noise_profile not in NOISE_PROFILE_IDS:
        raise AppError("Unknown noise profile.")


def backend_label(noise_profile: str) -> str:
    device = DEVICE_PROFILES.get(noise_profile)
    return f"Qiskit Aer · {device['label']}" if device else "Qiskit Aer"


def _device_simulator(profile: str) -> AerSimulator:
    with _device_lock:
        if profile not in _device_simulators:
            from qiskit_ibm_runtime import fake_provider

            fake_backend = getattr(fake_provider, DEVICE_PROFILES[profile]["backend"])()
            _device_simulators[profile] = AerSimulator.from_backend(fake_backend)
        return _device_simulators[profile]


def run_circuits(circuits: list[QuantumCircuit], shots: int, noise_profile: str) -> list[dict]:
    """Run measured circuits in one Aer job and return counts in input order."""
    try:
        if noise_profile in DEVICE_PROFILES:
            backend = _device_simulator(noise_profile)
            # A fixed seed keeps the qubit layout, and therefore its noise, reproducible.
            compiled = transpile(circuits, backend, optimization_level=1, seed_transpiler=11)
        else:
            backend = AerSimulator(noise_model=build_noise_model(noise_profile))
            compiled = transpile(circuits, backend)
        result = backend.run(compiled, shots=shots).result()
        return [dict(result.get_counts(index)) for index in range(len(circuits))]
    except AppError:
        raise
    except Exception as exc:
        logger.exception("Simulation failed")
        raise AppError("Simulation failed.") from exc


def run_simulation(
    experiment_id: str,
    shots: int,
    noise_profile: str = "ideal",
    measurement_bases: list[str] | None = None,
) -> dict:
    validate_request(shots, noise_profile)
    metadata = get_metadata(experiment_id)
    bases = validate_bases(measurement_bases, metadata["qubits"])
    circuit = build_circuit(experiment_id, bases)
    counts = run_circuits([circuit], shots, noise_profile)[0]
    prepared = build_circuit(experiment_id).remove_final_measurements(inplace=False)
    ideal = (
        ideal_measured_probabilities(circuit) if bases else metadata["ideal_probabilities"]
    ) or metadata["ideal_probabilities"]
    return _result(
        experiment_id,
        shots,
        noise_profile,
        counts,
        ideal,
        amplitude_rows(Statevector.from_instruction(prepared)),
        bases or ["Z"] * metadata["qubits"],
    )


def run_custom_simulation(
    qubit_count: int,
    gates: list[dict],
    shots: int,
    noise_profile: str,
    measurement_bases: list[str] | None = None,
) -> dict:
    validate_request(shots, noise_profile)
    bases = validate_bases(measurement_bases, qubit_count)
    circuit = build_custom_circuit(qubit_count, gates, bases)
    counts = run_circuits([circuit], shots, noise_profile)[0]
    prepared = build_custom_circuit(qubit_count, gates, measure=False)
    return _result(
        "custom",
        shots,
        noise_profile,
        counts,
        ideal_measured_probabilities(circuit) or {},
        amplitude_rows(Statevector.from_instruction(prepared)),
        bases or ["Z"] * qubit_count,
    )


def _result(
    experiment_id: str,
    shots: int,
    noise_profile: str,
    counts: dict,
    ideal: dict,
    amplitudes: list[dict],
    bases: list[str],
) -> dict:
    return {
        "experiment_id": experiment_id,
        "backend": "aer_simulator",
        "backend_name": backend_label(noise_profile),
        "shots": shots,
        "noise_profile": noise_profile,
        "measurement_bases": bases,
        "counts": counts,
        "observed_probabilities": normalize_counts(counts, shots),
        "ideal_probabilities": ideal,
        "amplitudes": amplitudes,
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
            noise.depolarizing_error(one_qubit_error, 1), NOISY_ONE_QUBIT
        )
    if two_qubit_error:
        model.add_all_qubit_quantum_error(
            noise.depolarizing_error(two_qubit_error, 2), NOISY_TWO_QUBIT
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
