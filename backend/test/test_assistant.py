from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.ai.assistant_service import AssistantService
from app.config import get_settings
from app.quantum.ibm_runtime import IBMRuntimeClient


@pytest.mark.asyncio
async def test_assistant_works_without_credentials():
    result = await AssistantService.chat([{"role": "user", "content": "What is a qubit?"}], None, None, None)
    assert result["source"] == "fallback"


@pytest.mark.asyncio
async def test_assistant_sends_context_and_preserves_complete_formatted_reply(database, monkeypatch):
    monkeypatch.setattr(get_settings(), "llm_api_key", "test-key")
    client = AsyncMock()
    response = MagicMock()
    reply = "### Walkthrough\n\n" + "A complete explanation of the circuit.\n\n" * 70
    reply += "$$\n\\frac{1}{\\sqrt{2}}(|0\\rangle+|1\\rangle)\n$$\n\n```python\nqc.h(0)\n```"
    response.json.return_value = {"choices": [{"message": {"content": reply}}]}
    client.post.return_value = response
    with patch("httpx.AsyncClient") as factory:
        factory.return_value.__aenter__.return_value = client
        result = await AssistantService.chat(
            [{"role": "user", "content": "Explain"}], "superposition", "superposition", None,
        )
    assert result["source"] == "llm"
    assert len(result["reply"]) > 2000
    assert result["reply"] == reply
    payload = client.post.call_args.kwargs["json"]
    assert payload["messages"][-1]["role"] == "user"
    assert "LESSON:" in payload["messages"][0]["content"]


def test_long_assistant_answer_is_valid_in_followup_history():
    from app.database.models import AssistantRequest
    payload = AssistantRequest(messages=[
        {"role": "assistant", "content": "A detailed explanation. " * 150},
        {"role": "user", "content": "Explain the last step."},
    ])
    assert len(payload.messages[0].content) > 2000


def test_long_user_question_still_exceeds_the_input_limit():
    from pydantic import ValidationError
    from app.database.models import AssistantRequest
    with pytest.raises(ValidationError, match="Questions must be at most 2000 characters"):
        AssistantRequest(messages=[{"role": "user", "content": "A" * 2001}])


@pytest.mark.asyncio
async def test_llm_timeout_returns_fallback(monkeypatch):
    monkeypatch.setattr(get_settings(), "llm_api_key", "test-key")
    with patch("httpx.AsyncClient") as factory:
        factory.return_value.__aenter__.return_value.post.side_effect = httpx.ReadTimeout("timeout")
        result = await AssistantService.chat([{"role": "user", "content": "Explain"}], None, None, None)
    assert result["source"] == "fallback"


@pytest.mark.parametrize("raw,expected", [("ERROR", "failed"), ("CANCELLED", "cancelled"), ("RUNNING", "running")])
def test_ibm_status_mapping(raw, expected):
    with patch.object(IBMRuntimeClient, "service") as service:
        service.return_value.job.return_value.status.return_value = raw
        assert IBMRuntimeClient.get_status_and_counts("fake")[0] == expected


def test_completed_ibm_job_uses_named_register():
    from qiskit.primitives import DataBin, BitArray
    from types import SimpleNamespace
    data = DataBin(c=BitArray.from_samples(["0", "1", "1"]))
    with patch.object(IBMRuntimeClient, "service") as service:
        job = service.return_value.job.return_value
        job.status.return_value = "DONE"
        job.result.return_value = [SimpleNamespace(data=data)]
        status, counts, error = IBMRuntimeClient.get_status_and_counts("fake")
    assert status == "completed"
    assert counts == {"0": 1, "1": 2}
    assert error is None
