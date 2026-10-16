import logging

from app.database.mongodb import Mongo

logger = logging.getLogger(__name__)

LESSONS = [
    {
        "lesson_id": "intro-quantum",
        "title": "Introduction to Quantum Computing",
        "description": "What quantum computers are and why they differ from classical computers.",
        "difficulty": "beginner",
        "order": 1,
        "learning_objectives": [
            "Explain the difference between classical and quantum computing",
            "Describe a qubit and its two basis states",
            "Identify why quantum computers are not simply faster classical computers",
        ],
        "related_experiments": ["superposition"],
        "content": """A classical computer stores information in **bits**, which are either `0` or `1`.

A quantum computer uses **qubits**. A qubit has two basis states, written \(|0⟩\) and \(|1⟩\). Before measurement, it can exist in a *superposition* of both.

Quantum computers are not simply faster laptops. They are useful when a problem can be expressed so that quantum effects—superposition, interference, and entanglement—help compute a result.

**Knowledge check:** Which statement is true?

- A classical bit can be both 0 and 1 at the same time.
- A qubit has basis states \(|0⟩\) and \(|1⟩\), and may be in a superposition before measurement. ✅
- Quantum computers replace all classical computers.""",
    },
    {
        "lesson_id": "superposition",
        "title": "Superposition and the Hadamard Gate",
        "description": "Create an equal superposition with the Hadamard gate.",
        "difficulty": "beginner",
        "order": 2,
        "learning_objectives": [
            "Explain superposition",
            "Describe what a Hadamard gate does",
            "Predict ideal measurement probabilities",
        ],
        "related_experiments": ["superposition", "interference"],
        "content": """A qubit begins in \(|0⟩\). Applying a **Hadamard gate** (`H`) creates an equal superposition:

\[
|0⟩ \\xrightarrow{H} \\frac{|0⟩ + |1⟩}{\\sqrt{2}}
\]

When measured once, the result is either `0` or `1`; a single outcome is random. Across many shots, an ideal device produces `0` and `1` about 50% each.

**Knowledge check:** After `H` on \(|0⟩\), what are the ideal probabilities?

- 100% `0`
- 50% `0`, 50% `1` ✅
- 25% `0`, 75% `1`""",
    },
    {
        "lesson_id": "entanglement",
        "title": "Entanglement and Bell States",
        "description": "Use H and CX to create correlated two-qubit measurements.",
        "difficulty": "beginner",
        "order": 3,
        "learning_objectives": [
            "Create a Bell state",
            "Explain correlated measurement outcomes",
            "Distinguish entanglement from independent randomness",
        ],
        "related_experiments": ["bell_entanglement"],
        "content": """Start with two qubits in \(|00⟩\). Apply `H` to qubit 0, then apply `CX` with qubit 0 as control and qubit 1 as target:

\[
|00⟩ \\xrightarrow{H \\otimes I} \\frac{|00⟩ + |10⟩}{\\sqrt{2}}
\\xrightarrow{CX} \\frac{|00⟩ + |11⟩}{\\sqrt{2}}
\]

The result is a Bell state. Measurement yields `00` or `11`, each ideally with probability 50%. The outcomes are correlated: you never see `01` or `10` in the ideal circuit.

This correlation is stronger than two independent coins: measuring one qubit tells you something definite about the other.

**Knowledge check:** Which outcomes are expected ideally?

- `00` and `11` ✅
- `01` and `10`
- All four equally""",
    },
    {
        "lesson_id": "gates",
        "title": "Quantum Gates",
        "description": "X, Y, Z, Hadamard, CNOT, and measurement.",
        "difficulty": "beginner",
        "order": 4,
        "learning_objectives": [
            "Identify common single- and two-qubit gates",
            "Explain measurement",
            "Interpret circuit diagrams",
        ],
        "related_experiments": ["superposition", "bell_entanglement", "interference"],
        "content": """- **X**: flips \(|0⟩\) to \(|1⟩\) and \(|1⟩\) to \(|0⟩\).
- **Y**: rotates a qubit around the Y axis of the Bloch sphere.
- **Z**: applies a phase flip; it changes relative phase rather than measurement probabilities for basis states.
- **H**: creates or removes superposition.
- **CX / CNOT**: flips the target qubit when the control qubit is `1`; essential for entanglement.
- **Measure**: converts a qubit state into a classical bit.

Circuits are read left to right. Each horizontal line is a qubit wire; boxes are gates; meters represent measurement.

**Knowledge check:** Which gate commonly creates superposition?

- X
- H ✅
- CX""",
    },
    {
        "lesson_id": "hardware-noise",
        "title": "Quantum Hardware and Noise",
        "description": "Why real quantum results differ from ideal simulations.",
        "difficulty": "beginner",
        "order": 5,
        "learning_objectives": [
            "Explain hardware noise",
            "Compare ideal and real results",
            "Interpret small deviations from expected probabilities",
        ],
        "related_experiments": ["superposition", "bell_entanglement", "interference"],
        "content": """Real quantum processors are physical devices. Their qubits and gates are imperfect, so results can include:

- **Gate errors**: a gate does not perform its intended transformation perfectly.
- **Measurement errors**: a `0` may occasionally be read as `1`, or vice versa.
- **Decoherence**: qubits lose quantum information over time.

Therefore, a Bell-state circuit may produce a few `01` or `10` outcomes on hardware even though the ideal circuit predicts none. Small deviations are normal; the goal is to compare the observed distribution with the ideal distribution.

**Knowledge check:** Why might real hardware produce `01` in a Bell experiment?

- Because the ideal Bell state contains `01`
- Because hardware noise can cause errors ✅
- Because Qiskit changes the circuit randomly""",
    },
]

