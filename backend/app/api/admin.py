import csv
import hmac
import io

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import Response

from app.config import get_settings
from app.database.models import SessionCreateRequest
from app.errors import FeatureDisabledError, UnauthorizedError
from app.rate_limit import limiter
from app.services.session_service import (
    SessionService,
    feedback_rows,
    feedback_summary,
    normalize_code,
)


def require_admin(authorization: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not settings.admin_enabled:
        raise FeatureDisabledError(
            "Facilitator tools are disabled. Set ADMIN_TOKEN on the backend to enable them."
        )
    scheme, _, token = (authorization or "").partition(" ")
    expected = settings.admin_token.strip().encode()
    if scheme.lower() != "bearer" or not hmac.compare_digest(token.strip().encode(), expected):
        raise UnauthorizedError()


router = APIRouter(prefix="/api/admin", tags=["facilitator"], dependencies=[Depends(require_admin)])


@router.get("/status")
@limiter.limit("30/minute")
def admin_status(request: Request) -> dict:
    return {"status": "ok"}


@router.post("/sessions")
@limiter.limit("30/minute")
def create_session(request: Request, payload: SessionCreateRequest) -> dict:
    return SessionService.create(payload.name)


@router.get("/sessions")
@limiter.limit("30/minute")
def list_sessions(request: Request) -> dict:
    return {"sessions": SessionService.list_active()}


@router.get("/sessions/{code}")
@limiter.limit("60/minute")
def session_dashboard(request: Request, code: str) -> dict:
    return SessionService.dashboard(code)


@router.get("/feedback")
@limiter.limit("30/minute")
def feedback(
    request: Request, session_code: str | None = Query(default=None, max_length=12)
) -> dict:
    return feedback_summary(normalize_code(session_code) if session_code else None)


@router.get("/feedback/export")
@limiter.limit("10/minute")
def export_feedback(
    request: Request, session_code: str | None = Query(default=None, max_length=12)
) -> Response:
    rows = feedback_rows(normalize_code(session_code) if session_code else None)
    buffer = io.StringIO()
    fields = ["created_at", "session_code", "rating", "clarity_rating", "completed_workshop"]
    writer = csv.DictWriter(buffer, fieldnames=[*fields, "comments"], extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        comment = row.get("comments") or ""
        # Neutralize spreadsheet formulas in free-text comments.
        if comment[:1] in {"=", "+", "-", "@"}:
            comment = f"'{comment}"
        writer.writerow({**{key: row.get(key) for key in fields}, "comments": comment})
    return Response(
        buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="workshop-feedback.csv"'},
    )
