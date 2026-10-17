from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import APIRouter,Request
from app.database.mongodb import Mongo
from app.errors import NotFoundError
from app.quantum import simulator
from app.quantum.circuits import all_experiments, get_metadata
from app.quantum.job_manager import JobManager
from app.rate_limit import limiter
from app.schemas import HardwareRequest, SimulateRequest

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


@router.get("")
def list_experiments() -> dict:
    return {"experiments": all_experiments()}


@router.get("/{experiment_id}")
def get_experiment(experiment_id: str) -> dict:
    try:
        return get_metadata(experiment_id)
    except NotFoundError:
        raise


@router.post("/simulate")
@limiter.limit("20/minute")
def simulate(request: Request, payload: SimulateRequest) -> dict:
    return simulator.run_simulation(payload.experiment_id, payload.shots)


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
    return JobManager.to_response(job)