EXPERIMENTS = {
    "superposition": {
        "experiment_id": "superposition",
        "title": "Superposition",
        "description": "Put one qubit into an equal superposition of |0⟩ and |1⟩ using a Hadamard gate.",
        "qubits": 1,
        "classical_bits": 1,
        "gates": [
            {"name": "H", "qubits": [0], "explanation": "Creates an equal superposition of |0⟩ and |1⟩."},
            {"name": "Measure", "qubits": [0], "explanation": "Reads the qubit as a classical bit."},
        ],
        "qiskit_code": "qc = QuantumCircuit(1, 1)\nqc.h(0)\nqc.measure(0, 0)",
        "ideal_probabilities": {"0": 0.5, "1": 0.5},
        "interpretation": "A single shot is unpredictable, but many shots should approach 50% `0` and 50% `1`.",
        "next_experiment": "bell_entanglement",
    },
    "bell_entanglement": {
        "experiment_id": "bell_entanglement",
        "title": "Bell-State Entanglement",
        "description": "Create an entangled pair whose measurements are perfectly correlated.",
        "qubits": 2,
        "classical_bits": 2,
        "gates": [
            {"name": "H", "qubits": [0], "explanation": "Puts qubit 0 into superposition."},
            {"name": "CX", "qubits": [0, 1], "explanation": "Entangles qubit 1 with qubit 0."},
            {"name": "Measure", "qubits": [0, 1], "explanation": "Measures both qubits."},
        ],
        "qiskit_code": "qc = QuantumCircuit(2, 2)\nqc.h(0)\nqc.cx(0, 1)\nqc.measure([0, 1], [0, 1])",
        "ideal_probabilities": {"00": 0.5, "01": 0.0, "10": 0.0, "11": 0.5},
        "interpretation": "The ideal Bell state produces only `00` and `11`. Hardware noise can introduce a small number of `01` or `10` outcomes.",
        "next_experiment": "interference",
    },
    "interference": {
        "experiment_id": "interference",
        "title": "Quantum Interference",
        "description": "Apply two Hadamard gates and observe constructive interference back to |0⟩.",
        "qubits": 1,
        "classical_bits": 1,
        "gates": [
            {"name": "H", "qubits": [0], "explanation": "Creates superposition."},
            {"name": "H", "qubits": [0], "explanation": "Interferes the paths, returning the qubit to |0⟩."},
            {"name": "Measure", "qubits": [0], "explanation": "Reads the qubit."},
        ],
        "qiskit_code": "qc = QuantumCircuit(1, 1)\nqc.h(0)\nqc.h(0)\nqc.measure(0, 0)",
        "ideal_probabilities": {"0": 1.0, "1": 0.0},
        "interpretation": "The two Hadamard gates interfere constructively for `0` and destructively for `1`, so an ideal simulator returns `0` every time.",
        "next_experiment": "superposition",
    },
}


def seed_database() -> None:
    db = Mongo.db()
    for lesson in LESSONS:
        db.lessons.update_one(
            {"lesson_id": lesson["lesson_id"]},
            {"$set": lesson, "$setOnInsert": {"created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc)}},
            upsert=True,
        )
    for experiment in EXPERIMENTS.values():
        db.experiments.update_one(
            {"experiment_id": experiment["experiment_id"]},
            {"$set": experiment},
            upsert=True,
        )
    logger.info("Database seed complete.")