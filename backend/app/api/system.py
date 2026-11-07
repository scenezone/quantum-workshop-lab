from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database.models import PublicConfig
from app.database.mongodb import Mongo
from app.quantum.catalog import noise_profile_catalog
from app.services.quota_service import QuotaService

router = APIRouter(tags=["system"])


@router.get("/api/health")
def health() -> JSONResponse:
    connected = Mongo.health()
    if connected is None:
        database = "disabled"
    else:
        database = "connected" if connected else "unavailable"
    healthy = connected is not False
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={
            "status": "ok" if healthy else "unavailable",
            "database": database,
            "environment": get_settings().app_env,
        },
    )


@router.get("/api/config/public", response_model=PublicConfig)
def public_config() -> dict:
    settings = get_settings()
    database = Mongo.available()
    return {
        "hardware_enabled": QuotaService.hardware_available(),
        "max_simulator_shots": settings.max_simulator_shots,
        "max_hardware_shots": settings.ibm_max_shots,
        "default_shots": settings.default_shots,
        "database_enabled": database,
        "feedback_enabled": database,
        "sessions_enabled": database,
        "live_ai_enabled": settings.llm_enabled,
        "noise_profiles": noise_profile_catalog(),
    }
