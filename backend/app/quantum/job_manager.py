import hashlib
import secrets
from datetime import timedelta

from pymongo.errors import DuplicateKeyError

from app.config import get_settings
from app.database.mongodb import Mongo, utcnow
from app.errors import AppError, NotFoundError
from app.quantum import ibm_runtime
from app.quantum.circuits import get_metadata
from app.services.quota_service import QuotaService


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class JobManager:
    @staticmethod
    def submit(experiment_id: str, shots: int, idempotency_key: str) -> tuple[str, str]:
        settings = get_settings()
        if not settings.ibm_hardware_enabled:
            raise AppError("IBM hardware access is disabled.")
        if shots > settings.ibm_max_shots:
            raise AppError("Requested shots exceed the hardware limit.")

        idempotency_hash = _hash_token(idempotency_key)
        existing = Mongo.db().quantum_jobs.find_one({"idempotency_key_hash": idempotency_hash})
        if existing:
            return existing["public_tracking_token"], existing["status"]

        QuotaService.reserve_submission()

        tracking_token = secrets.token_urlsafe(32)
        now = utcnow()
        document = {
            "internal_job_id": secrets.token_hex(12),
            "public_tracking_token_hash": _hash_token(tracking_token),
            "idempotency_key_hash": idempotency_hash,
            "provider_job_id": None,
            "experiment_type": experiment_id,
            "backend_name": None,
            "shots": shots,
            "status": "queued",
            "result_counts": None,
            "created_at": now,
            "updated_at": now,
            "expires_at": now + timedelta(hours=24),
        }

        try:
            Mongo.db().quantum_jobs.insert_one(document)
        except DuplicateKeyError:
            QuotaService.release_reservation()
            existing = Mongo.db().quantum_jobs.find_one(
                {"idempotency_key_hash": idempotency_hash}
            )
            if existing:
                return existing["public_tracking_token"], existing["status"]
            raise AppError("Unable to create hardware job.")

        try:
            provider_job_id, backend_name, _ = ibm_runtime.IBMRuntimeClient.submit(
                experiment_id, shots
            )
        except Exception:
            Mongo.db().quantum_jobs.update_one(
                {"public_tracking_token_hash": _hash_token(tracking_token)},
                {"$set": {"status": "failed", "error": "Submission failed.", "updated_at": utcnow()}},
            )
            QuotaService.release_reservation()
            raise

        Mongo.db().quantum_jobs.update_one(
            {"public_tracking_token_hash": _hash_token(tracking_token)},
            {
                "$set": {
                    "provider_job_id": provider_job_id,
                    "backend_name": backend_name,
                    "status": "queued",
                    "updated_at": utcnow(),
                }
            },
        )
        QuotaService.confirm_submission()
        return tracking_token, "queued"

    @staticmethod
    def get_job(tracking_id: str) -> dict:
        token_hash = _hash_token(tracking_id)
        job = Mongo.db().quantum_jobs.find_one(
            {"public_tracking_token_hash": token_hash}
        )
        if not job:
            raise NotFoundError("Job not found or expired.")

        if job["status"] not in {"completed", "failed", "cancelled"} and job.get("provider_job_id"):
            status, counts, error = ibm_runtime.IBMRuntimeClient.get_status_and_counts(
                job["provider_job_id"]
            )
            update = {"status": status, "updated_at": utcnow()}
            if counts is not None:
                update["result_counts"] = counts
            if error:
                update["error"] = error
            if status in {"completed", "failed", "cancelled"}:
                QuotaService.release_active_job()
            Mongo.db().quantum_jobs.update_one(
                {"_id": job["_id"]}, {"$set": update}
            )
            job.update(update)

        return job

    @staticmethod
    def to_response(job: dict) -> dict:
        counts = job.get("result_counts")
        shots = job["shots"]
        metadata = get_metadata(job["experiment_type"])
        observed = None
        if counts:
            total = sum(counts.values()) or shots
            observed = {key: value / total for key, value in counts.items()}

        return {
            "tracking_id": job["public_tracking_token_hash"],
            "status": job["status"],
            "experiment_id": job["experiment_type"],
            "backend_name": job.get("backend_name"),
            "provider_job_id": job.get("provider_job_id"),
            "shots": shots,
            "counts": counts,
            "observed_probabilities": observed,
            "ideal_probabilities": metadata["ideal_probabilities"],
            "error": job.get("error"),
            "created_at": job.get("created_at"),
            "updated_at": job.get("updated_at"),
        }