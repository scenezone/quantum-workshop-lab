from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database.mongodb import Mongo
from app.quantum.ibm_runtime import IBMRuntimeClient

router = APIRouter(tags=["system"])


@router.get("/api/health")
def health() -> JSONResponse:
    connected = Mongo.health()
    return JSONResponse(
        status_code=200 if connected else 503,
        content={
            "status": "ok" if connected else "unavailable",
            "database": "connected" if connected else "unavailable",
            "environment": get_settings().app_env,
        },
    )


@router.get("/api/config/public")
def public_config() -> dict:
    settings = get_settings()
    return {
        "hardware_enabled": settings.ibm_hardware_enabled
        and IBMRuntimeClient.configured_account_count() > 0,
        "hardware_demo_verified": settings.ibm_hardware_demo_verified,
        "max_simulator_shots": settings.max_simulator_shots,
        "max_hardware_shots": settings.ibm_max_shots,
        "default_shots": settings.default_shots,
    }
