from copy import deepcopy
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.database.seed import LESSONS
from app.main import app


@pytest.fixture
def client():
    database = MagicMock()
    lessons = deepcopy(LESSONS)
    database.lessons.find.return_value.sort.return_value = sorted(
        lessons, key=lambda lesson: lesson["order"]
    )
    database.lessons.find_one.side_effect = lambda query, projection: next(
        (lesson for lesson in lessons if lesson["lesson_id"] == query["lesson_id"]),
        None,
    )
    with (
        patch("app.database.mongodb.Mongo.connect"),
        patch("app.database.mongodb.Mongo.close"),
        patch("app.database.mongodb.Mongo.db", return_value=database),
        TestClient(app) as test_client,
    ):
        yield test_client


def test_health_and_public_config(client):
    health = client.get("/api/health")
    assert health.status_code == 200

    config = client.get("/api/config/public")
    assert config.status_code == 200
    assert "hardware_enabled" in config.json()


def test_lesson_endpoints(client):
    lessons = client.get("/api/lessons").json()["lessons"]
    assert len(lessons) >= 5

    lesson = client.get("/api/lessons/superposition")
    assert lesson.status_code == 200
    assert lesson.json()["lesson_id"] == "superposition"


def test_simulate_validation(client):
    response = client.post(
        "/api/experiments/simulate",
        json={"experiment_id": "superposition", "shots": 0},
    )
    assert response.status_code == 422
