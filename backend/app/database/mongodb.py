from datetime import datetime,timezone
from typing import Any
import time

from pymongo import ASCENDING, MongoClient
from pymongo.errors import PyMongoError

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
        db.lessons.create_index([("order",ASCENDING)])

        db.quantum_jobs.create_index([("public_tracking_token_hash",ASCENDING)], unique=True)
        db.quantum_jobs.create_index([("provider_job_id", ASCENDING)])
        db.quantum_jobs.create_index(
            [("idempotency_key_hash", ASCENDING)], unique=True,
            partialFilterExpression={"idempotency_key_hash": {"$type": "string"}},
        )
        db.quantum_jobs.create_index([("status", ASCENDING)])
        db.experiments.create_index([("experiment_id", ASCENDING)], unique=True)
        db.quantum_jobs.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)

        db.hardware_quota.create_index([("quota_date", ASCENDING)], unique=True)
        db.feedback.create_index([("created_at", ASCENDING)])

    @classmethod
    def health(cls)->bool:
        try:
            cls.db().command("ping")
            return True
        except (PyMongoError, ExternalServiceError):
            return False


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
