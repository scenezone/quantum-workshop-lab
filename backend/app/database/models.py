from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.content.curriculum import ExperimentId
from app.quantum.catalog import (
    ANGLE_LIMIT,
    CUSTOM_GATES,
    MAX_CUSTOM_GATES,
    MAX_CUSTOM_QUBITS,
    MEASUREMENT_BASES,
    NOISE_PROFILE_IDS,
)

NoiseProfile = Literal[NOISE_PROFILE_IDS]
GateName = Literal[tuple(CUSTOM_GATES)]
MeasurementBasis = Literal[MEASUREMENT_BASES]


def _angle():
    return Field(default=None, ge=-ANGLE_LIMIT, le=ANGLE_LIMIT)


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


class AIWrittenFeedback(BaseModel):
    covered_points: list[str]
    missing_points: list[str]
    feedback: str


class PracticeFeedbackResponse(BaseModel):
    question_id: str
    kind: Literal["multiple_choice", "short_answer"]
    correct: bool | None = None
    correct_option_id: str | None = None
    explanation: str | None = None
    sample_answer: str | None = None
    key_points: list[str] | None = None
    ai_feedback: AIWrittenFeedback | None = None


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


class LessonList(BaseModel):
    lessons: list[Lesson]


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


class ExperimentList(BaseModel):
    experiments: list[Experiment]


class SimulateRequest(BaseModel):
    experiment_id: ExperimentId
    shots: int = Field(default=1024, ge=1)
    noise_profile: NoiseProfile = "ideal"
    # One basis per circuit qubit; only measured qubits are affected. Omit for Z.
    measurement_bases: list[MeasurementBasis] | None = Field(default=None, max_length=8)


class CustomGate(BaseModel):
    name: GateName
    qubits: list[int] = Field(min_length=1, max_length=3)
    angle: float | None = _angle()
    phi: float | None = _angle()
    lam: float | None = _angle()

    @model_validator(mode="after")
    def validate_gate(self):
        spec = CUSTOM_GATES[self.name]
        if len(self.qubits) != spec["qubits"] or len(set(self.qubits)) != len(self.qubits):
            raise ValueError("Gate has an invalid number of distinct qubits.")
        expected = {0: (), 1: ("angle",), 3: ("angle", "phi", "lam")}[spec["params"]]
        supplied = tuple(
            name for name in ("angle", "phi", "lam") if getattr(self, name) is not None
        )
        if supplied != expected:
            raise ValueError(
                "Rotation gates require their angles; other gates do not accept angles."
            )
        return self


class CustomCircuit(BaseModel):
    qubits: int = Field(ge=1, le=MAX_CUSTOM_QUBITS)
    gates: list[CustomGate] = Field(max_length=MAX_CUSTOM_GATES)

    @model_validator(mode="after")
    def validate_qubit_indices(self):
        if any(index < 0 or index >= self.qubits for gate in self.gates for index in gate.qubits):
            raise ValueError("Gate qubit indices must be inside this circuit.")
        return self

    def gate_dicts(self) -> list[dict]:
        return [gate.model_dump(exclude_none=True) for gate in self.gates]


class CustomCircuitRequest(CustomCircuit):
    shots: int = Field(default=1024, ge=1)
    noise_profile: NoiseProfile = "ideal"
    measurement_bases: list[MeasurementBasis] | None = Field(
        default=None, max_length=MAX_CUSTOM_QUBITS
    )


class QasmImportRequest(BaseModel):
    source: str = Field(min_length=1, max_length=20000)


class HardwareRequest(BaseModel):
    experiment_id: ExperimentId
    shots: int = Field(default=1024, ge=1)
    idempotency_key: str = Field(min_length=16, max_length=128)


class HardwareSubmission(BaseModel):
    tracking_id: str
    status: str


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
    transpiled_depth: int | None = None
    two_qubit_gate_count: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Amplitude(BaseModel):
    outcome: str
    real: float
    imag: float
    probability: float
    phase_degrees: float


