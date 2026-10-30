"""Atomic reservations including active jobs from previous UTC days."""

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.config import get_settings
from app.database.mongodb import Mongo, utcnow
from app.errors import ExternalServiceError, QuotaExceededError


class QuotaService:
    LEDGER_ID = "hardware-ledger-v1"

    @staticmethod
    def reserve_submission(job_id: str, quota_date: str) -> None:
        settings = get_settings()
        collection = Mongo.db().hardware_quota
        try:
            try:
                collection.update_one(
                    {"_id": QuotaService.LEDGER_ID},
                    {"$setOnInsert": {"entries": []}},
                    upsert=True,
                )
            except DuplicateKeyError:
                pass
            collection.update_one(
                {"_id": QuotaService.LEDGER_ID},
                {"$pull": {"entries": {"active": False, "quota_date": {"$ne": quota_date}}}},
            )

            def count(condition):
                return {
                    "$size": {
                        "$filter": {
                            "input": "$entries",
                            "as": "entry",
                            "cond": condition,
                        }
                    }
                }

            document = collection.find_one_and_update(
                {
                    "_id": QuotaService.LEDGER_ID,
                    "entries.job_id": {"$ne": job_id},
                    "$expr": {
                        "$and": [
                            {
                                "$lt": [
                                    count({"$eq": ["$$entry.quota_date", quota_date]}),
                                    settings.ibm_max_daily_jobs,
                                ]
                            },
                            {
                                "$lt": [
                                    count({"$eq": ["$$entry.active", True]}),
                                    settings.ibm_max_active_jobs,
                                ]
                            },
                        ]
                    },
                },
                {
                    "$push": {
                        "entries": {
                            "job_id": job_id,
                            "quota_date": quota_date,
                            "state": "reserved",
                            "active": True,
                        }
                    },
                    "$set": {"updated_at": utcnow()},
                },
                return_document=ReturnDocument.AFTER,
            )
            if document is None:
                existing = collection.find_one(
                    {
                        "_id": QuotaService.LEDGER_ID,
                        "entries.job_id": job_id,
                    }
                )
                if existing is None:
                    raise QuotaExceededError()
        except PyMongoError as exc:
            raise ExternalServiceError("Unable to check hardware quota.") from exc

    @staticmethod
    def confirm_submission(job_id: str) -> None:
        Mongo.db().hardware_quota.update_one(
            {"_id": QuotaService.LEDGER_ID, "entries.job_id": job_id},
            {"$set": {"entries.$.state": "submitted", "updated_at": utcnow()}},
        )

    @staticmethod
    def release_reservation(job_id: str) -> None:
        Mongo.db().hardware_quota.update_one(
            {"_id": QuotaService.LEDGER_ID},
            {
                "$pull": {"entries": {"job_id": job_id, "state": "reserved"}},
                "$set": {"updated_at": utcnow()},
            },
        )

    @staticmethod
    def release_active_job(job_id: str) -> None:
        Mongo.db().hardware_quota.update_one(
            {"_id": QuotaService.LEDGER_ID, "entries.job_id": job_id},
            {"$set": {"entries.$.active": False, "updated_at": utcnow()}},
        )

    @staticmethod
    def status() -> dict:
        settings = get_settings()
        document = Mongo.db().hardware_quota.find_one({"_id": QuotaService.LEDGER_ID}) or {}
        entries = document.get("entries", [])
        today = utcnow().date().isoformat()
        todays_entries = [entry for entry in entries if entry["quota_date"] == today]
        return {
            "hardware_enabled": settings.ibm_hardware_enabled,
            "daily_limit": settings.ibm_max_daily_jobs,
            "submitted_today": sum(entry["state"] == "submitted" for entry in todays_entries),
            "remaining_today": max(0, settings.ibm_max_daily_jobs - len(todays_entries)),
            "active_jobs": sum(bool(entry["active"]) for entry in entries),
            "active_limit": settings.ibm_max_active_jobs,
            "max_shots": settings.ibm_max_shots,
        }
