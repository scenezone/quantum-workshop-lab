"""Circuit-building challenges graded on the server against a target state or distribution."""

import math

import numpy as np
from qiskit.quantum_info import Statevector

from app.errors import InvalidInputError, NotFoundError
from app.quantum.circuits import custom_statevector

R = 1 / math.sqrt(2)
FIDELITY_THRESHOLD = 0.99

# Simulator challenges defined and checked by the frontend Playground.
EXPERIMENT_CHALLENGE_IDS = (
    "balanced-superposition",
    "bell-correlations",
    "interference-cancellation",
)

# Targets use Qiskit's displayed bit order: the rightmost character is qubit 0.
BUILD_CHALLENGES: list[dict] = [
    {
        "challenge_id": "minus-state",
        "title": "Prepare the minus state",
        "objective": "Prepare |−⟩ = (|0⟩ − |1⟩)/√2 on one qubit.",
        "difficulty": "beginner",
        "qubits": 1,
        "allowed_gates": ["H", "X", "Z"],
        "max_gates": 3,
        "hint": "H turns |1⟩ into |−⟩. How do you reach |1⟩ first?",
        "kind": "state",
        "target": {"0": R, "1": -R},
    },
    {
        "challenge_id": "flip-without-x",
        "title": "Flip a qubit without X",
        "objective": "Turn |0⟩ into |1⟩ using only H and Z gates.",
        "difficulty": "beginner",
        "qubits": 1,
        "allowed_gates": ["H", "Z"],
        "max_gates": 3,
        "hint": "Z changes a relative phase. Sandwich it between two H gates.",
        "kind": "state",
        "target": {"1": 1.0},
    },
    {
        "challenge_id": "biased-coin",
        "title": "Build a 75/25 quantum coin",
        "objective": "Use RY rotations so a measurement gives 0 with 75% and 1 with 25% probability.",
        "difficulty": "beginner",
        "qubits": 1,
        "allowed_gates": ["RY"],
        "max_gates": 2,
        "hint": "RY(θ)|0⟩ gives P(1) = sin²(θ/2). Solve sin²(θ/2) = 0.25.",
        "kind": "distribution",
        "target": {"0": 0.75, "1": 0.25},
        "tolerance": 0.01,
    },
    {
        "challenge_id": "bell-phi-minus",
        "title": "Prepare the Φ⁻ Bell state",
        "objective": "Prepare (|00⟩ − |11⟩)/√2. Measured counts look like Φ⁺; only the phase differs.",
        "difficulty": "intermediate",
        "qubits": 2,
        "allowed_gates": ["H", "X", "Z", "CX"],
        "max_gates": 4,
        "hint": "Start from the Φ⁺ recipe, then add a phase to one branch.",
        "kind": "state",
        "target": {"00": R, "11": -R},
    },
    {
        "challenge_id": "bell-psi-plus",
        "title": "Prepare the Ψ⁺ Bell state",
        "objective": "Prepare (|01⟩ + |10⟩)/√2, where the two qubits always disagree.",
        "difficulty": "intermediate",
        "qubits": 2,
        "allowed_gates": ["H", "X", "CX"],
        "max_gates": 4,
        "hint": "Make the Bell pair, then flip one qubit so the outcomes disagree.",
        "kind": "state",
        "target": {"01": R, "10": R},
    },
    {
        "challenge_id": "ghz-three",
        "title": "Entangle three qubits",
        "objective": "Prepare the GHZ state (|000⟩ + |111⟩)/√2.",
        "difficulty": "intermediate",
        "qubits": 3,
        "allowed_gates": ["H", "CX"],
        "max_gates": 4,
        "hint": "One H creates the superposition; each CX copies the control into a new qubit.",
        "kind": "state",
        "target": {"000": R, "111": R},
    },
    {
        "challenge_id": "uniform-three",
        "title": "Sample all eight outcomes equally",
        "objective": "Make all eight 3-bit outcomes equally likely (12.5% each).",
        "difficulty": "beginner",
        "qubits": 3,
        "allowed_gates": ["H", "X", "RY", "CX"],
        "max_gates": 6,
        "hint": "Each qubit needs its own equal superposition.",
        "kind": "distribution",
        "target": {format(index, "03b"): 0.125 for index in range(8)},
        "tolerance": 0.01,
    },
    {
        "challenge_id": "toffoli-and",
        "title": "Compute AND with a Toffoli",
        "objective": "Set q0 and q1 to 1, then use CCX so q2 stores q0 AND q1. The final state is |111⟩.",
        "difficulty": "advanced",
        "qubits": 3,
        "allowed_gates": ["X", "CCX"],
        "max_gates": 3,
        "hint": "Prepare both controls with X, then apply CCX with q2 as the target.",
        "kind": "state",
        "target": {"111": 1.0},
    },
]

_BY_ID = {challenge["challenge_id"]: challenge for challenge in BUILD_CHALLENGES}


def public_challenges() -> list[dict]:
    return [
        {key: value for key, value in challenge.items() if key not in {"target", "tolerance"}}
        for challenge in BUILD_CHALLENGES
    ]


def all_challenge_ids() -> set[str]:
    return set(_BY_ID) | set(EXPERIMENT_CHALLENGE_IDS)


def _target_state(challenge: dict) -> Statevector:
    vector = np.zeros(2 ** challenge["qubits"], dtype=complex)
    for outcome, amplitude in challenge["target"].items():
        vector[int(outcome, 2)] = amplitude
    return Statevector(vector)


def check_build_challenge(challenge_id: str, qubits: int, gates: list[dict]) -> dict:
    challenge = _BY_ID.get(challenge_id)
    if challenge is None:
        raise NotFoundError("Challenge not found.")
    if qubits != challenge["qubits"]:
        raise InvalidInputError(f"This challenge uses exactly {challenge['qubits']} qubit(s).")
    if len(gates) > challenge["max_gates"]:
        raise InvalidInputError(f"Use at most {challenge['max_gates']} gates for this challenge.")
    disallowed = sorted({gate["name"] for gate in gates} - set(challenge["allowed_gates"]))
    if disallowed:
        raise InvalidInputError(
            f"Gates not allowed in this challenge: {', '.join(disallowed)}. "
            f"Use {', '.join(challenge['allowed_gates'])}."
        )

    state = custom_statevector(qubits, gates)
    if challenge["kind"] == "state":
        # |<target|state>|^2 ignores global phase, which no measurement can detect.
        score = float(abs(np.vdot(_target_state(challenge).data, state.data)) ** 2)
        passed = score >= FIDELITY_THRESHOLD
        message = (
            "Your circuit prepares the target state."
            if passed
            else "Not yet. Measured counts can match while relative phases differ; compare amplitudes."
            if score > 0.4
            else "Not yet. Step through your circuit on the Bloch spheres and compare with the goal."
        )
        metric = "fidelity"
    else:
        probabilities = state.probabilities_dict()
        outcomes = set(probabilities) | set(challenge["target"])
        distance = 0.5 * sum(
            abs(probabilities.get(key, 0.0) - challenge["target"].get(key, 0.0)) for key in outcomes
        )
        score = 1 - float(distance)
        passed = distance <= challenge["tolerance"]
        message = (
            "Your circuit produces the target probabilities."
            if passed
            else f"Not yet. Your ideal distribution is {distance:.1%} away from the goal."
        )
        metric = "distribution_match"
    return {
        "challenge_id": challenge_id,
        "passed": passed,
        "score": round(score, 6),
        "metric": metric,
        "message": message,
    }
