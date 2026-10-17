from datetime import datetime, timezone

from fastapi import APIRouter, Request
from slowapi import Limiter

from app.database.mongodb import Mongo
from app.rate_limit import limiter
from app.schemas import FeedbackRequest

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("")
@limiter.limit("5/minute")
def submit_feedback(request: Request, payload: FeedbackRequest) -> dict:
    Mongo.db().feedback.insert_one(
        {
            "rating": payload.rating,
            "clarity_rating": payload.clarity_rating,
            "completed_workshop": payload.completed_workshop,
            "comments": payload.comments,
            "created_at": datetime.now(timezone.utc),
        }
    )
    return {"status": "received"}