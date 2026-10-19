import hashlib
import hmac
import logging
import secrets
from datetime import timedelta

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.config import get_settings
from app.database.mongodb import Mongo, utcnow
from app.errors import AppError, ConflictError, HardwareUnavailableError, NotFoundError
from app.quantum.ibm_runtime import IBMRuntimeClient
from app.quantum.circuits import get_metadata
from app.services.quota_service import QuotaService

logger = logging.getLogger(__name__)
TERMINAL = {"completed", "failed", "cancelled"}


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _tracking_token(idempotency_key: str, nonce: str) -> str:
    # Replay needs the caller's original key; neither credential is stored.
    return hmac.new(idempotency_key.encode(), nonce.encode(), hashlib.sha256).hexdigest()


class JobManager:
    @staticmethod
    def _replay(job: dict, experiment_id: str, shots: int, key: str) -> tuple[str, str]:
        if job["experiment_type"] != experiment_id or job["shots"] != shots:
            raise ConflictError("This submission key was already used for different parameters.")
        if not job.get("tracking_nonce"):
            raise ConflictError("Please retain the original tracking ID for this older submission.")
        return _tracking_token(key, job["tracking_nonce"]), job["status"]

    @staticmethod
    def submit(experiment_id: str, shots: int, idempotency_key: str) -> tuple[str, str]:
        settings = get_settings()
        get_metadata(experiment_id)
        collection = Mongo.db().quantum_jobs
        idempotency_hash = _hash_token(idempotency_key)
        existing = collection.find_one({"idempotency_key_hash": idempotency_hash})
        if existing:
            return JobManager._replay(existing, experiment_id, shots, idempotency_key)
        if not settings.ibm_hardware_enabled:
            raise HardwareUnavailableError("IBM hardware access is disabled.")
        if not 1 <= shots <= settings.ibm_max_shots:
            raise AppError("Requested shots exceed the hardware limit.")

        nonce = secrets.token_hex(32)
        tracking_token = _tracking_token(idempotency_key, nonce)
        now = utcnow()
        job_id = secrets.token_hex(12)
        document = {
            "internal_job_id": job_id, "tracking_nonce": nonce,
            "public_tracking_token_hash": _hash_token(tracking_token),
            "idempotency_key_hash": idempotency_hash,
            "provider_job_id": None, "experiment_type": experiment_id,
            "backend_name": None, "shots": shots, "status": "queued",
            "submission_state": "preparing", "quota_released": False,
            "result_counts": None, "created_at": now, "updated_at": now,
            "quota_date": now.date().isoformat(),
        }
        try:
            collection.insert_one(document)
        except DuplicateKeyError:
            existing = collection.find_one({"idempotency_key_hash": idempotency_hash})
            if existing:
                return JobManager._replay(existing, experiment_id, shots, idempotency_key)
            raise ConflictError("Unable to create this hardware submission.")

        try:
            QuotaService.reserve_submission(job_id, document["quota_date"])
            collection.update_one({"internal_job_id": job_id}, {"$set": {
                "submission_state": "submitting", "updated_at": utcnow(),
            }})
        except Exception:
            JobManager._fail_before_submission(document, "Hardware capacity is unavailable.")
            raise

        try:
            provider_job_id, backend_name, _ = IBMRuntimeClient.submit_job(experiment_id, shots, job_id)
        except HardwareUnavailableError:
            JobManager._fail_before_submission(document, "Hardware is currently unavailable.")
            raise
        except Exception:
            # A timeout may follow provider acceptance. Tags recover the job
            # without automatically duplicating a paid submission.
            logger.exception("Hardware submission requires reconciliation")
            try:
                collection.update_one({"internal_job_id": job_id}, {"$set": {
                    "status": "unknown", "updated_at": utcnow(),
                    "error": "Checking whether the hardware provider accepted this submission.",
                }})
            except Exception:
                logger.exception("Unable to persist pending submission status")
            return tracking_token, "unknown"

        try:
            JobManager._record_submission(document, provider_job_id, backend_name)
        except Exception:
            logger.exception("Submission accepted; provider tag will recover database state")
        return tracking_token, "queued"

    @staticmethod
    def _fail_before_submission(job: dict, error: str) -> None:
        try:
            Mongo.db().quantum_jobs.update_one({"internal_job_id": job["internal_job_id"]}, {"$set": {
                "status": "failed", "submission_state": "rejected", "error": error,
                "updated_at": utcnow(),
            }})
        finally:
            QuotaService.release_reservation(job["internal_job_id"])
        Mongo.db().quantum_jobs.update_one({"internal_job_id": job["internal_job_id"]}, {"$set": {
            "quota_released": True,
            "expires_at": utcnow() + timedelta(days=get_settings().job_retention_days),
        }})

    @staticmethod
    def _record_submission(job: dict, provider_id: str, backend_name: str) -> None:
        Mongo.db().quantum_jobs.update_one({
            "internal_job_id": job["internal_job_id"], "status": {"$nin": list(TERMINAL)},
        }, {"$set": {
            "provider_job_id": provider_id, "backend_name": backend_name,
            "submission_state": "submitted", "status": "queued", "error": None,
            "updated_at": utcnow(),
        }})
        QuotaService.confirm_submission(job["internal_job_id"])

    @staticmethod
    def _refresh(job: dict) -> dict:
        collection = Mongo.db().quantum_jobs
        job_id = job["internal_job_id"]
        if job["status"] in TERMINAL:
            if not job.get("quota_released"):
                if job.get("submission_state") == "rejected":
                    QuotaService.release_reservation(job_id)
                else:
                    QuotaService.confirm_submission(job_id)
                    QuotaService.release_active_job(job_id)
                collection.update_one({"_id": job["_id"]}, {"$set": {
                    "quota_released": True,
                    "expires_at": utcnow() + timedelta(days=get_settings().job_retention_days),
                }})
            return job
        if not job.get("provider_job_id"):
            age = (utcnow() - job["created_at"]).total_seconds()
            if age < 120:
                return job
            if job.get("submission_state") == "preparing":
                JobManager._fail_before_submission(job, "Submission was interrupted before reaching hardware.")
                return collection.find_one({"_id": job["_id"]})
            found = IBMRuntimeClient.find_submission(job_id)
            if not found:
                return job  # Preserve ambiguous reservations instead of risking duplicate jobs.
            JobManager._record_submission(job, *found)
            job = collection.find_one({"_id": job["_id"]})
        QuotaService.confirm_submission(job_id)
        status, counts, error = IBMRuntimeClient.get_status_and_counts(job["provider_job_id"])
        update = {"status": status, "error": error, "updated_at": utcnow()}
        if counts is not None:
            update["result_counts"] = counts
        operations = {"$set": update}
        # Expiry starts only after quota settlement succeeds, so TTL cleanup
        # cannot remove the record needed to retry interrupted accounting.
        operations["$unset"] = {"expires_at": ""}
        updated = collection.find_one_and_update(
            {"_id": job["_id"], "status": {"$nin": list(TERMINAL)}},
            operations, return_document=ReturnDocument.AFTER,
        )
        job = updated or collection.find_one({"_id": job["_id"]})
        if job["status"] in TERMINAL:
            return JobManager._refresh(job)
        return job

    @staticmethod
    def reconcile() -> None:
        for job in Mongo.db().quantum_jobs.find({"$or": [
            {"status": {"$nin": list(TERMINAL)}}, {"quota_released": False},
        ]}):
            try:
                JobManager._refresh(job)
            except Exception:
                logger.exception("Unable to reconcile hardware job %s", job.get("internal_job_id"))

    @staticmethod
    def get_job(tracking_id: str) -> dict:
        job = Mongo.db().quantum_jobs.find_one({"public_tracking_token_hash": _hash_token(tracking_id)})
        if not job:
            raise NotFoundError("Job not found or expired.")
        return JobManager._refresh(job)

    @staticmethod
    def to_response(job: dict, tracking_id: str) -> dict:
        counts = job.get("result_counts")
        total = sum(counts.values()) if counts else 0
        return {
            "tracking_id": tracking_id, "status": job["status"],
            "experiment_id": job["experiment_type"], "backend_name": job.get("backend_name"),
            "provider_job_id": job.get("provider_job_id"), "shots": job["shots"],
            "counts": counts,
            "observed_probabilities": {key: value / total for key, value in counts.items()} if total else None,
            "ideal_probabilities": get_metadata(job["experiment_type"])["ideal_probabilities"],
            "error": job.get("error"), "created_at": job.get("created_at"), "updated_at": job.get("updated_at"),
        }
