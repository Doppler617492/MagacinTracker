"""Team management endpoints."""
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import UUID
import uuid as uuid_module

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app_common.db import get_db
from app_common.config import get_settings
from app_common.logging import get_logger
from ..models import Team, UserAccount, Zaduznica, ScanLog
from ..models.enums import Role, ZaduznicaStatus
from ..services.shift import get_shift_status, get_all_shifts_status

settings = get_settings()
logger = get_logger(__name__)
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_any_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> dict:
    """Get user from JWT token - accepts both device tokens and regular user tokens"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None:
            raise credentials_exception
    except JWTError as exc:  # noqa: BLE001
        raise credentials_exception from exc
    
    # Check if this is a device token (non-UUID format)
    try:
        uuid_module.UUID(user_id)
        is_device = False
    except ValueError:
        is_device = True
    
    # For device tokens, just validate the role
    if is_device:
        if role not in ["MENADZER", "ADMIN", "SEF"]:
            raise credentials_exception
        return {
            "id": user_id,
            "role": role,
            "device_id": user_id,
        }
    
    # For regular user tokens, look up in database
    result = await db.execute(
        text("SELECT id, email, first_name, last_name, role, is_active FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    )
    user_row = result.fetchone()
    
    if user_row is None or not user_row.is_active:
        raise credentials_exception
    
    return {
        "id": str(user_row.id),
        "email": user_row.email,
        "first_name": user_row.first_name,
        "last_name": user_row.last_name,
        "role": user_row.role,
    }


class TeamMember(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str


class TeamResponse(BaseModel):
    id: str
    name: str
    shift: str
    active: bool
    worker1: TeamMember
    worker2: TeamMember
    created_at: datetime


class TeamCreateRequest(BaseModel):
    name: str
    worker1_id: str
    worker2_id: str
    shift: str  # 'A' or 'B'


class TeamUpdateRequest(BaseModel):
    name: str | None = None
    worker1_id: str | None = None
    worker2_id: str | None = None
    shift: str | None = None
    active: bool | None = None


class TeamPerformance(BaseModel):
    team_id: str
    team_name: str
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    completion_rate: float
    total_scans: int
    average_speed_per_hour: float


@router.get("/teams", response_model=List[TeamResponse])
async def list_teams(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_any_user),
) -> List[TeamResponse]:
    """Get list of all teams with member details."""
    
    stmt = select(Team).where(Team.active == True).order_by(Team.shift, Team.name)
    result = await db.execute(stmt)
    teams = result.scalars().all()
    
    team_list = []
    for team in teams:
        team_list.append(TeamResponse(
            id=str(team.id),
            name=team.name,
            shift=team.shift,
            active=team.active,
            worker1=TeamMember(
                id=str(team.worker1.id),
                first_name=team.worker1.first_name,
                last_name=team.worker1.last_name,
                email=team.worker1.email,
            ),
            worker2=TeamMember(
                id=str(team.worker2.id),
                first_name=team.worker2.first_name,
                last_name=team.worker2.last_name,
                email=team.worker2.email,
            ),
            created_at=team.created_at,
        ))
    
    return team_list


@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_any_user),
) -> TeamResponse:
    """Get team details by ID."""
    
    stmt = select(Team).where(Team.id == team_id)
    result = await db.execute(stmt)
    team = result.scalar_one_or_none()
    
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    
    return TeamResponse(
        id=str(team.id),
        name=team.name,
        shift=team.shift,
        active=team.active,
        worker1=TeamMember(
            id=str(team.worker1.id),
            first_name=team.worker1.first_name,
            last_name=team.worker1.last_name,
            email=team.worker1.email,
        ),
        worker2=TeamMember(
            id=str(team.worker2.id),
            first_name=team.worker2.first_name,
            last_name=team.worker2.last_name,
            email=team.worker2.email,
        ),
        created_at=team.created_at,
    )


@router.get("/teams/{team_id}/performance", response_model=TeamPerformance)
async def get_team_performance(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_any_user),
) -> TeamPerformance:
    """Get performance metrics for a specific team."""
    
    # Get team
    team_stmt = select(Team).where(Team.id == team_id)
    team_result = await db.execute(team_stmt)
    team = team_result.scalar_one_or_none()
    
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    
    # Get zaduznica stats for this team
    zaduznica_stats_stmt = (
        select(
            func.count(Zaduznica.id).label('total_tasks'),
            func.count(Zaduznica.id).filter(Zaduznica.status == ZaduznicaStatus.done).label('completed'),
            func.count(Zaduznica.id).filter(Zaduznica.status == ZaduznicaStatus.in_progress).label('in_progress'),
        )
        .where(Zaduznica.team_id == team_id)
    )
    
    stats_result = await db.execute(zaduznica_stats_stmt)
    stats = stats_result.one()
    
    # Get scan count for team members
    scan_count_stmt = (
        select(func.count(ScanLog.id))
        .where(ScanLog.user_id.in_([team.worker1_id, team.worker2_id]))
    )
    scan_result = await db.execute(scan_count_stmt)
    total_scans = scan_result.scalar() or 0
    
    # Calculate metrics
    total_tasks = stats.total_tasks or 0
    completed_tasks = stats.completed or 0
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
    
    # Mock average speed (would need time tracking for real calculation)
    average_speed_per_hour = total_scans / 8.0 if total_scans > 0 else 0.0
    
    return TeamPerformance(
        team_id=str(team_id),
        team_name=team.name,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        in_progress_tasks=stats.in_progress or 0,
        completion_rate=round(completion_rate, 2),
        total_scans=total_scans,
        average_speed_per_hour=round(average_speed_per_hour, 2),
    )


@router.get("/dashboard/live")
async def get_live_dashboard(
    scope: str = "day",  # day or shift
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_any_user),
) -> Dict[str, Any]:
    """Get live dashboard data with team and shift information."""
    
    # Get all active teams
    teams_stmt = select(Team).where(Team.active == True)
    teams_result = await db.execute(teams_stmt)
    teams = teams_result.scalars().all()
    
    # Get shift status
    shift_status = get_all_shifts_status()
    
    # Build team progress
    team_progress = []
    total_tasks = 0
    completed_tasks = 0
    
    for team in teams:
        # Get zaduznica stats for this team
        stats_stmt = (
            select(
                func.count(Zaduznica.id).label('total'),
                func.count(Zaduznica.id).filter(Zaduznica.status == ZaduznicaStatus.done).label('completed'),
            )
            .where(Zaduznica.team_id == team.id)
        )
        
        stats_result = await db.execute(stats_stmt)
        stats = stats_result.one()
        
        team_total = stats.total or 0
        team_completed = stats.completed or 0
        team_completion = team_completed / team_total if team_total > 0 else 0.0
        
        total_tasks += team_total
        completed_tasks += team_completed
        
        team_progress.append({
            'team': team.name,
            'team_id': str(team.id),
            'members': [
                f"{team.worker1.first_name} {team.worker1.last_name}",
                f"{team.worker2.first_name} {team.worker2.last_name}",
            ],
            'completion': round(team_completion, 2),
            'shift': team.shift,
            'tasks_total': team_total,
            'tasks_completed': team_completed,
        })
    
    return {
        'total_tasks_today': total_tasks,
        'completed_tasks': completed_tasks,
        'active_teams': len([t for t in teams if t.shift == shift_status['active_shift']]) if shift_status['active_shift'] else 0,
        'team_progress': team_progress,
        'shift_status': {
            'active_shift': shift_status['active_shift'],
            'shift_a': shift_status['shift_a_status'],
            'shift_b': shift_status['shift_b_status'],
            'current_time': shift_status['current_time'],
        },
        'generated_at': datetime.now(timezone.utc).isoformat(),
    }


@router.post("/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    request: TeamCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_any_user),
) -> TeamResponse:
    """Create a new team. Only ADMIN, SEF, and MENADZER can create teams."""
    
    # Check permissions
    if current_user["role"] not in ["ADMIN", "SEF", "MENADZER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can create teams"
        )
    
    # Validate shift
    if request.shift not in ['A', 'B']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shift must be 'A' or 'B'"
        )
    
    # Validate workers exist and are magacioneri
    worker1_stmt = select(UserAccount).where(UserAccount.id == uuid_module.UUID(request.worker1_id))
    worker1_result = await db.execute(worker1_stmt)
    worker1 = worker1_result.scalar_one_or_none()
    
    if not worker1 or worker1.role != "MAGACIONER":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Worker 1 not found or is not a magacioner"
        )
    
    worker2_stmt = select(UserAccount).where(UserAccount.id == uuid_module.UUID(request.worker2_id))
    worker2_result = await db.execute(worker2_stmt)
    worker2 = worker2_result.scalar_one_or_none()
    
    if not worker2 or worker2.role != "MAGACIONER":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Worker 2 not found or is not a magacioner"
        )
    
    # Check if workers are already in another active team
    existing_team_stmt = select(Team).where(
        ((Team.worker1_id == worker1.id) | (Team.worker2_id == worker1.id) |
         (Team.worker1_id == worker2.id) | (Team.worker2_id == worker2.id)) &
        (Team.active == True)
    )
    existing_team_result = await db.execute(existing_team_stmt)
    existing_team = existing_team_result.scalar_one_or_none()
    
    if existing_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"One or both workers are already in an active team: {existing_team.name}"
        )
    
    # Check if team name already exists
    name_check_stmt = select(Team).where(Team.name == request.name)
    name_check_result = await db.execute(name_check_stmt)
    if name_check_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Team name '{request.name}' already exists"
        )
    
    # Create team
    new_team = Team(
        id=uuid_module.uuid4(),
        name=request.name,
        worker1_id=worker1.id,
        worker2_id=worker2.id,
        shift=request.shift,
        active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    db.add(new_team)
    await db.commit()
    await db.refresh(new_team)
    
    # Load relationships
    team_stmt = select(Team).where(Team.id == new_team.id)
    team_result = await db.execute(team_stmt)
    team = team_result.scalar_one()
    
    return TeamResponse(
        id=str(team.id),
        name=team.name,
        shift=team.shift,
        active=team.active,
        worker1=TeamMember(
            id=str(team.worker1.id),
            first_name=team.worker1.first_name,
            last_name=team.worker1.last_name,
            email=team.worker1.email,
        ),
        worker2=TeamMember(
            id=str(team.worker2.id),
            first_name=team.worker2.first_name,
            last_name=team.worker2.last_name,
            email=team.worker2.email,
        ),
        created_at=team.created_at,
    )


@router.put("/teams/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: UUID,
    request: TeamUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_any_user),
) -> TeamResponse:
    """Update an existing team. Only ADMIN, SEF, and MENADZER can update teams."""
    
    # Check permissions
    if current_user["role"] not in ["ADMIN", "SEF", "MENADZER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can update teams"
        )
    
    # Get team
    team_stmt = select(Team).where(Team.id == team_id)
    team_result = await db.execute(team_stmt)
    team = team_result.scalar_one_or_none()
    
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    
    # Update fields
    if request.name is not None:
        # Check if new name already exists (excluding current team)
        name_check_stmt = select(Team).where(Team.name == request.name, Team.id != team_id)
        name_check_result = await db.execute(name_check_stmt)
        if name_check_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Team name '{request.name}' already exists"
            )
        team.name = request.name
    
    if request.worker1_id is not None:
        worker1_stmt = select(UserAccount).where(UserAccount.id == uuid_module.UUID(request.worker1_id))
        worker1_result = await db.execute(worker1_stmt)
        worker1 = worker1_result.scalar_one_or_none()
        
        if not worker1 or worker1.role != "MAGACIONER":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Worker 1 not found or is not a magacioner"
            )
        team.worker1_id = worker1.id
    
    if request.worker2_id is not None:
        worker2_stmt = select(UserAccount).where(UserAccount.id == uuid_module.UUID(request.worker2_id))
        worker2_result = await db.execute(worker2_stmt)
        worker2 = worker2_result.scalar_one_or_none()
        
        if not worker2 or worker2.role != "MAGACIONER":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Worker 2 not found or is not a magacioner"
            )
        team.worker2_id = worker2.id
    
    if request.shift is not None:
        if request.shift not in ['A', 'B']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shift must be 'A' or 'B'"
            )
        team.shift = request.shift
    
    if request.active is not None:
        team.active = request.active
    
    team.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(team)
    
    return TeamResponse(
        id=str(team.id),
        name=team.name,
        shift=team.shift,
        active=team.active,
        worker1=TeamMember(
            id=str(team.worker1.id),
            first_name=team.worker1.first_name,
            last_name=team.worker1.last_name,
            email=team.worker1.email,
        ),
        worker2=TeamMember(
            id=str(team.worker2.id),
            first_name=team.worker2.first_name,
            last_name=team.worker2.last_name,
            email=team.worker2.email,
        ),
        created_at=team.created_at,
    )


@router.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_any_user),
) -> None:
    """Delete (deactivate) a team. Only ADMIN and SEF can delete teams."""
    
    # Check permissions
    if current_user["role"] not in ["ADMIN", "SEF"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and shift managers can delete teams"
        )
    
    # Get team
    team_stmt = select(Team).where(Team.id == team_id)
    team_result = await db.execute(team_stmt)
    team = team_result.scalar_one_or_none()
    
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    
    # Check if team has active zaduznice
    active_zaduznice_stmt = select(func.count(Zaduznica.id)).where(
        Zaduznica.team_id == team_id,
        Zaduznica.status.in_([ZaduznicaStatus.assigned, ZaduznicaStatus.in_progress])
    )
    active_count_result = await db.execute(active_zaduznice_stmt)
    active_count = active_count_result.scalar()
    
    if active_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete team with {active_count} active tasks. Complete or reassign tasks first."
        )
    
    # Soft delete (deactivate)
    team.active = False
    team.updated_at = datetime.now(timezone.utc)
    
    await db.commit()

