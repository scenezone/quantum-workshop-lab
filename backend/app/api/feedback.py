from fastapi import APIRouter, Request

from app.database.models import FeedbackRequest
from app.database.mongodb import Mongo, utcnow
from app.errors import NotFoundError
from app.rate_limit import limiter
from app.services.session_service import SessionService

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("")
@limiter.limit("5/minute")
def submit_feedback(request: Request, payload: FeedbackRequest) -> dict:
    session_code = None
    if payload.session_code:
        try:
            session_code = SessionService.get(payload.session_code)["code"]
        except NotFoundError:
            session_code = None  # An ended session should not block anonymous feedback.
    Mongo.db().feedback.insert_one(
        {
            "rating": payload.rating,
            "clarity_rating": payload.clarity_rating,
            "completed_workshop": payload.completed_workshop,
            "comments": payload.comments,
            "session_code": session_code,
            "created_at": utcnow(),
        }
    )
    return {"status": "received"}
