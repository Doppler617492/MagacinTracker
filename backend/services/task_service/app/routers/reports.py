"""Reports endpoints for shortage tracking and analytics."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app_common.db import get_db

from ..dependencies import require_roles
from ..models import Magacin, Radnja, Trebovanje, TrebovanjeStavka, UserAccount
from ..models.enums import DiscrepancyStatus, Role
from ..schemas.shortage import ShortageReportItem

router = APIRouter()


@router.get("/reports/shortages")
async def get_shortage_report(
    from_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    radnja_id: Optional[UUID] = Query(None, description="Filter by store"),
    magacioner_id: Optional[UUID] = Query(None, description="Filter by worker"),
    discrepancy_status: Optional[str] = Query(None, description="Filter by status"),
    format: str = Query("json", regex="^(json|csv)$", description="Output format"),
    user=Depends(require_roles([Role.MENADZER, Role.SEF])),
    db: AsyncSession = Depends(get_db),
):
    """
    Get shortage report with filters.
    
    Returns all items with shortages (missing_qty > 0 or discrepancy_status != none).
    Can export as JSON or CSV.
    """
    # Build query
    stmt = (
        select(
            Trebovanje.dokument_broj,
            Trebovanje.datum,
            Radnja.naziv.label("radnja_naziv"),
            Magacin.naziv.label("magacin_naziv"),
            TrebovanjeStavka.artikl_sifra,
            TrebovanjeStavka.naziv.label("artikal_naziv"),
            TrebovanjeStavka.kolicina_trazena,
            TrebovanjeStavka.picked_qty,
            TrebovanjeStavka.missing_qty,
            TrebovanjeStavka.discrepancy_status,
            TrebovanjeStavka.discrepancy_reason,
            UserAccount.first_name,
            UserAccount.last_name,
            Trebovanje.closed_at,
        )
        .join(TrebovanjeStavka, Trebovanje.id == TrebovanjeStavka.trebovanje_id)
        .join(Radnja, Trebovanje.radnja_id == Radnja.id)
        .join(Magacin, Trebovanje.magacin_id == Magacin.id)
        .outerjoin(UserAccount, Trebovanje.closed_by == UserAccount.id)
        .where(
            or_(
                TrebovanjeStavka.missing_qty > 0,
                TrebovanjeStavka.discrepancy_status != DiscrepancyStatus.none,
            )
        )
    )
    
    # Apply filters
    if from_date:
        stmt = stmt.where(Trebovanje.datum >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        stmt = stmt.where(Trebovanje.datum <= datetime.combine(to_date, datetime.max.time()))
    if radnja_id:
        stmt = stmt.where(Trebovanje.radnja_id == radnja_id)
    if magacioner_id:
        stmt = stmt.where(Trebovanje.closed_by == magacioner_id)
    if discrepancy_status:
        stmt = stmt.where(TrebovanjeStavka.discrepancy_status == discrepancy_status)
    
    stmt = stmt.order_by(Trebovanje.datum.desc(), Trebovanje.dokument_broj)
    
    result = await db.execute(stmt)
    rows = result.all()
    
    # Convert to response models
    items = [
        ShortageReportItem(
            trebovanje_dokument_broj=row.dokument_broj,
            trebovanje_datum=row.datum.strftime("%Y-%m-%d %H:%M"),
            radnja_naziv=row.radnja_naziv,
            magacin_naziv=row.magacin_naziv,
            artikal_sifra=row.artikl_sifra,
            artikal_naziv=row.artikal_naziv,
            required_qty=float(row.kolicina_trazena),
            picked_qty=float(row.picked_qty),
            missing_qty=float(row.missing_qty),
            discrepancy_status=row.discrepancy_status.value,
            discrepancy_reason=row.discrepancy_reason,
            magacioner_name=f"{row.first_name or ''} {row.last_name or ''}".strip() or "N/A",
            completed_at=row.closed_at.strftime("%Y-%m-%d %H:%M") if row.closed_at else None,
        )
        for row in rows
    ]
    
    # Return JSON or CSV
    if format == "csv":
        return _generate_csv_response(items)
    else:
        return items


def _generate_csv_response(items: list[ShortageReportItem]) -> StreamingResponse:
    """Generate CSV response from shortage report items."""
    import io
    
    output = io.StringIO()
    
    # Write CSV header
    headers = [
        "Document",
        "Date",
        "Store",
        "Warehouse",
        "SKU",
        "Article Name",
        "Required Qty",
        "Picked Qty",
        "Missing Qty",
        "Status",
        "Reason",
        "Worker",
        "Completed At",
    ]
    output.write(",".join(f'"{h}"' for h in headers) + "\n")
    
    # Write rows
    for item in items:
        row = [
            item.trebovanje_dokument_broj,
            item.trebovanje_datum,
            item.radnja_naziv,
            item.magacin_naziv,
            item.artikal_sifra,
            item.artikal_naziv,
            str(item.required_qty),
            str(item.picked_qty),
            str(item.missing_qty),
            item.discrepancy_status,
            item.discrepancy_reason or "",
            item.magacioner_name,
            item.completed_at or "",
        ]
        output.write(",".join(f'"{v}"' for v in row) + "\n")
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=shortage_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        },
    )

