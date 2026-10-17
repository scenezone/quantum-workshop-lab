import logging
import httpx

from app.ai.knowledge_base import build_context
from app.ai.prompts import SYSTEM_PROMPT
from app.config import get_settings
from app.errors import ExternalServiceError


logger = logging.getLogger(__name__)


FALLBACK = (
    "I cannot reach the AI service right now. "
    "For quantum questions, remember: a qubit can be in a superposition of |0⟩ and |1⟩; "
    "a Hadamard gate creates superposition; a CNOT can entangle two qubits; "
    "and real hardware results can differ from ideal simulations because of noise."
)

class AssistantService:

    @staticmethod
    async def chat(
        messages: list[dict],
        lesson_id: str|None,
        experiment_id: str|None,
        result_context:dict|None,
    )->dict:
        settings = get_settings()
        context = build_context(lesson_id,experiment_id,result_context)
        payload_messages = [{"role":"system","content":f"{SYSTEM_PROMPT}\n\nCONTEXT:\n{context}"}]
        payload_messages.extent(
            {"role":message["role"],"content":message['content']} for message in messages
        )

        if not settings.llm_api_key:
            return {'reply':FALLBACK,"source":"fallback"}

        try:
            async with httpx.AsyncClinet(timeout=settings.llm_timeout_seconds) as client:
                response = await client.post(
                    f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                    headers={'Authorization':f"Bearer {settings.llm_api_key}"},
                    json={
                        "model": settings.llm_model,
                        "messages": payload_messages,
                        "temperature": 0.2,
                        "max_tokens": 700,
                    }
                )
                response.raise_for_status()
                data = response.json()
                reply = data["choices"][0]['message']['content'].strip()
                return {'reply':reply,'source':"llm"}

        except httpx.TimeoutException:
            logger.warning("LLM timeout")
        except httpx.HTTPStatusError as exc:
            logger.warning("LLM HTTP error: %s", exc.response.status_code)
        except Exception:
            logger.exception("LLM request failed")

        return {"reply": FALLBACK, "source": "fallback"}