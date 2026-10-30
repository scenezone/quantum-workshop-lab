from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.database.mongodb import utcnow
from app.errors import QuotaExceededError
from app.main import app
from app.services.quota_service import QuotaService


def test_daily_limit_includes_confirmed_jobs(database, hardware_settings):
    hardware_settings.ibm_max_daily_jobs = 1
    day = utcnow().date().isoformat()
    QuotaService.reserve_submission("first", day)
    QuotaService.confirm_submission("first")
    QuotaService.release_active_job("first")
    with pytest.raises(QuotaExceededError):
        QuotaService.reserve_submission("second", day)


def test_active_limit_includes_previous_day(database, hardware_settings):
    hardware_settings.ibm_max_active_jobs = 1
    yesterday = (utcnow() - timedelta(days=1)).date().isoformat()
    QuotaService.reserve_submission("first", yesterday)
    QuotaService.confirm_submission("first")
    with pytest.raises(QuotaExceededError):
        QuotaService.reserve_submission("second", utcnow().date().isoformat())
    assert QuotaService.status()["active_jobs"] == 1


def test_reservations_and_releases_are_idempotent(database, hardware_settings):
    day = utcnow().date().isoformat()
    QuotaService.reserve_submission("first", day)
    QuotaService.reserve_submission("first", day)
    QuotaService.confirm_submission("first")
    QuotaService.confirm_submission("first")
    QuotaService.reserve_submission("second", day)
    QuotaService.confirm_submission("second")
    QuotaService.release_active_job("first")
    QuotaService.release_active_job("first")
    assert QuotaService.status()["active_jobs"] == 1
    assert QuotaService.status()["submitted_today"] == 2


def test_release_after_midnight_targets_original_reservation(database, hardware_settings):
    yesterday = (utcnow() - timedelta(days=1)).date().isoformat()
    QuotaService.reserve_submission("first", yesterday)
    QuotaService.release_reservation("first")
    assert QuotaService.status()["active_jobs"] == 0


def test_parallel_reservations_obey_limit(database, hardware_settings):
    hardware_settings.ibm_max_active_jobs = 2

    def reserve(index):
        try:
            QuotaService.reserve_submission(str(index), utcnow().date().isoformat())
            return True
        except QuotaExceededError:
            return False

    with ThreadPoolExecutor(max_workers=6) as pool:
        assert sum(pool.map(reserve, range(12))) == 2
    assert QuotaService.status()["active_jobs"] == 2


def test_hardware_disabled_rejects_submission(database):
    with (
        patch("app.database.mongodb.Mongo.connect"),
        patch("app.database.mongodb.Mongo.close"),
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
    assert response.status_code == 503
