import time
from datetime import datetime, timedelta, timezone
from typing import Any

from pymongo import ASCENDING, MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.config import get_settings
from app.errors import ExternalServiceError


class Mongo:
    client: MongoClient | None = None

    @classmethod
    def connect(cls) -> None:
        settings = get_settings()
        cls.client = MongoClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=settings.mongodb_timeout_ms,
            connectTimeoutMS=settings.mongodb_timeout_ms,
            maxPoolSize=20,
            tz_aware=True,
        )
        for attempt in range(settings.mongodb_connect_attempts):
            try:
                cls.client.admin.command("ping")
                cls.ensure_indexes()
                return
            except PyMongoError:
                if attempt == settings.mongodb_connect_attempts - 1:
                    cls.close()
                    raise
                time.sleep(min(attempt + 1, 5))

    @classmethod
    def close(cls) -> None:
        if cls.client:
            cls.client.close()
            cls.client = None

    @classmethod
    def db(cls) -> Any:
        if cls.client is None:
            raise ExternalServiceError("Database is not initialized.")
        return cls.client[get_settings().mongodb_database]

    @classmethod
    def ensure_indexes(cls) -> None:
        db = cls.db()
        db.lessons.create_index([("lesson_id", ASCENDING)], unique=True)
        db.lessons.create_index([("order", ASCENDING)])

        db.quantum_jobs.create_index([("public_tracking_token_hash", ASCENDING)], unique=True)
        db.quantum_jobs.create_index([("provider_job_id", ASCENDING)])
        db.quantum_jobs.create_index(
            [("idempotency_key_hash", ASCENDING)],
            unique=True,
            partialFilterExpression={"idempotency_key_hash": {"$type": "string"}},
        )
        db.quantum_jobs.create_index([("status", ASCENDING)])
        db.experiments.create_index([("experiment_id", ASCENDING)], unique=True)
        db.quantum_jobs.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)

        db.hardware_quota.create_index([("quota_date", ASCENDING)], unique=True)
        db.feedback.create_index([("created_at", ASCENDING)])

    @classmethod
    def health(cls) -> bool:
        try:
            cls.db().command("ping")
            return True
        except (PyMongoError, ExternalServiceError):
            return False

    @classmethod
    def acquire_lease(cls, name: str, owner: str, lease_seconds: int = 60) -> bool:
        """Acquire a short MongoDB-backed lease shared by all API workers."""
        now = utcnow()
        try:
            lease = cls.db().runtime_locks.find_one_and_update(
                {
                    "_id": name,
                    "$or": [
                        {"expires_at": {"$lte": now}},
                        {"owner": owner},
                    ],
                },
                {"$set": {"owner": owner, "expires_at": now + timedelta(seconds=lease_seconds)}},
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
        except DuplicateKeyError:
            # Another worker owns the unexpired lease.
            return False
        return bool(lease and lease.get("owner") == owner)

    @classmethod
    def renew_lease(cls, name: str, owner: str, lease_seconds: int = 60) -> bool:
        result = cls.db().runtime_locks.update_one(
            {"_id": name, "owner": owner},
            {"$set": {"expires_at": utcnow() + timedelta(seconds=lease_seconds)}},
        )
        return result.modified_count == 1 or result.matched_count == 1

    @classmethod
    def release_lease(cls, name: str, owner: str) -> None:
        cls.db().runtime_locks.delete_one({"_id": name, "owner": owner})


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
