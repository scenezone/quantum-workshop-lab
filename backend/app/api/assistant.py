from fastapi import APIRouter, Request
from slowapi import Limiter

from app.ai.assistant_service import AssistantService
from app.rate_limit import limiter
from app.schemas import AssistantRequest

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


@router.post("/chat")
@limiter.limit("10/minute")
async def chat(request: Request, payload: AssistantRequest) -> dict:
    return await AssistantService.chat(
        [message.model_dump() for message in payload.messages],
        payload.lesson_id,
        payload.experiment_id,
        payload.result_context,
    )