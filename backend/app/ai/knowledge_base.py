import json
import logging
import re

from pymongo.errors import PyMongoError

from app.content.curriculum import EXPERIMENTS, LESSONS
from app.database.mongodb import Mongo
from app.errors import ExternalServiceError, NotFoundError
from app.quantum.circuits import get_metadata

logger = logging.getLogger(__name__)

WORKSHOP_OVERVIEW = (
    "WORKSHOP BASICS: A qubit has basis states |0> and |1> and can be in a normalized "
    "superposition before measurement. H applied to |0> gives equal measurement probabilities. "
    "H followed by CX(0,1) creates the Bell state (|00> + |11>)/sqrt(2). "
    "Two H gates return a qubit to its initial state by interference. Shots are repeated "
    "circuit executions. Finite samples fluctuate; real devices also have gate, readout, "
    "and decoherence errors. Advanced labs cover phase kickback, GHZ coherence, a fixed balanced "
    "Deutsch-Jozsa oracle, two-qubit Grover search for 11, QFT phase encoding of 01, coherent "
    "deferred-measurement teleportation, and a three-qubit bit-flip correction demonstration. "
    "QFT counts alone do not reveal phase; fixed circuits do not run a variational optimizer. "
    "Results use Qiskit's displayed bit order, highest bit index first."
)

TOPICS = [
    (("grover", "amplification", "marked item"), "grover-search"),
    (("deutsch", "balanced oracle"), "deutsch-jozsa"),
    (("fourier", "qft", "phase estimation"), "quantum-fourier-transform"),
    (("teleport", "feed-forward", "deferred measurement"), "quantum-teleportation"),
    (
        ("syndrome", "repetition", "error correction", "stabilizer", "bit flip"),
        "quantum-error-correction",
    ),
    (("ghz", "multipartite", "coherence"), "multipartite-entanglement"),
    (("kickback",), "phase-kickback"),
    (("vqe", "variational", "optimizer", "parameter shift"), "variational-methods"),
    (("amplitude", "bloch", "born rule", "global phase", "relative phase"), "complex-amplitudes"),
    (("qubit", "classical", "quantum computing"), "intro-quantum"),
    (("hadamard", "superposition", "50/50"), "superposition"),
    (("entangle", "bell", "cnot", "cx"), "entanglement"),
    (("noise", "hardware", "error", "decoherence"), "hardware-noise"),
    (("gate", "measure"), "gates"),
]


def find_lesson_id(
    question: str, lesson_id: str | None = None, experiment_id: str | None = None
) -> str | None:
    selected = lesson_id or EXPERIMENTS.get(experiment_id, {}).get("lesson_id")
    if selected and re.search(r"\b(current|this|these|that|my|our)\b", question.lower()):
        return selected
    matched = next(
        (topic for keywords, topic in TOPICS if any(word in question.lower() for word in keywords)),
        None,
    )
    return matched or selected


def build_context(
    lesson_id: str | None,
    experiment_id: str | None,
    result_context: dict | None,
    question: str = "",
) -> str:
    sections: list[str] = [WORKSHOP_OVERVIEW]

    related_id = find_lesson_id(question)
    lesson_id = lesson_id or EXPERIMENTS.get(experiment_id, {}).get("lesson_id") or related_id

    if lesson_id:
        try:
            lesson = Mongo.db().lessons.find_one({"lesson_id": lesson_id})
        except (PyMongoError, ExternalServiceError):
            logger.warning("Using bundled lesson context while the database is unavailable")
            lesson = None
        if not lesson:
            lesson = next((item for item in LESSONS if item["lesson_id"] == lesson_id), None)
        if lesson:
            sections.append(
                f"LESSON: {lesson['title']}\nDifficulty: {lesson.get('difficulty', 'beginner')}\n"
                f"Learning objectives: {lesson.get('learning_objectives', [])}\n{lesson['content'][:3500]}"
            )

    if related_id and related_id != lesson_id:
        related = next((item for item in LESSONS if item["lesson_id"] == related_id), None)
        if related:
            sections.append(f"RELATED LESSON: {related['title']}\n{related['content'][:3500]}")

    if experiment_id:
        try:
            metadata = get_metadata(experiment_id)
            sections.append(
                "EXPERIMENT:\n"
                f"ID: {experiment_id}\n"
                f"Title: {metadata['title']}\n"
                f"Difficulty: {metadata['difficulty']}\n"
                f"Qubits: {metadata['qubits']}\n"
                f"Description: {metadata['description']}\n"
                f"Ideal probabilities: {metadata['ideal_probabilities']}\n"
                f"Interpretation: {metadata['interpretation']}\n"
                f"Circuit: {metadata['qiskit_code']}\n"
                f"Gate walkthrough: {json.dumps(metadata['gates'], ensure_ascii=True)[:3500]}"
            )
        except NotFoundError:
            pass

    if result_context:
        safe_keys = {
            "backend",
            "backend_name",
            "shots",
            "counts",
            "observed_probabilities",
            "ideal_probabilities",
            "status",
            "provider_job_id",
            "amplitudes",
        }
        filtered = {key: result_context[key] for key in safe_keys if key in result_context}
        sections.append("RESULT CONTEXT:\n" + json.dumps(filtered, ensure_ascii=True)[:10000])

    return "\n\n".join(sections) if sections else "No additional workshop context was provided."
