"""Team management router - proxies to task service."""
from typing import Any, Dict, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from httpx import AsyncClient

from app_common.logging import get_logger
from ..dependencies.http import get_task_client
from ..services.auth import require_roles

logger = get_logger(__name__)
router = APIRouter()


def _forward_headers(request: Request) -> dict:
    """Extract and forward necessary headers"""
    headers = {}
    auth_header = request.headers.get("Authorization")
    if auth_header:
        headers["Authorization"] = auth_header
    return headers


@router.get("/teams")
async def list_teams(
    request: Request,
    task_client: AsyncClient = Depends(get_task_client),
    _: None = Depends(require_roles(["ADMIN", "SEF", "MENADZER"])),
) -> List[Dict[str, Any]]:
    """Get list of all teams."""
    response = await task_client.get("/api/teams", headers=_forward_headers(request))
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.get("/teams/{team_id}")
async def get_team(
    team_id: UUID,
    request: Request,
    task_client: AsyncClient = Depends(get_task_client),
    _: None = Depends(require_roles(["ADMIN", "SEF", "MENADZER"])),
) -> Dict[str, Any]:
    """Get team details."""
    response = await task_client.get(f"/api/teams/{team_id}", headers=_forward_headers(request))
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Team not found")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.get("/teams/{team_id}/performance")
async def get_team_performance(
    team_id: UUID,
    request: Request,
    task_client: AsyncClient = Depends(get_task_client),
    _: None = Depends(require_roles(["ADMIN", "SEF", "MENADZER"])),
) -> Dict[str, Any]:
    """Get team performance metrics."""
    response = await task_client.get(f"/api/teams/{team_id}/performance", headers=_forward_headers(request))
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Team not found")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.get("/dashboard/live")
async def get_live_dashboard(
    request: Request,
    scope: str = "day",
    task_client: AsyncClient = Depends(get_task_client),
    _: None = Depends(require_roles(["ADMIN", "SEF", "MENADZER"])),
) -> Dict[str, Any]:
    """Get live dashboard with team and shift information."""
    response = await task_client.get(f"/api/dashboard/live?scope={scope}", headers=_forward_headers(request))
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.post("/teams", status_code=201)
async def create_team(
    request: Request,
    task_client: AsyncClient = Depends(get_task_client),
    _: None = Depends(require_roles(["ADMIN", "SEF", "MENADZER"])),
) -> Dict[str, Any]:
    """Create a new team."""
    body = await request.json()
    response = await task_client.post("/api/teams", json=body, headers=_forward_headers(request))
    if response.status_code not in (200, 201):
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.put("/teams/{team_id}")
async def update_team(
    team_id: UUID,
    request: Request,
    task_client: AsyncClient = Depends(get_task_client),
    _: None = Depends(require_roles(["ADMIN", "SEF", "MENADZER"])),
) -> Dict[str, Any]:
    """Update an existing team."""
    body = await request.json()
    response = await task_client.put(f"/api/teams/{team_id}", json=body, headers=_forward_headers(request))
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Team not found")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.delete("/teams/{team_id}", status_code=204)
async def delete_team(
    team_id: UUID,
    request: Request,
    task_client: AsyncClient = Depends(get_task_client),
    _: None = Depends(require_roles(["ADMIN", "SEF"])),
) -> None:
    """Delete (deactivate) a team."""
    response = await task_client.delete(f"/api/teams/{team_id}", headers=_forward_headers(request))
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Team not found")
    if response.status_code != 204:
        raise HTTPException(status_code=response.status_code, detail=response.text)

