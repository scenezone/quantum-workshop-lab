from fastapi import APIRouter, Request

from app.database.models import SessionJoinRequest, SessionProgressRequest
from app.rate_limit import limiter
from app.services.session_service import SessionService

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("/{code}")
@limiter.limit("30/minute")
def get_session(request: Request, code: str) -> dict:
    return SessionService.get(code)


@router.post("/{code}/join")
@limiter.limit("10/minute")
def join_session(request: Request, code: str, payload: SessionJoinRequest) -> dict:
    return SessionService.join(code, payload.nickname)


@router.put("/{code}/progress")
@limiter.limit("60/minute")
def update_progress(request: Request, code: str, payload: SessionProgressRequest) -> dict:
    return SessionService.update_progress(code, payload.model_dump())
