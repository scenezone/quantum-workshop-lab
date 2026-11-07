from fastapi import APIRouter, Request

from app.database.models import (
    CustomCircuit,
    CustomCircuitRequest,
    EvolutionResponse,
    Experiment,
    ExperimentList,
    ExperimentResult,
    HardwareRequest,
    HardwareSubmission,
    JobStatusResponse,
    QasmImportRequest,
    SimulateRequest,
)
from app.quantum import simulator
from app.quantum.circuits import (
    all_experiments,
    custom_state_evolution,
    get_metadata,
    state_evolution,
)
from app.quantum.job_manager import JobManager
from app.quantum.qasm import import_qasm
from app.rate_limit import limiter

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


@router.get("", response_model=ExperimentList)
def list_experiments() -> dict:
    return {"experiments": all_experiments()}


@router.post("/simulate", response_model=ExperimentResult)
@limiter.limit("20/minute")
def simulate(request: Request, payload: SimulateRequest) -> dict:
    return simulator.run_simulation(
        payload.experiment_id, payload.shots, payload.noise_profile, payload.measurement_bases
    )


@router.post("/custom/simulate", response_model=ExperimentResult)
@limiter.limit("20/minute")
def simulate_custom_circuit(request: Request, payload: CustomCircuitRequest) -> dict:
    return simulator.run_custom_simulation(
        payload.qubits,
        payload.gate_dicts(),
        payload.shots,
        payload.noise_profile,
        payload.measurement_bases,
    )


@router.post("/custom/evolution", response_model=EvolutionResponse)
@limiter.limit("40/minute")
def custom_circuit_evolution(request: Request, payload: CustomCircuit) -> dict:
    return custom_state_evolution(payload.qubits, payload.gate_dicts())


@router.post("/custom/qasm", response_model=CustomCircuit, response_model_exclude_none=True)
@limiter.limit("20/minute")
def import_custom_qasm(request: Request, payload: QasmImportRequest) -> dict:
    return import_qasm(payload.source)


@router.post("/hardware", response_model=HardwareSubmission)
@limiter.limit("5/minute")
def submit_hardware(request: Request, payload: HardwareRequest) -> dict:
    tracking_token, status = JobManager.submit(
        payload.experiment_id, payload.shots, payload.idempotency_key
    )
    return {"tracking_id": tracking_token, "status": status}


@router.get("/jobs/{tracking_id}", response_model=JobStatusResponse)
@limiter.limit("60/minute")
def job_status(request: Request, tracking_id: str) -> dict:
    job = JobManager.get_job(tracking_id)
    return JobManager.to_response(job, tracking_id)


# Parameterized routes last, so "/custom/..." and "/jobs/..." are matched first.
@router.get("/{experiment_id}", response_model=Experiment)
def get_experiment(experiment_id: str) -> dict:
    return get_metadata(experiment_id)


@router.get("/{experiment_id}/evolution", response_model=EvolutionResponse)
def get_experiment_evolution(experiment_id: str) -> dict:
    return state_evolution(experiment_id)
