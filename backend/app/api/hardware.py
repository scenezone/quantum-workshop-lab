from fastapi import APIRouter

from app.services.quota_service import QuotaService

router = APIRouter(prefix="/api/hardware", tags=["hardware"])


@router.get("/status")
def hardware_status() -> dict:
    return QuotaService.status()
