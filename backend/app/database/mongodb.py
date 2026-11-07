import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from pymongo import ASCENDING, MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.config import get_settings
from app.errors import ExternalServiceError, FeatureDisabledError

logger = logging.getLogger(__name__)


class Mongo:
    client: MongoClient | None = None

    @staticmethod
    def enabled() -> bool:
        return get_settings().database_enabled

    @classmethod
    def available(cls) -> bool:
        return cls.client is not None

    @classmethod
    def connect(cls) -> None:
        settings = get_settings()
        if not settings.database_enabled:
            logger.info("MONGODB_URI is empty; running in simulator-only mode without a database")
            return
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
            if not get_settings().database_enabled:
                raise FeatureDisabledError(
                    "This feature needs a database, and this workshop runs in simulator-only mode."
                )
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
        db.hardware_results.create_index([("experiment_id", ASCENDING)], unique=True)

        # The quota ledger is a single document; this per-date index is no longer used.
        _drop_index(db.hardware_quota, "quota_date_1")

        retention_days = get_settings().feedback_retention_days
        _drop_index(db.feedback, "created_at_1")
        if retention_days:
            # MongoDB rejects two indexes on the same key with different options.
            _drop_index(db.feedback, "feedback_created")
            _replace_index(
                db.feedback,
                "feedback_retention",
                [("created_at", ASCENDING)],
                expireAfterSeconds=retention_days * 86400,
            )
        else:
            _drop_index(db.feedback, "feedback_retention")
            db.feedback.create_index([("created_at", ASCENDING)], name="feedback_created")
        db.feedback.create_index([("session_code", ASCENDING)])

        db.workshop_sessions.create_index([("code", ASCENDING)], unique=True)
        db.workshop_sessions.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)
        db.session_participants.create_index(
            [("session_code", ASCENDING), ("participant_id", ASCENDING)], unique=True
        )
        db.session_participants.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)

    @classmethod
    def health(cls) -> bool | None:
        """True when connected, False when unreachable, None in simulator-only mode."""
        if not get_settings().database_enabled:
            return None
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


def _drop_index(collection, name: str) -> None:
    try:
        if name in collection.index_information():
            collection.drop_index(name)
    except PyMongoError:
        logger.warning("Unable to drop index %s", name, exc_info=True)


def _replace_index(collection, name: str, keys, **options) -> None:
    """Recreate a named index when its options changed, such as a new TTL."""
    existing = collection.index_information().get(name)
    if existing and existing.get("expireAfterSeconds") != options.get("expireAfterSeconds"):
        collection.drop_index(name)
    collection.create_index(keys, name=name, **options)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
