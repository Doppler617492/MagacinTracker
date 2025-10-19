"""Worker picking endpoints with shortage tracking."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app_common.db import get_db

from .auth_test import get_current_user
from ..schemas import (
    CatalogLookupResponse,
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
from ..schemas.partial import (
    PartialCompleteRequest,
    PartialCompleteResponse,
    MarkirajPreostaloRequest,
)
from ..services.catalog import CatalogService
from ..services.shortage import ShortageService

router = APIRouter()


@router.get("/catalog/lookup", response_model=CatalogLookupResponse)
async def lookup_by_code(
    code: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> CatalogLookupResponse:
    """
    Lookup article by barcode or SKU.
    
    Workers can use this endpoint to verify items before picking.
    """
    service = CatalogService(db)
    return await service.lookup(code)


@router.post("/worker/tasks/{stavka_id}/manual-entry", response_model=ManualQuantityResponse)
async def manual_quantity_entry(
    stavka_id: UUID,
    request: ManualQuantityRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> ManualQuantityResponse:
    """
    Manual quantity entry without barcode scanning.
    
    This is the main endpoint for manual-only picking operations.
    Supports partial quantities and closing items with reasons.
    """
    service = ShortageService(db)
    user_id = UUID(current_user.get("sub") or current_user.get("id"))
    
    try:
        return await service.enter_manual_quantity(stavka_id, request, user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/worker/tasks/{stavka_id}/pick-by-code", response_model=PickByCodeResponse)
async def pick_by_code(
    stavka_id: UUID,
    request: PickByCodeRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> PickByCodeResponse:
    """
    Record a pick using barcode or SKU scan.
    
    Validates that the scanned code matches the item's article,
    then increments picked_qty. Idempotent via operation_id.
    """
    service = ShortageService(db)
    user_id = UUID(current_user.get("sub") or current_user.get("id"))
    
    try:
        return await service.pick_by_code(stavka_id, request, user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/worker/tasks/{stavka_id}/short-pick", response_model=ShortPickResponse)
async def short_pick(
    stavka_id: UUID,
    request: ShortPickRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> ShortPickResponse:
    """
    Record a short pick (less than requested quantity).
    
    Used when the worker cannot find the full quantity.
    Sets discrepancy_status to 'short_pick'.
    """
    service = ShortageService(db)
    user_id = UUID(current_user.get("sub") or current_user.get("id"))
    
    try:
        return await service.record_short_pick(stavka_id, request, user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/worker/tasks/{stavka_id}/not-found", response_model=NotFoundResponse)
async def not_found(
    stavka_id: UUID,
    request: NotFoundRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> NotFoundResponse:
    """
    Mark an item as not found (picked_qty = 0).
    
    Used when the worker cannot locate the item at all.
    Sets discrepancy_status to 'not_found'.
    """
    service = ShortageService(db)
    user_id = UUID(current_user.get("sub") or current_user.get("id"))
    
    try:
        return await service.record_not_found(stavka_id, request, user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/worker/tasks/{stavka_id}/partial-complete", response_model=PartialCompleteResponse)
async def partial_complete(
    stavka_id: UUID,
    request: PartialCompleteRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> PartialCompleteResponse:
    """
    Complete task with partial quantity (Manhattan-style exception handling).
    
    Serbian: Završi zadatak sa djelimičnom količinom
    
    This endpoint allows workers to complete a task with a quantity less than requested,
    providing a reason for the discrepancy. This is the Manhattan Active WMS pattern
    for exception handling.
    
    Args:
        stavka_id: Trebovanje stavka ID
        request: Partial completion details (količina_pronađena, razlog, razlog_tekst)
        
    Returns:
        Updated stavka with is_partial=true, procenat_ispunjenja, status
        
    Raises:
        400: If količina_pronađena > količina_tražena or validation fails
        404: If stavka not found
    """
    service = ShortageService(db)
    user_id = UUID(current_user.get("sub") or current_user.get("id"))
    
    try:
        return await service.complete_partial(stavka_id, request, user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}",
        )


@router.post("/worker/tasks/{stavka_id}/markiraj-preostalo")
async def markiraj_preostalo(
    stavka_id: UUID,
    request: MarkirajPreostaloRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Mark remaining quantity as 0 (Serbian: Markiraj preostalo = 0).
    
    This is a convenience endpoint that sets količina_pronađena to the current
    picked_qty and marks the item as partial with a reason.
    
    Typical use: Worker has scanned/entered some items but cannot find the rest.
    Instead of manually entering the quantity found, they can use this endpoint
    to automatically set it and provide a reason.
    
    Args:
        stavka_id: Trebovanje stavka ID
        request: Reason for not finding remaining items
        
    Returns:
        Updated stavka marked as partial
    """
    service = ShortageService(db)
    user_id = UUID(current_user.get("sub") or current_user.get("id"))
    
    try:
        return await service.markiraj_preostalo(stavka_id, request, user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/worker/documents/{trebovanje_id}/complete", response_model=CompleteDocumentResponse)
async def complete_document(
    trebovanje_id: UUID,
    request: CompleteDocumentRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> CompleteDocumentResponse:
    """
    Complete a trebovanje document.
    
    If there are items with shortages, the worker must set confirm_incomplete=true.
    Otherwise, the request will be rejected with a 400 error.
    """
    service = ShortageService(db)
    user_id = UUID(current_user.get("sub") or current_user.get("id"))
    
    try:
        return await service.complete_document(trebovanje_id, request, user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

