"""
Manhattan-style partial completion service methods
Extension to ShortageService
"""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app_common.events import publish
from app_common.logging import get_logger

from ..models import TrebovanjeStavka, UserAccount
from ..models.enums import AuditAction, TrebovanjeItemStatus
from ..schemas.partial import (
    PartialCompleteRequest,
    PartialCompleteResponse,
    MarkirajPreostaloRequest,
    get_reason_display,
)
from .audit import record_audit

logger = get_logger(__name__)

async def complete_partial(
    session: AsyncSession,
    stavka_id: UUID,
    request: PartialCompleteRequest,
    user_id: UUID,
) -> PartialCompleteResponse:
    """
    Complete a task with partial quantity (Manhattan-style exception handling).
    
    Serbian: Završi zadatak sa djelimičnom količinom
    
    This implements the Manhattan Active WMS pattern for exception handling:
    1. Worker enters actual quantity found
    2. Selects reason from dropdown
    3. System calculates % completion
    4. Marks as "Završeno (djelimično)" if < 100%
    
    Args:
        session: Database session
        stavka_id: Trebovanje stavka ID
        request: Partial completion details
        user_id: Current user ID
        
    Returns:
        PartialCompleteResponse with updated stavka data
        
    Raises:
        ValueError: If validation fails
    """
    # 1. Load stavka with related data
    stmt = (
        select(TrebovanjeStavka)
        .options(joinedload(TrebovanjeStavka.trebovanje))
        .where(TrebovanjeStavka.id == stavka_id)
    )
    result = await session.execute(stmt)
    stavka = result.scalar_one_or_none()
    
    if not stavka:
        raise ValueError(f"Stavka {stavka_id} not found")
    
    # 2. Validate količina_pronađena
    količina_tražena = float(stavka.kolicina_trazena)
    količina_pronađena = float(request.količina_pronađena)
    
    if količina_pronađena > količina_tražena:
        raise ValueError(
            f"Količina pronađena ({količina_pronađena}) ne može biti veća od tražene ({količina_tražena})"
        )
    
    if količina_pronađena < 0:
        raise ValueError("Količina ne može biti manja od 0")
    
    # 3. Calculate procenat_ispunjenja
    if količina_tražena > 0:
        procenat = round((količina_pronađena / količina_tražena) * 100, 2)
    else:
        procenat = 100.0
    
    # 4. Determine if partial
    is_partial = količina_pronađena < količina_tražena
    
    # 5. Update stavka fields
    stavka.količina_pronađena = request.količina_pronađena
    stavka.razlog = request.razlog if is_partial else None
    stavka.razlog_tekst = request.razlog_tekst if is_partial else None
    stavka.is_partial = is_partial
    stavka.procenat_ispunjenja = Decimal(str(procenat))
    stavka.picked_qty = request.količina_pronađena  # Sync with existing field
    stavka.missing_qty = količina_tražena - količina_pronađena
    stavka.status = TrebovanjeItemStatus.done
    stavka.completed_at = datetime.now(timezone.utc)
    stavka.completed_by_id = user_id
    
    # 6. Get user info for response
    stmt_user = select(UserAccount).where(UserAccount.id == user_id)
    result_user = await session.execute(stmt_user)
    user = result_user.scalar_one_or_none()
    user_name = f"{user.first_name} {user.last_name}" if user else "Unknown"
    
    # 7. Record audit event
    await record_audit(
        session,
        action=AuditAction.ITEM_PARTIAL if is_partial else AuditAction.ITEM_CLOSED,
        actor_id=user_id,
        entity_type="trebovanje_stavka",
        entity_id=str(stavka_id),
        payload={
            "stavka_id": str(stavka_id),
            "količina_tražena": količina_tražena,
            "količina_pronađena": količina_pronađena,
            "procenat_ispunjenja": procenat,
            "is_partial": is_partial,
            "razlog": request.razlog.value if is_partial else None,
            "razlog_tekst": request.razlog_tekst,
            "operation_id": request.operation_id,
        },
    )
    
    # 8. Commit to database
    await session.commit()
    await session.refresh(stavka)
    
    # 9. Publish Redis event for real-time updates
    await publish(
        "task_item_completed",
        {
            "stavka_id": str(stavka_id),
            "trebovanje_id": str(stavka.trebovanje_id),
            "is_partial": is_partial,
            "procenat_ispunjenja": procenat,
            "completed_by": user_name,
            "completed_at": stavka.completed_at.isoformat(),
        },
    )
    
    # 10. Build response
    status_serbian = "Završeno (djelimično)" if is_partial else "Završeno"
    message = f"Stavka označena kao {status_serbian.lower()}"
    if is_partial:
        message = f"{message} - {get_reason_display(request.razlog, request.razlog_tekst)}"
    
    return PartialCompleteResponse(
        stavka_id=stavka.id,
        količina_tražena=Decimal(str(količina_tražena)),
        količina_pronađena=Decimal(str(količina_pronađena)),
        razlog=request.razlog if is_partial else None,
        razlog_tekst=request.razlog_tekst if is_partial else None,
        is_partial=is_partial,
        procenat_ispunjenja=stavka.procenat_ispunjenja,
        status=stavka.status.value,
        status_serbian=status_serbian,
        message=message,
        completed_at=stavka.completed_at,
        completed_by=user_name,
    )


async def markiraj_preostalo(
    session: AsyncSession,
    stavka_id: UUID,
    request: MarkirajPreostaloRequest,
    user_id: UUID,
):
    """
    Mark remaining quantity as 0 (Serbian: Markiraj preostalo = 0).
    
    This is a convenience method that:
    1. Takes current picked_qty as količina_pronađena
    2. Marks remaining as unavailable with reason
    3. Completes the item as partial
    
    Typical use case:
    - Worker scanned/entered 5 items
    - Cannot find remaining 5
    - Instead of manually entering "5", clicks "Markiraj preostalo = 0"
    - Selects reason "Nije pronađeno"
    - Item marked as partial completion with količina_pronađena=5
    
    Args:
        session: Database session
        stavka_id: Trebovanje stavka ID
        request: Reason for marking remaining as 0
        user_id: Current user ID
        
    Returns:
        PartialCompleteResponse
    """
    # 1. Load stavka
    stmt = (
        select(TrebovanjeStavka)
        .options(joinedload(TrebovanjeStavka.trebovanje))
        .where(TrebovanjeStavka.id == stavka_id)
    )
    result = await session.execute(stmt)
    stavka = result.scalar_one_or_none()
    
    if not stavka:
        raise ValueError(f"Stavka {stavka_id} not found")
    
    # 2. Use current picked_qty as količina_pronađena
    količina_pronađena = float(stavka.picked_qty)
    
    # 3. Create PartialCompleteRequest
    partial_request = PartialCompleteRequest(
        stavka_id=stavka_id,
        količina_pronađena=Decimal(str(količina_pronađena)),
        razlog=request.razlog,
        razlog_tekst=request.razlog_tekst,
        operation_id=request.operation_id,
    )
    
    # 4. Call complete_partial
    return await complete_partial(session, stavka_id, partial_request, user_id)

