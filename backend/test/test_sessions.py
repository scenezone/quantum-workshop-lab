import json
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.ai.assistant_service import AssistantService
from app.config import get_settings
from app.database.mongodb import Mongo, utcnow
from app.main import app

TOKEN = "facilitator-token-123456"
ADMIN = {"Authorization": f"Bearer {TOKEN}"}


@pytest.fixture
def client(database, monkeypatch):
    monkeypatch.setattr(get_settings(), "admin_token", TOKEN)
    with (
        patch("app.database.mongodb.Mongo.connect"),
        patch("app.database.mongodb.Mongo.close"),
        TestClient(app) as test_client,
    ):
        yield test_client


def test_admin_endpoints_require_the_configured_token(client, monkeypatch):
    assert client.get("/api/admin/status").status_code == 401
    assert (
        client.get("/api/admin/status", headers={"Authorization": "Bearer wrong"}).status_code
        == 401
    )
    assert client.get("/api/admin/status", headers=ADMIN).json() == {"status": "ok"}
    monkeypatch.setattr(get_settings(), "admin_token", "")
    assert client.get("/api/admin/status", headers=ADMIN).status_code == 503


def test_session_join_progress_and_dashboard(client):
    session = client.post("/api/admin/sessions", json={"name": "Friday lab"}, headers=ADMIN).json()
    code = session["code"]
    assert len(code) == 6
    assert client.get(f"/api/sessions/{code.lower()}").json()["name"] == "Friday lab"

    joined = client.post(f"/api/sessions/{code}/join", json={"nickname": "  Ada   L "}).json()
    progress = {
        "participant_id": joined["participant_id"],
        "participant_token": joined["participant_token"],
        "completed_lessons": ["superposition", "not-a-lesson"],
        "completed_challenges": ["ghz-three", "bell-correlations", "unknown"],
        "practice_correct": 9,
        "practice_attempted": 4,
    }
    saved = client.put(f"/api/sessions/{code}/progress", json=progress).json()
    assert saved["completed_lessons"] == ["superposition"]
    assert saved["completed_challenges"] == ["bell-correlations", "ghz-three"]

    forged = {**progress, "participant_token": "x" * 32}
    assert client.put(f"/api/sessions/{code}/progress", json=forged).status_code == 401

    client.post(
        "/api/feedback",
        json={
            "rating": 4,
            "clarity_rating": 5,
            "completed_workshop": True,
            "comments": "=SUM(1)",
            "session_code": code,
        },
    )
    dashboard = client.get(f"/api/admin/sessions/{code}", headers=ADMIN).json()
    assert dashboard["participant_count"] == 1
    participant = dashboard["participants"][0]
    assert participant["nickname"] == "Ada L"
    assert participant["practice_correct"] == 4  # Clamped to the attempts.
    assert "token_hash" not in json.dumps(dashboard)
    lesson = next(
        item for item in dashboard["lesson_completion"] if item["lesson_id"] == "superposition"
    )
    assert lesson["completed"] == 1
    assert dashboard["feedback"]["count"] == 1
    assert dashboard["feedback"]["average_clarity"] == 5

    export = client.get(f"/api/admin/feedback/export?session_code={code}", headers=ADMIN)
    assert export.headers["content-type"].startswith("text/csv")
    assert "'=SUM(1)" in export.text  # Spreadsheet formulas are neutralized.


def test_unknown_or_expired_sessions_are_not_found(client, database):
    assert client.get("/api/sessions/ZZZZZZ").status_code == 404
    session = client.post("/api/admin/sessions", json={"name": "Old"}, headers=ADMIN).json()
    assert client.get(f"/api/sessions/{session['code']}").status_code == 200
    database.workshop_sessions.update_one(
        {"code": session["code"]}, {"$set": {"expires_at": utcnow() - timedelta(minutes=1)}}
    )
    assert client.get(f"/api/sessions/{session['code']}").status_code == 404


def test_feedback_with_an_ended_session_is_still_saved(client, database):
    response = client.post(
        "/api/feedback",
        json={
            "rating": 3,
            "clarity_rating": 3,
            "completed_workshop": False,
            "session_code": "NOPE42",
        },
    )
    assert response.status_code == 200
    assert database.feedback.find_one()["session_code"] is None


