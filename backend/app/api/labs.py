from fastapi import APIRouter, Request

from app.database.models import ChshRequest, ChshResponse, VqeRequest, VqeResponse
from app.quantum.labs import run_chsh, run_vqe
from app.rate_limit import limiter

router = APIRouter(prefix="/api/labs", tags=["labs"])


@router.post("/chsh", response_model=ChshResponse)
@limiter.limit("20/minute")
def chsh(request: Request, payload: ChshRequest) -> dict:
    return run_chsh(payload.shots, payload.noise_profile, payload.alice, payload.bob)


@router.post("/vqe", response_model=VqeResponse)
@limiter.limit("6/minute")
def vqe(request: Request, payload: VqeRequest) -> dict:
    return run_vqe(
        payload.hamiltonian,
        payload.iterations,
        payload.learning_rate,
        payload.shots,
        payload.noise_profile,
        payload.initial_parameters,
    )
