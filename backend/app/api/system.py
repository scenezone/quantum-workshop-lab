from fastapi import APIRouter

from app.config import get_settings
from app.database.mongodb import Mongo
from app.services.quota_service import QuotaService

router = APIRouter(tags=["system"])


@router.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "database": "connected" if Mongo.health() else "unavailable",
        "environment": get_settings().app_env,
    }


@router.get("/api/config/public")
def public_config() -> dict:
    settings = get_settings()
    return {
        "hardware_enabled": settings.ibm_hardware_enabled,
        "max_simulator_shots": settings.max_simulator_shots,
        "max_hardware_shots": settings.ibm_max_shots,
        "default_shots": settings.default_shots,
    }