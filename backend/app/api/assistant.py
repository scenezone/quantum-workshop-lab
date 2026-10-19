from fastapi import APIRouter, Request
from app.config import get_settings

from app.ai.assistant_service import AssistantService
from app.rate_limit import limiter
from app.schemas import AssistantRequest, AssistantResponse

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


@router.post("/chat", response_model=AssistantResponse)
@limiter.limit(lambda: f"{get_settings().llm_max_requests_per_minute}/minute")
async def chat(request: Request, payload: AssistantRequest) -> dict:
    return await AssistantService.chat(
        [message.model_dump() for message in payload.messages],
        payload.lesson_id,
        payload.experiment_id,
        payload.result_context,
    )
