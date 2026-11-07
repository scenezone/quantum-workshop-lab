from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.ai.assistant_service import AssistantService
from app.config import get_settings
from app.database.models import AssistantRequest, AssistantResponse
from app.rate_limit import limiter

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


def _limit() -> str:
    return f"{get_settings().llm_max_requests_per_minute}/minute"


@router.post("/chat", response_model=AssistantResponse)
@limiter.limit(_limit)
async def chat(request: Request, payload: AssistantRequest) -> dict:
    return await AssistantService.chat(
        [message.model_dump() for message in payload.messages],
        payload.lesson_id,
        payload.experiment_id,
        payload.result_context,
        payload.mode,
    )


@router.post("/chat/stream")
@limiter.limit(_limit)
async def chat_stream(request: Request, payload: AssistantRequest) -> StreamingResponse:
    """Stream the reply as server-sent events: meta, delta..., done."""
    events = AssistantService.stream(
        [message.model_dump() for message in payload.messages],
        payload.lesson_id,
        payload.experiment_id,
        payload.result_context,
        payload.mode,
    )
    return StreamingResponse(
        events,
        media_type="text/event-stream",
        # Nginx would otherwise buffer the whole response before sending it.
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