class ExperimentResult(BaseModel):
    experiment_id: str
    backend: Literal["aer_simulator", "ibm_quantum", "ibm_quantum_recorded"]
    backend_name: str | None = None
    shots: int
    noise_profile: NoiseProfile | None = None
    measurement_bases: list[MeasurementBasis] | None = None
    counts: dict[str, int]
    observed_probabilities: dict[str, float]
    ideal_probabilities: dict[str, float]
    provider_job_id: str | None = None
    tracking_id: str | None = None
    recorded_at: str | None = None
    amplitudes: list[Amplitude] | None = None


class BlochVector(BaseModel):
    qubit: int
    x: float
    y: float
    z: float
    length: float


class EvolutionStep(BaseModel):
    step: int
    gate: str
    explanation: str
    qubits: list[BlochVector]


class EvolutionResponse(BaseModel):
    experiment_id: str
    qubits: int
    steps: list[EvolutionStep]


class NoiseProfileInfo(BaseModel):
    id: NoiseProfile
    label: str
    kind: Literal["preset", "device"]


class PublicConfig(BaseModel):
    hardware_enabled: bool
    max_simulator_shots: int
    max_hardware_shots: int
    default_shots: int
    database_enabled: bool
    feedback_enabled: bool
    sessions_enabled: bool
    live_ai_enabled: bool
    noise_profiles: list[NoiseProfileInfo]


class HardwareStatus(BaseModel):
    hardware_enabled: bool
    configured_accounts: int
    daily_limit: int
    submitted_today: int
    remaining_today: int
    active_jobs: int
    active_limit: int
    max_shots: int


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
    session_code: str | None = Field(default=None, min_length=4, max_length=12)


class ChallengeCheckResponse(BaseModel):
    challenge_id: str
    passed: bool
    score: float
    metric: Literal["fidelity", "distribution_match"]
    message: str


class BuildChallenge(BaseModel):
    challenge_id: str
    title: str
    objective: str
    difficulty: Literal["beginner", "intermediate", "advanced"]
    qubits: int
    allowed_gates: list[GateName]
    max_gates: int
    hint: str
    kind: Literal["state", "distribution"]


class BuildChallengeList(BaseModel):
    challenges: list[BuildChallenge]
    experiment_challenge_ids: list[str]


class ChshRequest(BaseModel):
    shots: int = Field(default=1024, ge=1)
    noise_profile: NoiseProfile = "ideal"
    # Measurement directions in the X-Z plane, in radians. Defaults maximize S.
    alice: tuple[float, float] | None = None
    bob: tuple[float, float] | None = None


class ChshSetting(BaseModel):
    alice_angle: float
    bob_angle: float
    counts: dict[str, int]
    correlation: float
    ideal_correlation: float


class ChshResponse(BaseModel):
    shots: int
    noise_profile: NoiseProfile
    backend_name: str
    settings: list[ChshSetting]
    s_value: float
    s_standard_error: float
    ideal_s_value: float
    classical_bound: float
    quantum_bound: float


class VqeRequest(BaseModel):
    hamiltonian: Literal["zx", "h2"] = "zx"
    iterations: int = Field(default=20, ge=1, le=40)
    learning_rate: float = Field(default=0.4, gt=0, le=1.5)
    shots: int = Field(default=1024, ge=1)
    noise_profile: NoiseProfile = "ideal"
    initial_parameters: list[float] | None = Field(default=None, max_length=2)


class VqeIteration(BaseModel):
    iteration: int
    parameters: list[float]
    energy: float
    exact_energy: float


class VqeLandscapePoint(BaseModel):
    theta: float
    energy: float


class VqeResponse(BaseModel):
    hamiltonian: str
    description: str
    terms: list[tuple[str, float]]
    parameter_count: int
    ground_energy: float
    final_parameters: list[float]
    final_energy: float
    trace: list[VqeIteration]
    landscape: list[VqeLandscapePoint]
    backend_name: str


class SessionCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class SessionJoinRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=40)


class SessionProgressRequest(BaseModel):
    participant_id: str = Field(min_length=8, max_length=64)
    participant_token: str = Field(min_length=16, max_length=128)
    completed_lessons: list[str] = Field(default_factory=list, max_length=100)
    completed_challenges: list[str] = Field(default_factory=list, max_length=100)
    practice_correct: int = Field(default=0, ge=0, le=10000)
    practice_attempted: int = Field(default=0, ge=0, le=10000)
