from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dependencies import UserContext, require_roles
from ..enums import Role
from ..schemas import CatalogStatusResponse, CatalogSyncSummary, CatalogSyncTriggerRequest
from ..services.sync import get_sync_status, runner

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.post("/sync", response_model=CatalogSyncSummary)
async def trigger_catalog_sync(
    payload: CatalogSyncTriggerRequest | None = None,
    user: UserContext = Depends(require_roles(Role.menadzer, Role.sef)),
) -> CatalogSyncSummary:
    trigger = payload or CatalogSyncTriggerRequest()
    return await runner.trigger(initiated_by=user.id, trigger=trigger)


@router.get("/status", response_model=CatalogStatusResponse)
async def catalog_sync_status(
    user: UserContext = Depends(require_roles(Role.menadzer, Role.sef)),
) -> CatalogStatusResponse:
    return get_sync_status()
