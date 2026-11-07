"""Single source of truth for builder gates, limits, noise profiles, and measurement bases.

`scripts/export_catalog.py` writes these values to the frontend, and a test fails when the
generated TypeScript file is out of date.
"""

import math

ANGLE_LIMIT = 2 * math.pi
MAX_CUSTOM_QUBITS = 5
MAX_CUSTOM_GATES = 40

# qubits: operands (controls first); params: 0, 1 (angle), or 3 (angle, phi, lam).
CUSTOM_GATES: dict[str, dict] = {
    "H": {"qubits": 1, "params": 0, "method": "h", "symbol": "H", "label": "Hadamard"},
    "X": {"qubits": 1, "params": 0, "method": "x", "symbol": "X", "label": "Pauli-X (NOT)"},
    "Y": {"qubits": 1, "params": 0, "method": "y", "symbol": "Y", "label": "Pauli-Y"},
    "Z": {"qubits": 1, "params": 0, "method": "z", "symbol": "Z", "label": "Pauli-Z"},
    "S": {"qubits": 1, "params": 0, "method": "s", "symbol": "S", "label": "S (quarter turn)"},
    "T": {"qubits": 1, "params": 0, "method": "t", "symbol": "T", "label": "T (eighth turn)"},
    "SX": {"qubits": 1, "params": 0, "method": "sx", "symbol": "√X", "label": "Square root of X"},
    "RX": {"qubits": 1, "params": 1, "method": "rx", "symbol": "RX", "label": "X rotation"},
    "RY": {"qubits": 1, "params": 1, "method": "ry", "symbol": "RY", "label": "Y rotation"},
    "RZ": {"qubits": 1, "params": 1, "method": "rz", "symbol": "RZ", "label": "Z rotation"},
    "U": {
        "qubits": 1,
        "params": 3,
        "method": "u",
        "symbol": "U",
        "label": "General rotation U(θ, φ, λ)",
    },
    "CX": {"qubits": 2, "params": 0, "method": "cx", "symbol": "⊕", "label": "Controlled-X (CNOT)"},
    "CZ": {"qubits": 2, "params": 0, "method": "cz", "symbol": "Z", "label": "Controlled-Z"},
    "CP": {"qubits": 2, "params": 1, "method": "cp", "symbol": "P", "label": "Controlled phase"},
    "SWAP": {"qubits": 2, "params": 0, "method": "swap", "symbol": "×", "label": "Swap"},
    "CCX": {"qubits": 3, "params": 0, "method": "ccx", "symbol": "⊕", "label": "Toffoli (CCX)"},
}

MEASUREMENT_BASES = ("Z", "X", "Y")

# Depolarizing one-qubit error, two-qubit error, and readout flip probability.
NOISE_PRESETS: dict[str, dict] = {
    "ideal": {"errors": (0.0, 0.0, 0.0), "label": "Ideal (no added noise)"},
    "low": {"errors": (0.002, 0.01, 0.01), "label": "Low noise"},
    "medium": {"errors": (0.01, 0.04, 0.03), "label": "Medium noise"},
    "high": {"errors": (0.03, 0.10, 0.08), "label": "High noise"},
}

# Calibration snapshots shipped with qiskit-ibm-runtime; no IBM account is needed.
DEVICE_PROFILES: dict[str, dict] = {
    "device_manila": {
        "backend": "FakeManilaV2",
        "label": "IBM Manila snapshot (5 qubits, simulated)",
    },
    "device_nairobi": {
        "backend": "FakeNairobiV2",
        "label": "IBM Nairobi snapshot (7 qubits, simulated)",
    },
    "device_sherbrooke": {
        "backend": "FakeSherbrooke",
        "label": "IBM Sherbrooke snapshot (127 qubits, simulated)",
    },
}

NOISE_PROFILE_IDS: tuple[str, ...] = tuple(NOISE_PRESETS) + tuple(DEVICE_PROFILES)


def noise_profile_catalog() -> list[dict]:
    return [
        {"id": key, "label": value["label"], "kind": "preset"}
        for key, value in NOISE_PRESETS.items()
    ] + [
        {"id": key, "label": value["label"], "kind": "device"}
        for key, value in DEVICE_PROFILES.items()
    ]
