from fastapi import APIRouter, Depends, HTTPException

from contextwise.api.dependencies import get_database
from contextwise.application.health_service import HealthService
from contextwise.infrastructure.database import Database

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def health_live() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/ready")
async def health_ready(database: Database = Depends(get_database)) -> dict[str, str]:
    service = HealthService(database)
    if not await service.is_ready():
        raise HTTPException(status_code=503, detail={"status": "not ready"})
    return {"status": "ready"}
