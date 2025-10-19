"""
Receiving Service - Business logic for inbound workflow
Manhattan Active WMS pattern with exception handling
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app_common.events import publish
from app_common.logging import get_logger

from ..models.receiving import ReceivingHeader, ReceivingItem
from ..models.enums import (
    AuditAction,
    ReceivingStatus,
    ReceivingReason,
    ReceivingItemStatus
)
from ..schemas.receiving import (
    ReceiveItemRequest,
    ReceiveItemResponse,
    CompleteReceivingRequest,
    CompleteReceivingResponse,
    StartReceivingRequest,
)
from .audit import record_audit

logger = get_logger(__name__)


class ReceivingService:
    """
    Service for handling receiving (prijem robe) operations
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def start_receiving(
        self,
        receiving_id: UUID,
        request: StartReceivingRequest,
        user_id: UUID
    ) -> ReceivingHeader:
        """
        Start receiving process (set status to 'u_toku')
        
        Serbian: Započni prijem
        """
        # Load receiving header
        stmt = (
            select(ReceivingHeader)
            .options(joinedload(ReceivingHeader.items))
            .where(ReceivingHeader.id == receiving_id)
        )
        result = await self.session.execute(stmt)
        receiving = result.scalar_one_or_none()
        
        if not receiving:
            raise ValueError(f"Receiving {receiving_id} not found")
        
        if receiving.status != ReceivingStatus.NOVO:
            raise ValueError(f"Receiving already started (status: {receiving.status})")
        
        # Update status
        receiving.status = ReceivingStatus.U_TOKU
        receiving.started_at = datetime.now(timezone.utc)
        receiving.started_by_id = user_id
        
        # Record audit
        await record_audit(
            self.session,
            action=AuditAction.LOGIN_SUCCESS,  # TODO: Add RECEIVING_STARTED
            actor_id=user_id,
            entity_type="receiving_header",
            entity_id=str(receiving_id),
            payload={
                "broj_prijema": receiving.broj_prijema,
                "operation_id": request.operation_id
            }
        )
        
        # Commit
        await self.session.commit()
        await self.session.refresh(receiving)
        
        # Publish event
        await publish("receiving_started", {
            "receiving_id": str(receiving_id),
            "broj_prijema": receiving.broj_prijema,
            "started_by": str(user_id),
        })
        
        logger.info(
            "receiving.started",
            receiving_id=str(receiving_id),
            broj_prijema=receiving.broj_prijema,
            user_id=str(user_id)
        )
        
        return receiving
    
    async def receive_item(
        self,
        item_id: UUID,
        request: ReceiveItemRequest,
        user_id: UUID
    ) -> ReceiveItemResponse:
        """
        Receive an item (record quantity)
        
        Serbian: Primi stavku
        
        Args:
            item_id: Receiving item ID
            request: Quantity, reason, note, photos
            user_id: Current user
            
        Returns:
            Updated item with variance info
            
        Raises:
            ValueError: If validation fails
        """
        # Load item with header
        stmt = (
            select(ReceivingItem)
            .options(joinedload(ReceivingItem.header))
            .where(ReceivingItem.id == item_id)
        )
        result = await self.session.execute(stmt)
        item = result.scalar_one_or_none()
        
        if not item:
            raise ValueError(f"Receiving item {item_id} not found")
        
        # Validate receiving is in progress
        if item.header.status not in [ReceivingStatus.NOVO, ReceivingStatus.U_TOKU]:
            raise ValueError(f"Cannot receive item - receiving status is {item.header.status}")
        
        # Update quantities
        kolicina_trazena = float(item.kolicina_trazena)
        kolicina_primljena = float(request.quantity)
        variance = kolicina_primljena - kolicina_trazena
        
        item.kolicina_primljena = request.quantity
        item.razlog = request.razlog
        item.napomena = request.napomena
        
        # Add photo attachments
        if request.photo_ids:
            current_attachments = item.attachments or []
            item.attachments = current_attachments + request.photo_ids
        
        # Update status
        item.status = ReceivingItemStatus.GOTOVO
        item.completed_at = datetime.now(timezone.utc)
        item.completed_by_id = user_id
        
        # If header is still 'novo', set to 'u_toku'
        if item.header.status == ReceivingStatus.NOVO:
            item.header.status = ReceivingStatus.U_TOKU
            item.header.started_at = datetime.now(timezone.utc)
            item.header.started_by_id = user_id
        
        # Record audit
        await record_audit(
            self.session,
            action=AuditAction.MANUAL_QTY_SAVED,  # Reuse existing action
            actor_id=user_id,
            entity_type="receiving_item",
            entity_id=str(item_id),
            payload={
                "item_id": str(item_id),
                "kolicina_trazena": kolicina_trazena,
                "kolicina_primljena": kolicina_primljena,
                "variance": variance,
                "razlog": request.razlog.value if request.razlog else None,
                "napomena": request.napomena,
                "photos_count": len(request.photo_ids) if request.photo_ids else 0,
                "operation_id": request.operation_id,
            }
        )
        
        # Commit
        await self.session.commit()
        await self.session.refresh(item)
        
        # Publish event for real-time updates
        await publish("receiving_item_updated", {
            "item_id": str(item_id),
            "receiving_id": str(item.header_id),
            "broj_prijema": item.header.broj_prijema,
            "kolicina_primljena": kolicina_primljena,
            "variance": variance,
            "is_partial": item.is_partial,
            "is_overage": item.is_overage,
        })
        
        # Build message
        if variance == 0:
            message = f"Stavka primljena potpuno ({kolicina_primljena})"
        elif variance > 0:
            message = f"Višak: primljeno {kolicina_primljena}, traženo {kolicina_trazena}"
        else:
            message = f"Manjak: primljeno {kolicina_primljena}, traženo {kolicina_trazena}"
        
        if request.razlog:
            message += f" - Razlog: {item.razlog_serbian}"
        
        logger.info(
            "receiving.item_received",
            item_id=str(item_id),
            variance=variance,
            is_partial=item.is_partial,
            razlog=request.razlog.value if request.razlog else None
        )
        
        return ReceiveItemResponse(
            item_id=item.id,
            kolicina_primljena=item.kolicina_primljena,
            kolicina_trazena=item.kolicina_trazena,
            variance=variance,
            razlog=item.razlog,
            completion_percentage=item.completion_percentage,
            status=item.status,
            message=message
        )
    
    async def complete_receiving(
        self,
        receiving_id: UUID,
        request: CompleteReceivingRequest,
        user_id: UUID
    ) -> CompleteReceivingResponse:
        """
        Complete receiving document
        
        Serbian: Završi prijem
        
        Determines if completion is full or partial based on items.
        Always allowed (Manhattan pattern - partial completions OK).
        """
        # Load receiving with all items
        stmt = (
            select(ReceivingHeader)
            .options(joinedload(ReceivingHeader.items))
            .where(ReceivingHeader.id == receiving_id)
        )
        result = await self.session.execute(stmt)
        receiving = result.scalar_one_or_none()
        
        if not receiving:
            raise ValueError(f"Receiving {receiving_id} not found")
        
        if receiving.status in [ReceivingStatus.ZAVRSENO, ReceivingStatus.ZAVRSENO_DJELIMICNO]:
            raise ValueError(f"Receiving already completed")
        
        # Calculate statistics
        total_items = len(receiving.items)
        items_full = sum(
            1 for item in receiving.items
            if item.kolicina_primljena == item.kolicina_trazena
        )
        items_partial = sum(
            1 for item in receiving.items
            if item.is_partial
        )
        items_overage = sum(
            1 for item in receiving.items
            if item.is_overage
        )
        
        # Determine final status
        is_partial = receiving.is_partial
        final_status = (
            ReceivingStatus.ZAVRSENO_DJELIMICNO
            if is_partial
            else ReceivingStatus.ZAVRSENO
        )
        
        # Update receiving
        receiving.status = final_status
        receiving.completed_at = datetime.now(timezone.utc)
        receiving.completed_by_id = user_id
        
        # Record audit
        await record_audit(
            self.session,
            action=AuditAction.DOC_COMPLETED_PARTIAL if is_partial else AuditAction.DOC_COMPLETED_FULL,
            actor_id=user_id,
            entity_type="receiving_header",
            entity_id=str(receiving_id),
            payload={
                "broj_prijema": receiving.broj_prijema,
                "total_items": total_items,
                "items_full": items_full,
                "items_partial": items_partial,
                "items_overage": items_overage,
                "completion_percentage": receiving.completion_percentage,
                "is_partial": is_partial,
                "operation_id": request.operation_id,
            }
        )
        
        # Commit
        await self.session.commit()
        await self.session.refresh(receiving)
        
        # Publish event
        await publish("receiving_completed", {
            "receiving_id": str(receiving_id),
            "broj_prijema": receiving.broj_prijema,
            "status": final_status.value,
            "is_partial": is_partial,
            "completion_percentage": receiving.completion_percentage,
            "completed_by": str(user_id),
        })
        
        # Build message
        if is_partial:
            message = f"Prijem završen djelimično - {receiving.completion_percentage}% primljeno"
        else:
            message = f"Prijem uspješno završen - sve stavke primljene"
        
        logger.info(
            "receiving.completed",
            receiving_id=str(receiving_id),
            status=final_status.value,
            is_partial=is_partial,
            completion_percentage=receiving.completion_percentage
        )
        
        return CompleteReceivingResponse(
            receiving_id=receiving.id,
            broj_prijema=receiving.broj_prijema,
            status=final_status,
            total_items=total_items,
            items_full=items_full,
            items_partial=items_partial,
            items_overage=items_overage,
            completion_percentage=receiving.completion_percentage,
            message=message,
            completed_at=receiving.completed_at
        )

