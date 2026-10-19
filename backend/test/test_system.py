from unittest.mock import patch

from fastapi.testclient import TestClient

from app.config import get_settings
from app.errors import AppError
from app.main import app


def test_unhealthy_database_returns_503(database):
    with patch("app.database.mongodb.Mongo.connect"), patch("app.database.mongodb.Mongo.close"), TestClient(app) as client:
        with patch("app.database.mongodb.Mongo.health", return_value=False):
            response = client.get("/api/health")
        assert response.status_code == 503
        assert response.json()["status"] == "unavailable"


def test_experiment_detail_exposes_full_metadata(database):
    with patch("app.database.mongodb.Mongo.connect"), patch("app.database.mongodb.Mongo.close"), TestClient(app) as client:
        data = client.get("/api/experiments/superposition").json()
    assert data["experiment_id"] == "superposition"
    assert data["gates"]
    assert data["qiskit_code"]


def test_configured_simulator_limit_is_enforced(database, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_simulator_shots", 100)
    with patch("app.database.mongodb.Mongo.connect"), patch("app.database.mongodb.Mongo.close"), TestClient(app) as client:
        response = client.post("/api/experiments/simulate", json={"experiment_id": "superposition", "shots": 101})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid number of shots."


def test_custom_app_error_message_is_preserved():
    assert AppError("Specific reason").detail == "Specific reason"
