from datetime import datetime
from typing import Any,Literal

from pydantic import BaseModel,Field


class Lesson(BaseModel):
    lesson_id:str
    title:str
    description:str
    content:str
    difficulty: Literal["beginner","intermediate"]
    learning_objectives: list[str]
    related_experiments: list[str]
    order: int

class ExperimentGate(BaseModel):
    name: str
    qubits: list[int]
    explanation: str


class Experiment(BaseModel):
    experiment_id:Literal["superposition",'bell_entanglement',"interference"]
    title:str
    description:str
    qubits:int
    classical_bits:int
    gates:list[ExperimentGate]
    qiskit_code:str
    ideal_probabilities: dict[str, float]
    interpretation: str
    next_experiment: str | None = None

class SimulateRequest(BaseModel):
    experiment_id: Literal["superposition", "bell_entanglement", "interference"]
    shots: int = Field(default=1024, ge=1, le=10000)

class HardwareRequest(BaseModel):
    experiment_id: Literal["superposition", "bell_entanglement", "interference"]
    shots: int = Field(default=1024, ge=1, le=4096)
    idempotency_key: str = Field(min_length=16, max_length=128)

class JobStatusResponse(BaseModel):
    tracking_id:str
    status:Literal[
        "queued", "running", "completed", "failed", "cancelled", "unknown"
    ]
    experiment_id:str
    backend_name:str|None=None
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
    counts: dict[str, int]
    observed_probabilities: dict[str, float]
    ideal_probabilities: dict[str, float]
    provider_job_id: str | None = None
    tracking_id: str | None = None

class AssistantMessage(BaseModel):
    role:Literal["user","assistant"]
    content: str = Field(min_lenght=1,max_length=2000)

class AssistantRequest(BaseModel):
    messages: list[AssistantMessage] = Field(min_length=1, max_length=12)
    lesson_id: str | None = None
    experiment_id: str | None = None
    result_context: dict[str, Any] | None = None


class AssistantResponse(BaseModel):
    reply: str
    source: Literal["llm", "fallback"]


class FeedbackRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    clarity_rating: int = Field(ge=1, le=5)
    completed_workshop: bool
    comments: str | None = Field(default=None, max_length=1000)