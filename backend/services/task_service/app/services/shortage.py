"""Service for handling shortage tracking and picking operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app_common.events import publish
from app_common.logging import get_logger

from ..models import Trebovanje, TrebovanjeStavka, Zaduznica, ZaduznicaStavka
from ..models.enums import AuditAction, DiscrepancyStatus, TrebovanjeItemStatus, TrebovanjeStatus
from ..schemas.shortage import (
    CompleteDocumentRequest,
    CompleteDocumentResponse,
    ManualQuantityRequest,
    ManualQuantityResponse,
    NotFoundRequest,
    NotFoundResponse,
    PickByCodeRequest,
    PickByCodeResponse,
    ShortPickRequest,
    ShortPickResponse,
)
from .audit import record_audit
from .catalog import CatalogService

logger = get_logger(__name__)

TV_CHANNEL = "tv:delta"


class ShortageService:
    """Handles picking operations with shortage tracking."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.catalog_service = CatalogService(session)
    
    async def pick_by_code(
        self, 
        stavka_id: UUID, 
        request: PickByCodeRequest,
        user_id: UUID,
    ) -> PickByCodeResponse:
        """
        Record a pick using barcode or SKU.
        
        Validates that the scanned code matches the item's article,
        then increments picked_qty.
        """
        # Load the stavka
        stmt = (
            select(TrebovanjeStavka)
            .options(joinedload(TrebovanjeStavka.trebovanje))
            .where(TrebovanjeStavka.id == stavka_id)
        )
        result = await self.session.execute(stmt)
        stavka = result.scalar_one_or_none()
        
        if not stavka:
            raise ValueError(f"Stavka {stavka_id} not found")
        
        # Lookup the article by code
        catalog_response = await self.catalog_service.lookup(request.code)
        
        if not catalog_response.artikal_id:
            # Code not found in catalog
            await record_audit(
                self.session,
                action=AuditAction.SCAN_MISMATCH,
                actor_id=user_id,
                entity_type="trebovanje_stavka",
                entity_id=str(stavka_id),
                payload={"stavka_id": str(stavka_id), "code": request.code, "reason": "not_in_catalog"},
            )
            raise ValueError(f"Code '{request.code}' not found in catalog")
        
        # Check if the scanned article matches the stavka's article
        if stavka.artikal_id and catalog_response.artikal_id != stavka.artikal_id:
            # Mismatch!
            await record_audit(
                self.session,
                action=AuditAction.SCAN_MISMATCH,
                actor_id=user_id,
                entity_type="trebovanje_stavka",
                entity_id=str(stavka_id),
                payload={
                    "stavka_id": str(stavka_id),
                    "code": request.code,
                    "expected_artikal_id": str(stavka.artikal_id),
                    "scanned_artikal_id": str(catalog_response.artikal_id),
                },
            )
            raise ValueError(
                f"Scanned item '{catalog_response.naziv}' does not match expected item '{stavka.naziv}'"
            )
        
        # Increment picked_qty
        new_picked = float(stavka.picked_qty) + request.quantity
        required = float(stavka.kolicina_trazena)
        
        # Cap to required quantity (no overpick by default)
        if new_picked > required:
            new_picked = required
        
        stavka.picked_qty = new_picked
        stavka.last_scanned_code = request.code
        
        # Update missing_qty
        stavka.missing_qty = max(0, required - new_picked)
        
        # Update discrepancy_status
        if new_picked >= required:
            stavka.discrepancy_status = DiscrepancyStatus.none
        elif stavka.discrepancy_status == DiscrepancyStatus.none:
            # Don't override if already set to not_found, etc.
            pass
        
        await self.session.commit()
        await self.session.refresh(stavka)
        
        # Audit
        await record_audit(
            self.session,
            action=AuditAction.SCAN_OK,
            actor_id=user_id,
            entity_type="trebovanje_stavka",
            entity_id=str(stavka_id),
            payload={
                "stavka_id": str(stavka_id),
                "code": request.code,
                "quantity": request.quantity,
                "new_picked": float(new_picked),
                "operation_id": request.operation_id,
            },
        )
        
        return PickByCodeResponse(
            stavka_id=stavka.id,
            picked_qty=float(stavka.picked_qty),
            required_qty=required,
            missing_qty=float(stavka.missing_qty),
            discrepancy_status=stavka.discrepancy_status,
            needs_barcode=stavka.needs_barcode,
            matched_code=request.code,
            message=f"Picked {request.quantity}. Total: {new_picked}/{required}",
        )
    
    async def record_short_pick(
        self,
        stavka_id: UUID,
        request: ShortPickRequest,
        user_id: UUID,
    ) -> ShortPickResponse:
        """Record a short pick (less than requested quantity)."""
        stmt = select(TrebovanjeStavka).where(TrebovanjeStavka.id == stavka_id)
        result = await self.session.execute(stmt)
        stavka = result.scalar_one_or_none()
        
        if not stavka:
            raise ValueError(f"Stavka {stavka_id} not found")
        
        required = float(stavka.kolicina_trazena)
        
        stavka.picked_qty = request.actual_qty
        stavka.missing_qty = max(0, required - request.actual_qty)
        stavka.discrepancy_status = DiscrepancyStatus.short_pick
        stavka.discrepancy_reason = request.reason
        
        await self.session.commit()
        await self.session.refresh(stavka)
        
        # Audit
        await record_audit(
            self.session,
            action=AuditAction.SHORT_PICK_RECORDED,
            actor_id=user_id,
            entity_type="trebovanje_stavka",
            entity_id=str(stavka_id),
            payload={
                "stavka_id": str(stavka_id),
                "actual_qty": request.actual_qty,
                "required_qty": required,
                "missing_qty": float(stavka.missing_qty),
                "reason": request.reason,
                "operation_id": request.operation_id,
            },
        )
        
        return ShortPickResponse(
            stavka_id=stavka.id,
            picked_qty=float(stavka.picked_qty),
            required_qty=required,
            missing_qty=float(stavka.missing_qty),
            discrepancy_status=stavka.discrepancy_status,
            message=f"Short pick recorded: {request.actual_qty}/{required}",
        )
    
    async def record_not_found(
        self,
        stavka_id: UUID,
        request: NotFoundRequest,
        user_id: UUID,
    ) -> NotFoundResponse:
        """Mark an item as not found (0 picked)."""
        stmt = select(TrebovanjeStavka).where(TrebovanjeStavka.id == stavka_id)
        result = await self.session.execute(stmt)
        stavka = result.scalar_one_or_none()
        
        if not stavka:
            raise ValueError(f"Stavka {stavka_id} not found")
        
        required = float(stavka.kolicina_trazena)
        
        stavka.picked_qty = 0
        stavka.missing_qty = required
        stavka.discrepancy_status = DiscrepancyStatus.not_found
        stavka.discrepancy_reason = request.reason
        
        await self.session.commit()
        await self.session.refresh(stavka)
        
        # Audit
        await record_audit(
            self.session,
            action=AuditAction.NOT_FOUND_RECORDED,
            actor_id=user_id,
            entity_type="trebovanje_stavka",
            entity_id=str(stavka_id),
            payload={
                "stavka_id": str(stavka_id),
                "required_qty": required,
                "reason": request.reason,
                "operation_id": request.operation_id,
            },
        )
        
        return NotFoundResponse(
            stavka_id=stavka.id,
            picked_qty=0,
            required_qty=required,
            discrepancy_status=stavka.discrepancy_status,
            message=f"Item marked as not found",
        )
    
    async def complete_document(
        self,
        trebovanje_id: UUID,
        request: CompleteDocumentRequest,
        user_id: UUID,
    ) -> CompleteDocumentResponse:
        """
        Complete a trebovanje document.
        
        If there are shortages and confirm_incomplete is False, raises an error.
        Otherwise marks the document as done and records completion data.
        """
        # Load trebovanje with all stavke
        stmt = (
            select(Trebovanje)
            .options(joinedload(Trebovanje.stavke))
            .where(Trebovanje.id == trebovanje_id)
        )
        result = await self.session.execute(stmt)
        trebovanje = result.unique().scalar_one_or_none()
        
        if not trebovanje:
            raise ValueError(f"Trebovanje {trebovanje_id} not found")
        
        # Calculate totals
        total_items = len(trebovanje.stavke)
        completed_items = sum(
            1 for s in trebovanje.stavke 
            if float(s.picked_qty) >= float(s.kolicina_trazena) or s.discrepancy_status != DiscrepancyStatus.none
        )
        items_with_shortages = sum(
            1 for s in trebovanje.stavke 
            if s.discrepancy_status != DiscrepancyStatus.none or float(s.missing_qty) > 0
        )
        total_shortage_qty = sum(float(s.missing_qty) for s in trebovanje.stavke)
        
        # Check if incomplete
        if items_with_shortages > 0 and not request.confirm_incomplete:
            raise ValueError(
                f"Document has {items_with_shortages} items with shortages. "
                f"Set confirm_incomplete=true to complete anyway."
            )
        
        # Update individual stavka statuses
        for stavka in trebovanje.stavke:
            if float(stavka.picked_qty) >= float(stavka.kolicina_trazena):
                stavka.status = TrebovanjeItemStatus.done
            elif float(stavka.picked_qty) > 0:
                stavka.status = TrebovanjeItemStatus.in_progress
            elif stavka.discrepancy_status != DiscrepancyStatus.none:
                # Item has shortage/discrepancy but was processed
                stavka.status = TrebovanjeItemStatus.done
            # If picked_qty = 0 and no discrepancy, keep as assigned
        
        # Mark as completed
        trebovanje.status = TrebovanjeStatus.done
        trebovanje.closed_by = user_id
        trebovanje.closed_at = datetime.now(timezone.utc)
        
        # Update all related Zaduznica statuses to done
        from ..models.zaduznica import Zaduznica, ZaduznicaStatus
        zaduznica_stmt = select(Zaduznica).where(Zaduznica.trebovanje_id == trebovanje_id)
        zaduznica_result = await self.session.execute(zaduznica_stmt)
        zaduznice = zaduznica_result.scalars().all()
        
        for zaduznica in zaduznice:
            zaduznica.status = ZaduznicaStatus.done
            zaduznica.updated_at = datetime.now(timezone.utc)
        
        await self.session.commit()
        
        # Audit
        await record_audit(
            self.session,
            action=AuditAction.DOC_COMPLETED_INCOMPLETE if items_with_shortages > 0 else AuditAction.manual_complete,
            actor_id=user_id,
            entity_type="trebovanje",
            entity_id=str(trebovanje_id),
            payload={
                "trebovanje_id": str(trebovanje_id),
                "total_items": total_items,
                "completed_items": completed_items,
                "items_with_shortages": items_with_shortages,
                "total_shortage_qty": total_shortage_qty,
                "operation_id": request.operation_id,
            },
        )
        
        # Publish TV update for real-time sync
        await publish(
            TV_CHANNEL,
            {
                "type": "document_complete",
                "trebovanje_id": str(trebovanje_id),
                "status": "done",
                "completed_items": completed_items,
                "total_items": total_items,
                "items_with_shortages": items_with_shortages,
            },
        )
        
        return CompleteDocumentResponse(
            trebovanje_id=trebovanje.id,
            total_items=total_items,
            completed_items=completed_items,
            items_with_shortages=items_with_shortages,
            total_shortage_qty=total_shortage_qty,
            status="done",
            message=f"Document completed with {items_with_shortages} shortage(s)" if items_with_shortages > 0 
                   else "Document completed successfully",
        )
    
    async def enter_manual_quantity(
        self,
        stavka_id: UUID,
        request: ManualQuantityRequest,
        user_id: UUID,
    ) -> ManualQuantityResponse:
        """
        Manual quantity entry without barcode scanning.
        
        This is the main endpoint for manual-only picking operations.
        Supports partial quantities and closing items with reasons.
        """
        # Load the stavka
        stmt = select(TrebovanjeStavka).where(TrebovanjeStavka.id == stavka_id)
        result = await self.session.execute(stmt)
        stavka = result.scalar_one_or_none()
        
        if not stavka:
            raise ValueError(f"Stavka {stavka_id} not found")
        
        required = float(stavka.kolicina_trazena)
        
        # Validate quantity doesn't exceed required (ALLOW_OVERPICK=false)
        if request.quantity > required:
            raise ValueError(f"Quantity {request.quantity} exceeds required {required}")
        
        # Check if reason is mandatory
        reason_required = request.quantity < required or (request.close_item and request.quantity == 0)
        # Treat empty string, None, or whitespace-only as missing reason
        has_valid_reason = request.reason and request.reason.strip()
        
        # Log for debugging
        from app_common.logging import get_logger
        logger = get_logger(__name__)
        logger.info(
            "manual_quantity_validation",
            stavka_id=str(stavka_id),
            quantity=request.quantity,
            required=required,
            close_item=request.close_item,
            reason=request.reason,
            reason_required=reason_required,
            has_valid_reason=bool(has_valid_reason),
        )
        
        if reason_required and not has_valid_reason:
            raise ValueError("Reason is mandatory when quantity < required or closing item with 0")
        
        # Update the stavka
        stavka.picked_qty = request.quantity
        stavka.missing_qty = max(0, required - request.quantity)
        stavka.discrepancy_reason = request.reason
        # Note: we could store request.note in a new field if needed
        
        # Determine status
        status = "novo"
        if request.quantity == required:
            # Fully picked
            status = "zatvoreno"
            stavka.discrepancy_status = DiscrepancyStatus.none
        elif request.close_item:
            # Closed with shortage
            status = "djelimicno"
            stavka.discrepancy_status = DiscrepancyStatus.short_pick
        elif request.quantity > 0:
            # In progress
            status = "u_toku"
            stavka.discrepancy_status = DiscrepancyStatus.none
        else:
            # Zero quantity, not closed
            status = "novo"
            stavka.discrepancy_status = DiscrepancyStatus.none
        
        await self.session.commit()
        await self.session.refresh(stavka)
        
        # Audit
        audit_action = AuditAction.MANUAL_QTY_SAVED
        if status == "djelimicno":
            audit_action = AuditAction.ITEM_PARTIAL
        elif status == "zatvoreno":
            audit_action = AuditAction.ITEM_CLOSED
        
        await record_audit(
            self.session,
            action=audit_action,
            actor_id=user_id,
            entity_type="trebovanje_stavka",
            entity_id=str(stavka_id),
            payload={
                "stavka_id": str(stavka_id),
                "quantity": request.quantity,
                "required_qty": required,
                "close_item": request.close_item,
                "reason": request.reason,
                "note": request.note,
                "status": status,
                "operation_id": request.operation_id,
            },
        )
        
        # Build message
        if status == "zatvoreno":
            msg = f"Stavka završena: {request.quantity}/{required}"
        elif status == "djelimicno":
            msg = f"Stavka djelimično završena: {request.quantity}/{required}. Razlog: {request.reason}"
        elif status == "u_toku":
            msg = f"Količina unesena: {request.quantity}/{required}. Stavka u toku."
        else:
            msg = f"Količina unesena: {request.quantity}"
        
        return ManualQuantityResponse(
            stavka_id=stavka.id,
            picked_qty=float(stavka.picked_qty),
            required_qty=required,
            missing_qty=float(stavka.missing_qty),
            status=status,
            discrepancy_status=stavka.discrepancy_status,
            message=msg,
        )