def test_simulator_only_mode_without_a_database(monkeypatch):
    monkeypatch.setattr(get_settings(), "mongodb_uri", "")
    monkeypatch.setattr(Mongo, "client", None)
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["database"] == "disabled"
        config = client.get("/api/config/public").json()
        assert config["database_enabled"] is False
        assert config["hardware_enabled"] is False
        assert len(client.get("/api/lessons").json()["lessons"]) == 14
        assert (
            client.post(
                "/api/experiments/simulate", json={"experiment_id": "superposition", "shots": 16}
            ).status_code
            == 200
        )
        assert client.get("/api/hardware/status").json()["remaining_today"] == 0
        assert client.get("/api/hardware/saved/superposition").json() is None
        feedback = client.post(
            "/api/feedback", json={"rating": 5, "clarity_rating": 5, "completed_workshop": True}
        )
        assert feedback.status_code == 503
        assert "simulator-only" in feedback.json()["detail"]


def _events(body: str) -> list[dict]:
    return [json.loads(line[5:]) for line in body.splitlines() if line.startswith("data:")]


def test_stream_falls_back_to_the_guide_without_credentials(client):
    response = client.post(
        "/api/assistant/chat/stream",
        json={"messages": [{"role": "user", "content": "What is a Bell state?"}]},
    )
    assert response.headers["content-type"].startswith("text/event-stream")
    events = _events(response.text)
    assert [event["type"] for event in events] == ["meta", "delta", "done"]
    assert events[0]["source"] == "fallback"
    assert events[1]["text"]


def test_stream_relays_provider_tokens(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "llm_api_key", "test-key")
    chunks = [
        'data: {"choices":[{"delta":{"content":"Hello"}}]}',
        "",
        'data: {"choices":[{"delta":{"content":" learner"}}]}',
        "data: [DONE]",
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content)["stream"] is True
        return httpx.Response(
            200, text="\n".join(chunks), headers={"content-type": "text/event-stream"}
        )

    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient

    with patch(
        "app.ai.assistant_service.httpx.AsyncClient",
        lambda **kwargs: original(transport=transport, **kwargs),
    ):
        response = client.post(
            "/api/assistant/chat/stream",
            json={"messages": [{"role": "user", "content": "Hi"}]},
        )
    events = _events(response.text)
    assert events[0] == {"type": "meta", "source": "llm", "notice": None}
    assert "".join(event["text"] for event in events if event["type"] == "delta") == "Hello learner"
    assert events[-1]["type"] == "done"


def test_stream_provider_error_falls_back(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "llm_api_key", "test-key")
    transport = httpx.MockTransport(lambda request: httpx.Response(500, text="secret details"))
    original = httpx.AsyncClient
    with patch(
        "app.ai.assistant_service.httpx.AsyncClient",
        lambda **kwargs: original(transport=transport, **kwargs),
    ):
        response = client.post(
            "/api/assistant/chat/stream",
            json={"messages": [{"role": "user", "content": "Explain superposition"}]},
        )
    assert "secret details" not in response.text
    assert _events(response.text)[0]["source"] == "fallback"


def test_written_answers_get_ai_feedback_when_live_ai_is_configured(client):
    grading = {
        "covered_points": ["Sampling fluctuations"],
        "missing_points": [],
        "feedback": "Good.",
    }
    with patch.object(
        AssistantService, "grade_written_answer", AsyncMock(return_value=grading)
    ) as grade:
        response = client.post(
            "/api/lessons/superposition/practice/check",
            json={"question_id": "superposition-written-2", "answer": "Finite samples vary."},
        )
    assert response.json()["ai_feedback"] == grading
    assert "prompt" not in response.json()
    assert grade.await_args.args[3] == "Finite samples vary."


@pytest.mark.asyncio
async def test_grading_parses_model_json_and_ignores_unknown_points(monkeypatch):
    monkeypatch.setattr(get_settings(), "llm_api_key", "test-key")
    content = 'Here you go: {"covered": [1, 7, "x"], "feedback": "Nice start."}'
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"choices": [{"message": {"content": content}}]})
    )
    original = httpx.AsyncClient
    with patch(
        "app.ai.assistant_service.httpx.AsyncClient",
        lambda **kwargs: original(transport=transport, **kwargs),
    ):
        result = await AssistantService.grade_written_answer("Q", "S", ["one", "two"], "answer")
    assert result == {
        "covered_points": ["one"],
        "missing_points": ["two"],
        "feedback": "Nice start.",
    }
