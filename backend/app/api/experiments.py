from fastapi import APIRouter, Request

from app.quantum import simulator
from app.quantum.circuits import all_experiments, get_metadata, state_evolution
from app.quantum.job_manager import JobManager
from app.rate_limit import limiter
from app.schemas import CustomCircuitRequest, HardwareRequest, SimulateRequest

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


@router.get("")
def list_experiments() -> dict:
    return {"experiments": all_experiments()}


@router.get("/{experiment_id}")
def get_experiment(experiment_id: str) -> dict:
    return get_metadata(experiment_id)


@router.get("/{experiment_id}/evolution")
def get_experiment_evolution(experiment_id: str) -> dict:
    return state_evolution(experiment_id)


@router.post("/simulate")
@limiter.limit("20/minute")
def simulate(request: Request, payload: SimulateRequest) -> dict:
    return simulator.run_simulation(payload.experiment_id, payload.shots, payload.noise_profile)


@router.post("/custom/simulate")
@limiter.limit("20/minute")
def simulate_custom_circuit(request: Request, payload: CustomCircuitRequest) -> dict:
    return simulator.run_custom_simulation(
        payload.qubits,
        [gate.model_dump() for gate in payload.gates],
        payload.shots,
        payload.noise_profile,
    )


@router.post("/hardware")
@limiter.limit("5/minute")
def submit_hardware(request: Request, payload: HardwareRequest) -> dict:
    tracking_token, status = JobManager.submit(
        payload.experiment_id, payload.shots, payload.idempotency_key
    )
    return {"tracking_id": tracking_token, "status": status}


@router.get("/jobs/{tracking_id}")
@limiter.limit("60/minute")
def job_status(request: Request, tracking_id: str) -> dict:
    job = JobManager.get_job(tracking_id)
    return JobManager.to_response(job, tracking_id)
