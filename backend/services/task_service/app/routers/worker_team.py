"""Worker team endpoints for PWA."""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app_common.db import get_db
from app_common.logging import get_logger
from ..dependencies.auth import require_roles, UserContext
from ..models import Team, UserAccount
from ..models.enums import Role
from ..services.shift import get_shift_status

logger = get_logger(__name__)
router = APIRouter()


class WorkerTeamInfo(BaseModel):
    team_id: str
    team_name: str
    shift: str
    partner_id: str
    partner_name: str
    partner_online: bool
    shift_status: Dict[str, Any]


@router.get("/worker/my-team", response_model=Optional[WorkerTeamInfo])
async def get_my_team(
    user: UserContext = Depends(require_roles([Role.MAGACIONER])),
    db: AsyncSession = Depends(get_db),
) -> Optional[WorkerTeamInfo]:
    """Get the current worker's team information."""
    
    # Find team where user is a member
    stmt = select(Team).where(
        (Team.worker1_id == user.id) | (Team.worker2_id == user.id)
    ).where(Team.active == True)
    
    result = await db.execute(stmt)
    team = result.scalar_one_or_none()
    
    if not team:
        return None
    
    # Determine partner
    partner_id = team.get_partner_id(user.id)
    if not partner_id:
        return None
    
    # Get partner info
    partner_stmt = select(UserAccount).where(UserAccount.id == partner_id)
    partner_result = await db.execute(partner_stmt)
    partner = partner_result.scalar_one_or_none()
    
    if not partner:
        return None
    
    # Get shift status
    shift_status = get_shift_status(team.shift)
    
    # Check if partner is online (mock for now - would need session tracking)
    partner_online = True  # TODO: Implement real online status
    
    return WorkerTeamInfo(
        team_id=str(team.id),
        team_name=team.name,
        shift=team.shift,
        partner_id=str(partner.id),
        partner_name=f"{partner.first_name} {partner.last_name}",
        partner_online=partner_online,
        shift_status=shift_status,
    )

