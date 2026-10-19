from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.ai.assistant_service import AssistantService
from app.ai.knowledge_base import build_context, find_lesson_id
from app.config import Settings, get_settings
from app.errors import ExternalServiceError


@pytest.mark.parametrize("status", [400, 401, 403, 404, 429, 503])
@pytest.mark.asyncio
async def test_provider_errors_are_explicit_guide_answers(status, monkeypatch, caplog):
    monkeypatch.setattr(get_settings(), "llm_api_key", "private-test-credential")
    response = httpx.Response(status, request=httpx.Request("POST", "https://api.groq.com/chat"), json={
        "error": {"message": "Never expose private-test-credential"},
    })
    with patch("httpx.AsyncClient") as factory:
        factory.return_value.__aenter__.return_value.post = AsyncMock(return_value=response)
        result = await AssistantService.chat([{"role": "user", "content": "What is a qubit?"}], None, None, None)
    assert result["source"] == "fallback"
    assert "workshop guide" in result["notice"]
    assert "qubit" in result["reply"].lower()
    assert "private-test-credential" not in caplog.text
    assert "private-test-credential" not in str(result)


@pytest.mark.parametrize("data", [
    {"choices": []}, {"choices": [{"message": {"content": None}}]},
    {"choices": [{"message": {"content": ""}}]}, {"unexpected": "shape"},
])
@pytest.mark.asyncio
async def test_malformed_provider_answers_do_not_crash(data, monkeypatch):
    monkeypatch.setattr(get_settings(), "llm_api_key", "test")
    response = httpx.Response(200, request=httpx.Request("POST", "https://api.groq.com/chat"), json=data)
    with patch("httpx.AsyncClient") as factory:
        factory.return_value.__aenter__.return_value.post = AsyncMock(return_value=response)
        result = await AssistantService.chat([{"role": "user", "content": "Explain interference"}], None, None, None)
    assert result["source"] == "fallback"
    assert "cancel" in result["reply"]


@pytest.mark.asyncio
async def test_reasoning_model_request_uses_supported_groq_parameters(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "llm_api_key", "test")
    monkeypatch.setattr(settings, "llm_base_url", "https://api.groq.com/openai/v1")
    monkeypatch.setattr(settings, "llm_model", "openai/gpt-oss-20b")
    response = httpx.Response(200, request=httpx.Request("POST", "https://api.groq.com/chat"), json={
        "choices": [{"message": {"content": "A qubit is a quantum bit."}}],
    })
    with patch("httpx.AsyncClient") as factory:
        post = AsyncMock(return_value=response)
        factory.return_value.__aenter__.return_value.post = post
        result = await AssistantService.chat([{"role": "user", "content": "What is a qubit?"}], None, None, None)
    payload = post.call_args.kwargs["json"]
    assert "max_tokens" not in payload
    assert payload["max_completion_tokens"] == 1200
    assert payload["reasoning_effort"] == "low"
    assert payload["include_reasoning"] is False
    assert result["source"] == "llm"


def test_lesson_context_survives_a_database_outage():
    with patch("app.ai.knowledge_base.Mongo.db", side_effect=ExternalServiceError()):
        context = build_context("superposition", None, None)
    assert "LESSON:" in context
    assert "Hadamard" in context


def test_missing_database_lesson_uses_bundled_current_topic(database):
    database.lessons.delete_one({"lesson_id": "grover-search"})
    context = build_context("grover-search", None, None, "Explain this gate")
    assert "LESSON: Grover" in context
    assert "Difficulty: advanced" in context


@pytest.mark.parametrize("question", [
    "Explain this gate", "What do these measurements mean?", "Give me an overview of my current experiment",
])
def test_contextual_references_keep_the_selected_advanced_topic(question):
    assert find_lesson_id(question, experiment_id="grover_search") == "grover-search"


def test_current_experiment_retains_its_theory_when_question_mentions_a_general_gate(database):
    context = build_context(None, "grover_search", None, "What is a Hadamard gate?")
    assert "LESSON: Grover" in context
    assert "RELATED LESSON:" in context
    assert "Gate walkthrough:" in context


@pytest.mark.asyncio
async def test_automatic_offline_overview_includes_current_circuit_and_recorded_results():
    result = await AssistantService.chat(
        [{"role": "user", "content": "Give me an overview of my current experiment and its recorded results"}],
        "entanglement", "bell_entanglement", {"counts": {"00": 60, "11": 68}},
    )
    assert result["source"] == "fallback"
    assert "Circuit, left to right" in result["reply"]
    assert "CX(q0, q1)" in result["reply"]
    assert "128 shots" in result["reply"]
    assert "46.9%" in result["reply"]


@pytest.mark.asyncio
async def test_automatic_offline_lesson_overview_uses_the_selected_advanced_lesson():
    result = await AssistantService.chat(
        [{"role": "user", "content": "Give me an overview of my current lesson"}], "grover-search", None, None,
    )
    assert result["source"] == "fallback"
    assert "oracle" in result["reply"].lower()
    assert "diffusion" in result["reply"].lower()


@pytest.mark.asyncio
async def test_offline_guide_uses_the_question_and_recorded_results():
    first = await AssistantService.chat([{"role": "user", "content": "Explain entanglement"}], None, None, None)
    second = await AssistantService.chat([{"role": "user", "content": "Explain my results"}], None, "superposition", {"counts": {"0": 75, "1": 25}})
    assert first["reply"] != second["reply"]
    assert "75.0%" in second["reply"]
    assert "100 shots" in second["reply"]


def test_backend_env_file_is_independent_of_launch_directory(monkeypatch, tmp_path):
    from pathlib import Path
    original = Path(Settings.model_config["env_file"])
    assert original.is_absolute()
    # A cwd-local .env must not override this application's backend configuration.
    (tmp_path / ".env").write_text("LLM_MODEL=wrong-cwd-model\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert Settings().llm_model != "wrong-cwd-model"
