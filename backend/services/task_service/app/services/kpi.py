from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.audit import AuditLog
from ..models.execution import ScanLog
from ..models.scheduler import SchedulerLog
from ..models.trebovanje import Trebovanje, TrebovanjeStavka
from ..models.user import UserAccount
from ..models.zaduznica import Zaduznica, ZaduznicaStavka
from ..models.enums import AuditAction, ScanResult


class KPIService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_summary(
        self,
        radnja_id: Optional[uuid.UUID] = None,
        radnik_id: Optional[uuid.UUID] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get KPI summary with filtering options."""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Base query conditions
        conditions = [
            Trebovanje.created_at >= start_date,
            Trebovanje.created_at <= end_date
        ]
        
        if radnja_id:
            conditions.append(Trebovanje.radnja_id == radnja_id)
        
        # Total trebovanja and stavke
        trebovanja_query = select(
            func.count(Trebovanje.id).label('total_trebovanja'),
            func.sum(func.coalesce(TrebovanjeStavka.kolicina_trazena, 0)).label('total_stavke')
        ).select_from(
            Trebovanje.__table__.join(
                TrebovanjeStavka.__table__,
                Trebovanje.id == TrebovanjeStavka.trebovanje_id
            )
        ).where(and_(*conditions))
        
        trebovanja_result = await self.session.execute(trebovanja_query)
        trebovanja_stats = trebovanja_result.first()
        
        # Task completion stats
        zaduznica_conditions = conditions.copy()
        if radnik_id:
            zaduznica_conditions.append(Zaduznica.magacioner_id == radnik_id)
        
        zaduznica_query = select(
            func.count(Zaduznica.id).label('total_zadaci'),
            func.sum(
                case(
                    (Zaduznica.status == 'done', 1),
                    else_=0
                )
            ).label('completed_zadaci')
        ).select_from(Zaduznica.__table__).where(and_(*zaduznica_conditions))
        
        zaduznica_result = await self.session.execute(zaduznica_query)
        zaduznica_stats = zaduznica_result.first()
        
        # Manual completion percentage
        manual_query = select(
            func.count(ScanLog.id).label('total_scans'),
            func.sum(
                case(
                    (ScanLog.result == ScanResult.manual, 1),
                    else_=0
                )
            ).label('manual_scans')
        ).select_from(ScanLog.__table__).where(
            and_(
                ScanLog.created_at >= start_date,
                ScanLog.created_at <= end_date
            )
        )
        
        if radnik_id:
            manual_query = manual_query.where(ScanLog.user_id == radnik_id)
        
        manual_result = await self.session.execute(manual_query)
        manual_stats = manual_result.first()
        
        # Calculate percentages
        total_zadaci = zaduznica_stats.total_zadaci or 0
        completed_zadaci = zaduznica_stats.completed_zadaci or 0
        completion_rate = (completed_zadaci / total_zadaci * 100) if total_zadaci > 0 else 0
        
        total_scans = manual_stats.total_scans or 0
        manual_scans = manual_stats.manual_scans or 0
        manual_percentage = (manual_scans / total_scans * 100) if total_scans > 0 else 0
        
        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "filters": {
                "radnja_id": str(radnja_id) if radnja_id else None,
                "radnik_id": str(radnik_id) if radnik_id else None
            },
            "summary": {
                "total_trebovanja": trebovanja_stats.total_trebovanja or 0,
                "total_stavke": float(trebovanja_stats.total_stavke or 0),
                "total_zadaci": total_zadaci,
                "completed_zadaci": completed_zadaci,
                "completion_rate": round(completion_rate, 2),
                "total_scans": total_scans,
                "manual_scans": manual_scans,
                "manual_percentage": round(manual_percentage, 2)
            }
        }

    async def get_daily_stats(
        self,
        radnja_id: Optional[uuid.UUID] = None,
        radnik_id: Optional[uuid.UUID] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get daily statistics for the specified period."""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Generate date range
        daily_stats = []
        current_date = start_date.date()
        
        while current_date <= end_date.date():
            day_start = datetime.combine(current_date, datetime.min.time())
            day_end = datetime.combine(current_date, datetime.max.time())
            
            # Daily trebovanja count
            trebovanja_conditions = [
                Trebovanje.created_at >= day_start,
                Trebovanje.created_at <= day_end
            ]
            
            if radnja_id:
                trebovanja_conditions.append(Trebovanje.radnja_id == radnja_id)
            
            trebovanja_query = select(
                func.count(Trebovanje.id).label('trebovanja_count')
            ).where(and_(*trebovanja_conditions))
            
            trebovanja_result = await self.session.execute(trebovanja_query)
            trebovanja_count = trebovanja_result.scalar() or 0
            
            # Daily stavke count
            stavke_query = select(
                func.sum(func.coalesce(TrebovanjeStavka.kolicina_trazena, 0)).label('stavke_count')
            ).select_from(
                Trebovanje.__table__.join(
                    TrebovanjeStavka.__table__,
                    Trebovanje.id == TrebovanjeStavka.trebovanje_id
                )
            ).where(and_(*trebovanja_conditions))
            
            stavke_result = await self.session.execute(stavke_query)
            stavke_count = float(stavke_result.scalar() or 0)
            
            daily_stats.append({
                "date": current_date.isoformat(),
                "trebovanja_count": trebovanja_count,
                "stavke_count": stavke_count
            })
            
            current_date += timedelta(days=1)
        
        return daily_stats

    async def get_top_workers(
        self,
        radnja_id: Optional[uuid.UUID] = None,
        days: int = 30,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get top performing workers by task completion."""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        conditions = [
            Zaduznica.created_at >= start_date,
            Zaduznica.created_at <= end_date
        ]
        
        if radnja_id:
            conditions.append(Trebovanje.radnja_id == radnja_id)
        
        query = select(
            UserAccount.id,
            UserAccount.first_name,
            UserAccount.last_name,
            func.count(Zaduznica.id).label('total_zadaci'),
            func.sum(
                case(
                    (Zaduznica.status == 'done', 1),
                    else_=0
                )
            ).label('completed_zadaci')
        ).select_from(
            UserAccount.__table__.join(
                Zaduznica.__table__,
                UserAccount.id == Zaduznica.magacioner_id
            ).join(
                Trebovanje.__table__,
                Zaduznica.trebovanje_id == Trebovanje.id
            )
        ).where(
            and_(*conditions)
        ).group_by(
            UserAccount.id, UserAccount.first_name, UserAccount.last_name
        ).order_by(
            func.count(Zaduznica.id).desc()
        ).limit(limit)
        
        result = await self.session.execute(query)
        workers = []
        
        for row in result:
            total = row.total_zadaci or 0
            completed = row.completed_zadaci or 0
            completion_rate = (completed / total * 100) if total > 0 else 0
            
            workers.append({
                "radnik_id": str(row.id),
                "ime": row.first_name,
                "prezime": row.last_name,
                "total_zadaci": total,
                "completed_zadaci": completed,
                "completion_rate": round(completion_rate, 2)
            })
        
        return workers

    async def get_manual_completion_stats(
        self,
        radnja_id: Optional[uuid.UUID] = None,
        radnik_id: Optional[uuid.UUID] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get manual completion statistics."""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        conditions = [
            ScanLog.created_at >= start_date,
            ScanLog.created_at <= end_date
        ]
        
        if radnik_id:
            conditions.append(ScanLog.user_id == radnik_id)
        
        # If filtering by radnja, we need to join through zaduznica
        if radnja_id:
            query = select(
                func.count(ScanLog.id).label('total_scans'),
                func.sum(
                    case(
                        (ScanLog.barcode == "manual", 1),
                        else_=0
                    )
                ).label('manual_scans')
            ).select_from(
                ScanLog.__table__.join(
                    ZaduznicaStavka.__table__,
                    ScanLog.zaduznica_stavka_id == ZaduznicaStavka.id
                ).join(
                    Zaduznica.__table__,
                    ZaduznicaStavka.zaduznica_id == Zaduznica.id
                ).join(
                    Trebovanje.__table__,
                    Zaduznica.trebovanje_id == Trebovanje.id
                )
            ).where(
                and_(*conditions, Trebovanje.radnja_id == radnja_id)
            )
        else:
            query = select(
                func.count(ScanLog.id).label('total_scans'),
                func.sum(
                    case(
                        (ScanLog.barcode == "manual", 1),
                        else_=0
                    )
                ).label('manual_scans')
            ).where(and_(*conditions))
        
        result = await self.session.execute(query)
        stats = result.first()
        
        total_scans = stats.total_scans or 0
        manual_scans = stats.manual_scans or 0
        manual_percentage = (manual_scans / total_scans * 100) if total_scans > 0 else 0
        
        return {
            "total_scans": total_scans,
            "manual_scans": manual_scans,
            "manual_percentage": round(manual_percentage, 2),
            "scan_percentage": round(100 - manual_percentage, 2)
        }
