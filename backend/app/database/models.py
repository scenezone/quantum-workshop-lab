from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.content.curriculum import ExperimentId


class PracticeOption(BaseModel):
    option_id: str
    text: str


class PracticeQuestion(BaseModel):
    question_id: str
    kind: Literal["multiple_choice", "short_answer"]
    prompt: str
    options: list[PracticeOption] = Field(default_factory=list)


class PracticeAnswer(BaseModel):
    question_id: str = Field(min_length=1, max_length=100)
    option_id: str | None = Field(default=None, min_length=1, max_length=16)
    answer: str | None = Field(default=None, min_length=1, max_length=2000)


class Lesson(BaseModel):
    lesson_id: str
    title: str
    description: str
    content: str
    difficulty: Literal["beginner", "intermediate", "advanced"]
    learning_objectives: list[str]
    related_experiments: list[str]
    order: int
    prerequisites: list[str] = Field(default_factory=list)
    references: list[dict[str, str]] = Field(default_factory=list)
    practice_questions: list[PracticeQuestion] = Field(default_factory=list)


class ExperimentGate(BaseModel):
    name: str
    qubits: list[int]
    explanation: str
    classical_bits: list[int] | None = None
    angle: float | None = None
    label: str | None = None


class Experiment(BaseModel):
    experiment_id: ExperimentId
    difficulty: Literal["beginner", "intermediate", "advanced"]
    lesson_id: str
    title: str
    description: str
    qubits: int
    classical_bits: int
    gates: list[ExperimentGate]
    qiskit_code: str
    ideal_probabilities: dict[str, float]
    interpretation: str
    next_experiment: str | None = None


class SimulateRequest(BaseModel):
    experiment_id: ExperimentId
    shots: int = Field(default=1024, ge=1)
    noise_profile: Literal["ideal", "low", "medium", "high"] = "ideal"


class CustomGate(BaseModel):
    name: Literal["H", "X", "Y", "Z", "S", "T", "RX", "RY", "RZ", "CX", "CZ", "SWAP"]
    qubits: list[int] = Field(min_length=1, max_length=2)
    angle: float | None = Field(default=None, ge=-6.283185307179586, le=6.283185307179586)

    @model_validator(mode="after")
    def validate_gate(self):
        two_qubit = self.name in {"CX", "CZ", "SWAP"}
        if len(self.qubits) != (2 if two_qubit else 1) or len(set(self.qubits)) != len(self.qubits):
            raise ValueError("Gate has an invalid number of distinct qubits.")
        rotating = self.name in {"RX", "RY", "RZ"}
        if rotating != (self.angle is not None):
            raise ValueError("Rotation gates require an angle; other gates do not accept one.")
        return self


class CustomCircuitRequest(BaseModel):
    qubits: int = Field(ge=1, le=3)
    gates: list[CustomGate] = Field(max_length=30)
    shots: int = Field(default=1024, ge=1)
    noise_profile: Literal["ideal", "low", "medium", "high"] = "ideal"

    @model_validator(mode="after")
    def validate_qubit_indices(self):
        if any(index < 0 or index >= self.qubits for gate in self.gates for index in gate.qubits):
            raise ValueError("Gate qubit indices must be inside this circuit.")
        return self


class HardwareRequest(BaseModel):
    experiment_id: ExperimentId
    shots: int = Field(default=1024, ge=1)
    idempotency_key: str = Field(min_length=16, max_length=128)


class JobStatusResponse(BaseModel):
    tracking_id: str
    status: Literal["queued", "running", "completed", "failed", "cancelled", "unknown"]
    experiment_id: str
    backend_name: str | None = None
    provider_job_id: str | None = None
    shots: int
    counts: dict[str, int] | None = None
    observed_probabilities: dict[str, float] | None = None
    ideal_probabilities: dict[str, float]
    error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ExperimentResult(BaseModel):
    experiment_id: str
    backend: Literal["aer_simulator", "ibm_quantum"]
    backend_name: str | None = None
    shots: int
    noise_profile: Literal["ideal", "low", "medium", "high"] | None = None
    counts: dict[str, int]
    observed_probabilities: dict[str, float]
    ideal_probabilities: dict[str, float]
    provider_job_id: str | None = None
    tracking_id: str | None = None
    amplitudes: list[dict[str, Any]] | None = None


class AssistantMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=20000)

    @model_validator(mode="after")
    def validate_question_length(self):
        if self.role == "user" and len(self.content) > 2000:
            raise ValueError("Questions must be at most 2000 characters")
        return self


class AssistantRequest(BaseModel):
    messages: list[AssistantMessage] = Field(min_length=1, max_length=12)
    lesson_id: str | None = None
    experiment_id: str | None = None
    result_context: dict[str, Any] | None = None
    mode: Literal["explain", "hint", "quiz"] = "explain"


class AssistantResponse(BaseModel):
    reply: str
    source: Literal["llm", "fallback"]
    notice: str | None = None


class FeedbackRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    clarity_rating: int = Field(ge=1, le=5)
    completed_workshop: bool
    comments: str | None = Field(default=None, max_length=1000)
