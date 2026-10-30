from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import timedelta
from unittest.mock import patch

import pytest
from pymongo.errors import AutoReconnect

from app.database.mongodb import utcnow
from app.errors import ConflictError, HardwareUnavailableError
from app.quantum.ibm_runtime import IBMRuntimeClient
from app.quantum.job_manager import JobManager, _hash_token
from app.services.quota_service import QuotaService


def submit():
    return JobManager.submit("superposition", 100, "a-stable-idempotency-key")


def test_retry_reuses_token_and_does_not_resubmit(database, hardware_settings):
    with patch.object(
        IBMRuntimeClient, "submit_job", return_value=("provider-1", "backend", "circuit")
    ) as provider:
        token, _ = submit()
        assert submit()[0] == token
        assert provider.call_count == 1
    job = database.quantum_jobs.find_one()
    assert "public_tracking_token" not in job
    assert job["public_tracking_token_hash"] == _hash_token(token)
    response = JobManager.to_response(job, token)
    assert response["tracking_id"] == token
    with pytest.raises(ConflictError):
        JobManager.submit("interference", 100, "a-stable-idempotency-key")


def test_unique_index_rejects_duplicate_idempotency_keys(database, hardware_settings):
    from pymongo.errors import DuplicateKeyError

    with patch.object(IBMRuntimeClient, "submit_job", return_value=("p", "b", "c")):
        submit()
    job = database.quantum_jobs.find_one()
    job.pop("_id")
    job["public_tracking_token_hash"] = "another-hash"
    with pytest.raises(DuplicateKeyError):
        database.quantum_jobs.insert_one(job)


def test_stale_concurrent_completions_release_only_their_own_slot(database, hardware_settings):
    with patch.object(IBMRuntimeClient, "submit_job", return_value=("p", "b", "c")):
        submit()
        JobManager.submit("superposition", 100, "another-idempotency-key")
    job = database.quantum_jobs.find_one()
    with patch.object(
        IBMRuntimeClient, "get_status_and_counts", return_value=("completed", {"0": 100}, None)
    ):
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(JobManager._refresh, [deepcopy(job), deepcopy(job)]))
    assert QuotaService.status()["active_jobs"] == 1
    assert database.quantum_jobs.find_one({"_id": job["_id"]})["status"] == "completed"


def test_background_reconciliation_finishes_job_without_browser(database, hardware_settings):
    with patch.object(IBMRuntimeClient, "submit_job", return_value=("p", "b", "c")):
        token, _ = submit()
    assert "expires_at" not in database.quantum_jobs.find_one()
    with patch.object(
        IBMRuntimeClient, "get_status_and_counts", return_value=("failed", None, "Provider failure")
    ):
        JobManager.reconcile()
    job = database.quantum_jobs.find_one()
    assert job["status"] == "failed"
    assert job["expires_at"] > utcnow()
    assert QuotaService.status()["active_jobs"] == 0
    assert JobManager.to_response(job, token)["error"] == "Provider failure"


def test_known_submission_failure_releases_reservation(database, hardware_settings):
    with patch.object(IBMRuntimeClient, "submit_job", side_effect=HardwareUnavailableError()):
        with pytest.raises(HardwareUnavailableError):
            submit()
    assert QuotaService.status()["active_jobs"] == 0


def test_ambiguous_submission_is_not_repeated_and_is_recovered_by_tag(database, hardware_settings):
    with patch.object(IBMRuntimeClient, "submit_job", side_effect=TimeoutError()) as provider:
        token, state = submit()
        assert state == "unknown"
        assert submit()[0] == token
        assert provider.call_count == 1
    database.quantum_jobs.update_one({}, {"$set": {"created_at": utcnow() - timedelta(minutes=3)}})
    with (
        patch.object(IBMRuntimeClient, "find_submission", return_value=("recovered", "backend")),
        patch.object(
            IBMRuntimeClient, "get_status_and_counts", return_value=("completed", {"0": 100}, None)
        ),
    ):
        JobManager.reconcile()
    job = database.quantum_jobs.find_one()
    assert job["provider_job_id"] == "recovered"
    assert job["status"] == "completed"
    assert QuotaService.status()["submitted_today"] == 1
    assert QuotaService.status()["active_jobs"] == 0


def test_failure_to_store_provider_id_can_be_recovered(database, hardware_settings):
    with (
        patch.object(IBMRuntimeClient, "submit_job", return_value=("p", "b", "c")),
        patch.object(JobManager, "_record_submission", side_effect=AutoReconnect()),
    ):
        token, _ = submit()
    assert database.quantum_jobs.find_one()["provider_job_id"] is None
    database.quantum_jobs.update_one({}, {"$set": {"created_at": utcnow() - timedelta(minutes=3)}})
    with (
        patch.object(IBMRuntimeClient, "find_submission", return_value=("p", "b")),
        patch.object(
            IBMRuntimeClient, "get_status_and_counts", return_value=("running", None, None)
        ),
    ):
        assert JobManager.get_job(token)["provider_job_id"] == "p"
    assert QuotaService.status()["submitted_today"] == 1


def test_interrupted_quota_settlement_remains_recoverable(database, hardware_settings):
    with patch.object(IBMRuntimeClient, "submit_job", return_value=("p", "b", "c")):
        submit()
    with (
        patch.object(
            IBMRuntimeClient, "get_status_and_counts", return_value=("completed", {"0": 100}, None)
        ),
        patch.object(QuotaService, "release_active_job", side_effect=AutoReconnect()),
    ):
        JobManager.reconcile()
    job = database.quantum_jobs.find_one()
    assert job["status"] == "completed"
    assert "expires_at" not in job
    JobManager.reconcile()
    assert database.quantum_jobs.find_one()["quota_released"] is True
    assert "expires_at" in database.quantum_jobs.find_one()
    assert QuotaService.status()["active_jobs"] == 0
