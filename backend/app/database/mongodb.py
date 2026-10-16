from datetime import datetime,timezone
from typing import Any

from pymongo import ASCENDING, MongoClient, ReturnDocument
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
        )
        cls.client.admin.command("ping")
        cls.ensure_indexes()

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
        db.quantum_jobs.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)

        db.hardware_quota.create_index([("quota_date", ASCENDING)], unique=True)
        db.feedback.create_index([("created_at", ASCENDING)])

    @classmethod
    def health(cls)->bool:
        try:
            cls.db().command("ping")
            return True
        except PyMongoError:
            return False


def utcnow() -> datetime:
    return datetime.now(timezone.utc)