"""Multi-circuit labs: a CHSH Bell test and a small variational eigensolver."""

import math

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector

from app.errors import AppError
from app.quantum.simulator import backend_label, run_circuits, validate_request

CLASSICAL_BOUND = 2.0
QUANTUM_BOUND = 2 * math.sqrt(2)
DEFAULT_ALICE = (0.0, math.pi / 2)
DEFAULT_BOB = (math.pi / 4, -math.pi / 4)


def _bell_circuit(alice_angle: float, bob_angle: float) -> QuantumCircuit:
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    # Measuring cos(t)Z + sin(t)X equals rotating by RY(-t), then measuring Z.
    qc.ry(-alice_angle, 0)
    qc.ry(-bob_angle, 1)
    qc.measure([0, 1], [0, 1])
    return qc


def correlation(counts: dict[str, int]) -> float:
    total = sum(counts.values())
    if not total:
        return 0.0
    agree = sum(value for key, value in counts.items() if key[-1] == key[-2])
    return (2 * agree - total) / total


def run_chsh(
    shots: int,
    noise_profile: str,
    alice: tuple[float, float] | None = None,
    bob: tuple[float, float] | None = None,
) -> dict:
    validate_request(shots, noise_profile)
    alice = alice or DEFAULT_ALICE
    bob = bob or DEFAULT_BOB
    if any(not math.isfinite(angle) or abs(angle) > 2 * math.pi for angle in (*alice, *bob)):
        raise AppError("Measurement angles must be between -2π and 2π radians.")
    pairs = [(a, b) for a in alice for b in bob]
    all_counts = run_circuits([_bell_circuit(a, b) for a, b in pairs], shots, noise_profile)
    settings = []
    for (a, b), counts in zip(pairs, all_counts):
        settings.append(
            {
                "alice_angle": a,
                "bob_angle": b,
                "counts": counts,
                "correlation": correlation(counts),
                # For Φ+, E(a, b) = cos(a - b) for directions in the X-Z plane.
                "ideal_correlation": math.cos(a - b),
            }
        )
    signs = (1, 1, 1, -1)  # S = E(a0,b0) + E(a0,b1) + E(a1,b0) - E(a1,b1)
    s_value = sum(sign * item["correlation"] for sign, item in zip(signs, settings))
    ideal = sum(sign * item["ideal_correlation"] for sign, item in zip(signs, settings))
    # Each correlation estimate has variance (1 - E^2) / N.
    error = math.sqrt(sum(max(0.0, 1 - item["correlation"] ** 2) for item in settings) / shots)
    return {
        "shots": shots,
        "noise_profile": noise_profile,
        "backend_name": backend_label(noise_profile),
        "settings": settings,
        "s_value": s_value,
        "s_standard_error": error,
        "ideal_s_value": ideal,
        "classical_bound": CLASSICAL_BOUND,
        "quantum_bound": QUANTUM_BOUND,
    }


# Pauli labels follow Qiskit order: the rightmost character acts on qubit 0.
HAMILTONIANS = {
    "zx": {
        "description": "One qubit with H = Z + X. The exact ground energy is -√2.",
        "terms": [("Z", 1.0), ("X", 1.0)],
        "qubits": 1,
        "initial": [2.6],
    },
    "h2": {
        "description": (
            "Hydrogen molecule (STO-3G basis, 0.735 Å bond, parity mapping reduced to two qubits). "
            "Energies are electronic, in hartree."
        ),
        "terms": [
            ("II", -1.052373245772859),
            ("IZ", 0.39793742484318045),
            ("ZI", -0.39793742484318045),
            ("ZZ", -0.01128010425623538),
            ("XX", 0.18093119978423156),
        ],
        "qubits": 2,
        # Near the Hartree-Fock-like state; from (0, 0) descent crosses a long, flat plateau.
        "initial": [-0.5, 2.6],
    },
}


