from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.errors import QuotaExceededError
from app.main import app
from app.services.quota_service import QuotaService


def test_quota_reservation_rejects_over_limit():
    with patch("app.services.quota_service.get_settings") as mock_settings, patch(
        "app.services.quota_service.Mongo.db"
    ) as mock_db:
        settings = mock_settings.return_value
        settings.ibm_max_daily_jobs = 1
        mock_db.return_value.hardware_quota.find_one_and_update.return_value = {
            "reserved_count": 2
        }
        with pytest.raises(QuotaExceededError):
            QuotaService.reserve_submission()


def test_hardware_disabled_rejects_submission(monkeypatch):
    monkeypatch.setattr(get_settings(), "ibm_hardware_enabled", False)
    with (
        patch("app.database.mongodb.Mongo.connect"),
        patch("app.database.mongodb.Mongo.close"),
        patch("app.main.seed_database"),
        TestClient(app) as client,
    ):
        response = client.post(
            "/api/experiments/hardware",
            json={
                "experiment_id": "superposition",
                "shots": 100,
                "idempotency_key": "test-idempotency-key-123",
            },
        )
        assert response.status_code in {400, 503}
