import asyncio
import logging
from urllib.parse import urlsplit

import httpx

from app.ai.knowledge_base import build_context, find_lesson_id
from app.ai.prompts import SYSTEM_PROMPT
from app.config import get_settings
from app.content.curriculum import EXPERIMENTS, LESSONS

logger = logging.getLogger(__name__)

FALLBACK_NOTICE = (
    "Live AI is currently unavailable. This explanation comes from the workshop guide."
)


def guide_reply(
    question: str, lesson_id: str | None, experiment_id: str | None, result_context: dict | None
) -> str:
    question = question.lower()
    overview = "overview" in question
    result_summary = None
    if result_context and any(
        word in question for word in ("result", "count", "probabil", "50/50", "shot")
    ):
        counts = result_context.get("counts")
        if isinstance(counts, dict):
            counts = {
                key: value
                for key, value in counts.items()
                if isinstance(value, int) and not isinstance(value, bool) and value >= 0
            }
            total = sum(counts.values())
            if total:
                frequencies = "\n".join(
                    f"- **`{key}`:** {value / total:.1%}"
                    for key, value in sorted(counts.items())[:16]
                )
                result_summary = (
                    f"Your recorded measurements contain {total} shots.\n\n{frequencies}\n\n"
                    "A shot is one circuit execution and measurement.\n\nFinite samples can differ from ideal "
                    "probabilities by chance. On real hardware, gate errors, readout errors, and decoherence "
                    "can cause additional differences. Compare these frequencies with the ideal distribution "
                    "shown alongside the results."
                )
                if not overview:
                    return result_summary
    selected = find_lesson_id(question, lesson_id, experiment_id)
    experiment = EXPERIMENTS.get(experiment_id)
    if (
        experiment
        and selected == experiment["lesson_id"]
        and (
            overview
            or any(
                phrase in question
                for phrase in (
                    "this circuit",
                    "these gates",
                    "this experiment",
                    "current experiment",
                )
            )
        )
    ):
        gates = "\n".join(
            f"{index}. **{gate.get('label') or gate['name']}({', '.join(f'q{qubit}' for qubit in gate['qubits'])})** "
            f"— {gate['explanation']}"
            for index, gate in enumerate(experiment["gates"], 1)
        )
        probabilities = "\n".join(
            f"- **`{key}`:** {value:.1%}"
            for key, value in experiment["ideal_probabilities"].items()
        )
        return (
            f"### {experiment['title']}\n\n{experiment['description']}\n\n"
            f"### Circuit, left to right\n\n{gates}\n\n### What to expect\n\n{experiment['interpretation']}\n\n"
            f"### Ideal measurement probabilities\n\n{probabilities}\n\n"
            + (
                result_summary
                or "Run the simulator and compare its measurement frequencies with these ideal probabilities."
            )
        )
    if selected is None and ("interference" in question or experiment_id == "interference"):
        return (
            "Two Hadamard gates undo each other: H followed by H returns the qubit to its initial state. "
            "Starting from |0>, the first H creates equal amplitudes for |0> and |1>. The second H makes "
            "the amplitudes for |1> cancel and those for |0> reinforce. An ideal interference experiment "
            "therefore measures 0 on every shot."
        )
    lesson = next((item for item in LESSONS if item["lesson_id"] == selected), None)
    if lesson:
        return lesson["content"].split("**Knowledge check:**")[0].strip()
    return (
        "I can help with qubits, superposition, Hadamard and CNOT gates, entanglement, interference, "
        "measurement probabilities, quantum algorithms, teleportation, and error correction. Choose a lesson or experiment, or ask a "
        "specific question about one of these quantum computing topics."
    )


def fallback(
    messages: list[dict],
    lesson_id: str | None,
    experiment_id: str | None,
    result_context: dict | None,
) -> dict:
    question = next(
        (message["content"] for message in reversed(messages) if message["role"] == "user"), ""
    )
    return {
        "reply": guide_reply(question, lesson_id, experiment_id, result_context),
        "source": "fallback",
        "notice": FALLBACK_NOTICE,
    }


class AssistantService:
    @staticmethod
    async def chat(
        messages: list[dict],
        lesson_id: str | None,
        experiment_id: str | None,
        result_context: dict | None,
    ) -> dict:
        settings = get_settings()
        if not settings.llm_api_key.strip():
            logger.warning("Live assistant is not configured: LLM_API_KEY is missing")
            return fallback(messages, lesson_id, experiment_id, result_context)

        # MongoDB uses a synchronous driver; do not block the API event loop.
        question = next(
            (message["content"] for message in reversed(messages) if message["role"] == "user"), ""
        )
        context = await asyncio.to_thread(
            build_context, lesson_id, experiment_id, result_context, question
        )
        payload = {
            "model": settings.llm_model,
            "messages": [{"role": "system", "content": f"{SYSTEM_PROMPT}\n\nCONTEXT:\n{context}"}]
            + [{"role": message["role"], "content": message["content"]} for message in messages],
            "temperature": 0.2,
        }
        if urlsplit(settings.llm_base_url).hostname == "api.groq.com":
            payload["max_completion_tokens"] = 1200
            if settings.llm_model.startswith("openai/gpt-oss-"):
                payload["reasoning_effort"] = "low"
                payload["include_reasoning"] = False
        else:
            payload["max_tokens"] = 700

        try:
            async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
                response = await client.post(
                    f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.llm_api_key.strip()}"},
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                reply = data["choices"][0]["message"]["content"]
                if not isinstance(reply, str) or not reply.strip():
                    logger.warning("LLM response did not contain a usable answer")
                else:
                    # Provider token limits bound generation. Character slicing can
                    # sever Markdown tables, code fences, or LaTeX delimiters.
                    return {"reply": reply.strip(), "source": "llm", "notice": None}
        except httpx.TimeoutException:
            logger.warning("LLM request timed out")
        except httpx.HTTPStatusError as exc:
            # Never log the provider body: it can contain account or credential details.
            logger.warning(
                "LLM HTTP %s for configured model %s", exc.response.status_code, settings.llm_model
            )
        except (httpx.RequestError, ValueError, KeyError, IndexError, TypeError):
            logger.warning("LLM request failed or returned an invalid response")

        return fallback(messages, lesson_id, experiment_id, result_context)