def _ansatz(qubits: int, parameters: list[float]) -> QuantumCircuit:
    qc = QuantumCircuit(qubits)
    for qubit, theta in enumerate(parameters):
        qc.ry(theta, qubit)
    if qubits == 2:
        qc.cx(0, 1)
    return qc


def _measurement_groups(terms: list[tuple[str, float]]) -> list[str]:
    """Each term here uses one Pauli type, so group terms by that letter (Z or X)."""
    letters = sorted({next((c for c in label if c != "I"), "Z") for label, _ in terms})
    return letters


def _estimate_energy(
    terms: list[tuple[str, float]], counts_by_basis: dict[str, dict[str, int]]
) -> float:
    energy = 0.0
    for label, coefficient in terms:
        letter = next((c for c in label if c != "I"), None)
        if letter is None:
            energy += coefficient
            continue
        counts = counts_by_basis[letter]
        total = sum(counts.values())
        value = 0
        for bitstring, count in counts.items():
            sign = 1
            for qubit, pauli in enumerate(reversed(label)):
                if pauli != "I" and bitstring[-1 - qubit] == "1":
                    sign = -sign
            value += sign * count
        energy += coefficient * value / total
    return energy


def _measured(qubits: int, parameters: list[float], letter: str) -> QuantumCircuit:
    qc = _ansatz(qubits, parameters)
    if letter == "X":
        for qubit in range(qubits):
            qc.h(qubit)
    qc.measure_all()
    return qc


def run_vqe(
    hamiltonian: str,
    iterations: int,
    learning_rate: float,
    shots: int,
    noise_profile: str,
    initial_parameters: list[float] | None = None,
) -> dict:
    validate_request(shots, noise_profile)
    spec = HAMILTONIANS[hamiltonian]
    qubits, terms = spec["qubits"], spec["terms"]
    operator = SparsePauliOp.from_list(terms)
    ground = float(np.linalg.eigvalsh(operator.to_matrix()).min())
    parameters = list(initial_parameters or spec["initial"])
    if len(parameters) != qubits:
        raise AppError(f"This Hamiltonian uses {qubits} parameter(s).")
    groups = _measurement_groups(terms)

    def exact(point: list[float]) -> float:
        return float(
            Statevector.from_instruction(_ansatz(qubits, point)).expectation_value(operator).real
        )

    trace = []
    for iteration in range(iterations + 1):
        # Parameter-shift rule: dE/dθ = [E(θ + π/2) − E(θ − π/2)] / 2 for RY rotations.
        points = [parameters]
        for index in range(qubits):
            for shift in (math.pi / 2, -math.pi / 2):
                shifted = list(parameters)
                shifted[index] += shift
                points.append(shifted)
        circuits = [_measured(qubits, point, letter) for point in points for letter in groups]
        counts = run_circuits(circuits, shots, noise_profile)
        energies = [
            _estimate_energy(
                terms,
                {
                    letter: counts[point_index * len(groups) + group_index]
                    for group_index, letter in enumerate(groups)
                },
            )
            for point_index in range(len(points))
        ]
        trace.append(
            {
                "iteration": iteration,
                "parameters": [round(value, 6) for value in parameters],
                "energy": energies[0],
                "exact_energy": exact(parameters),
            }
        )
        if iteration == iterations:
            break
        gradient = [(energies[1 + 2 * i] - energies[2 + 2 * i]) / 2 for i in range(qubits)]
        parameters = [
            math.remainder(value - learning_rate * grad, 2 * math.pi)
            for value, grad in zip(parameters, gradient)
        ]

    landscape = []
    if qubits == 1:
        landscape = [
            {"theta": theta, "energy": exact([theta])}
            for theta in np.linspace(-math.pi, math.pi, 61).tolist()
        ]
    return {
        "hamiltonian": hamiltonian,
        "description": spec["description"],
        "terms": terms,
        "parameter_count": qubits,
        "ground_energy": ground,
        "final_parameters": trace[-1]["parameters"],
        "final_energy": trace[-1]["energy"],
        "trace": trace,
        "landscape": landscape,
        "backend_name": backend_label(noise_profile),
    }
