from fastapi import APIRouter, Request

from app.content.challenges import (
    EXPERIMENT_CHALLENGE_IDS,
    check_build_challenge,
    public_challenges,
)
from app.database.models import BuildChallengeList, ChallengeCheckResponse, CustomCircuit
from app.rate_limit import limiter

router = APIRouter(prefix="/api/challenges", tags=["challenges"])


@router.get("", response_model=BuildChallengeList)
def list_challenges() -> dict:
    return {
        "challenges": public_challenges(),
        "experiment_challenge_ids": list(EXPERIMENT_CHALLENGE_IDS),
    }


@router.post("/{challenge_id}/check", response_model=ChallengeCheckResponse)
@limiter.limit("30/minute")
def check_challenge(request: Request, challenge_id: str, payload: CustomCircuit) -> dict:
    return check_build_challenge(challenge_id, payload.qubits, payload.gate_dicts())
