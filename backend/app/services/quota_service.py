from datetime import date,datetime,timezone
from pymongo import ReturnDocument
from pymongo.errors import PyMongoError

from app.config import get_settings
from app.database.mongodb import Mongo
from app.errors import ExternalServiceError,QuotaExceededError

class QuotaService:
    @staticmethod
    def reserve_submission()->None:
        settings = get_settings()
        today = date.today().isoformat()
        try:
            document = Mongo.db().hardware_quota.find_one_and_update(
                {'quota_date',today},
                {
                    "$setOnInsert":{
                        "quota_date":today,
                        "submitted_count": 0,
                        "reserved_count": 0,
                        "active_job_count": 0,
                        "configured_limit": settings.ibm_max_daily_jobs,
                        "updated_at": datetime.now(timezone.utc),
                    },
                    "$inc": {"reserved_count": 1},
                },
                upset=True,
                return_document=ReturnDocument.AFTER,
            )
        except PyMongoError as exc:
            raise ExternalServiceError("Unable to check hardware quota.") from exc

        if document["reserved_count"] > settings.ibm_max_daily_jobs:
            QuotaService.release_reservation(today)
            raise QuotaExceededError()

    @staticmethod
    def confirm_submission() -> None:
        today = date.today().isoformat()
        Mongo.db().hardware_quota.update_one(
            {"quota_date": today},
            {
                "$inc": {"reserved_count": -1, "submitted_count": 1, "active_job_count": 1},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )

    @staticmethod
    def release_reservation(quota_date: str| None=None)-> None:
        today = quota_date or date.today().isoformat()
        Mongo.db().hardware_quota.update_one(
            {"quota_date": today, "reserved_count": {"$gt": 0}},
            {
                "$inc": {"reserved_count": -1},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )

    @staticmethod
    def release_active_job() -> None:
        today = date.today().isoformat()
        Mongo.db().hardware_quota.update_one(
            {"quota_date": today, "active_job_count": {"$gt": 0}},
            {
                "$inc": {"active_job_count": -1},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )

    @staticmethod
    def status() -> dict:
        settings = get_settings()
        today = date.today().isoformat()
        document = Mongo.db().hardware_quota.find_one({"quota_date": today}) or {}
        submitted = int(document.get("submitted_count", 0))
        active = int(document.get("active_job_count", 0))
        return {
            "hardware_enabled": settings.ibm_hardware_enabled,
            "daily_limit": settings.ibm_max_daily_jobs,
            "submitted_today": submitted,
            "remaining_today": max(0, settings.ibm_max_daily_jobs - submitted),
            "active_jobs": active,
            "active_limit": settings.ibm_max_active_jobs,
            "max_shots": settings.ibm_max_shots,
        }

    