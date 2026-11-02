from fastapi import APIRouter

from app.database.mongodb import Mongo
from app.quantum.circuits import get_metadata
from app.services.quota_service import QuotaService

router = APIRouter(prefix="/api/hardware", tags=["hardware"])


@router.get("/status")
def hardware_status() -> dict:
    return QuotaService.status()


@router.get("/saved/{experiment_id}")
def saved_hardware_result(experiment_id: str) -> dict | None:
    metadata = get_metadata(experiment_id)
    record = Mongo.db().hardware_results.find_one({"experiment_id": experiment_id})
    if not record:
        return None
    counts = record.get("counts") or {}
    total = sum(counts.values()) or 1
    return {
        "experiment_id": experiment_id,
        "backend": "ibm_quantum_recorded",
        "backend_name": record.get("backend_name"),
        "shots": record.get("shots", sum(counts.values())),
        "counts": counts,
        "observed_probabilities": {key: value / total for key, value in counts.items()},
        "ideal_probabilities": metadata["ideal_probabilities"],
        "provider_job_id": None,
        "tracking_id": None,
        "recorded_at": record.get("recorded_at").isoformat() if record.get("recorded_at") else None,
    }
