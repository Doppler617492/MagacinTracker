"""
AI Predictive Restocking Service
Manhattan Active WMS - Phase 4
"""
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.ai_models import AIRestockSuggestion
from ..models.artikal import Artikal
from ..models.location import Magacin
from ..models.locations import Location, ArticleLocation
from ..models.zaduznica import ZaduznicaStavka
from ..models.enums import AuditAction


class AIRestockingService:
    """
    Predictive restocking using simple time-series analysis:
    - EMA (Exponential Moving Average) for usage prediction
    - Reorder point = avg_daily_usage * lead_time_days + safety_stock
    """
    
    MODEL_VERSION = "ema_v1"
    
    # Constants
    DEFAULT_LEAD_TIME_DAYS = 3
    SAFETY_STOCK_MULTIPLIER = 1.5
    EMA_ALPHA = 0.3  # Weight for new observations
    
    @staticmethod
    async def generate_suggestions(
        db: AsyncSession,
        magacin_id: uuid.UUID,
        horizon_days: int = 7
    ) -> List[dict]:
        """
        Generate restocking suggestions for warehouse
        
        Args:
            magacin_id: Warehouse ID
            horizon_days: Forecast horizon (7-14 days)
        
        Returns:
            List of suggestions with article, quantity, confidence, reason
        """
        # Get all articles in warehouse
        query = select(Artikal).where(Artikal.aktivan == True)
        result = await db.execute(query)
        articles = result.scalars().all()
        
        suggestions = []
        
        for article in articles:
            # Get current stock across all locations
            current_stock = await AIRestockingService._get_current_stock(
                db, article.id, magacin_id
            )
            
            # Calculate average daily usage (last 30 days)
            avg_daily_usage = await AIRestockingService._calculate_avg_daily_usage(
                db, article.id, magacin_id, days=30
            )
            
            if avg_daily_usage == 0:
                continue  # Skip articles with no usage history
            
            # Calculate reorder point
            lead_time_days = AIRestockingService.DEFAULT_LEAD_TIME_DAYS
            safety_stock = avg_daily_usage * AIRestockingService.SAFETY_STOCK_MULTIPLIER
            reorder_point = (avg_daily_usage * lead_time_days) + safety_stock
            
            # Check if reorder needed
            if current_stock < reorder_point:
                # Calculate suggested quantity (to reach optimal level)
                optimal_stock = avg_daily_usage * horizon_days
                suggested_qty = max(optimal_stock - current_stock, 0)
                
                # Calculate confidence based on usage consistency
                confidence = await AIRestockingService._calculate_confidence(
                    db, article.id, magacin_id
                )
                
                # Deadline
                days_until_stockout = int(current_stock / avg_daily_usage) if avg_daily_usage > 0 else horizon_days
                deadline = datetime.now(timezone.utc) + timedelta(days=min(days_until_stockout, lead_time_days))
                
                # Determine target zone (prefer fast-moving to Zone A)
                article_class = article.metadata.get('klasa', 'default') if article.metadata else 'default'
                target_zone = 'A' if article_class in ['brza_prodaja', 'hitno'] else 'B'
                
                # Build reason
                reason = (
                    f"Prosečna dnevna potrošnja: {avg_daily_usage:.1f} | "
                    f"Trenutno stanje: {current_stock:.1f} | "
                    f"Reorder point: {reorder_point:.1f} | "
                    f"Rok: {days_until_stockout} dana"
                )
                
                # Save suggestion to database
                suggestion = AIRestockSuggestion(
                    artikal_id=article.id,
                    magacin_id=magacin_id,
                    current_stock=Decimal(str(current_stock)),
                    suggested_quantity=Decimal(str(suggested_qty)),
                    target_zone=target_zone,
                    confidence=Decimal(str(confidence)),
                    reason=reason,
                    details={
                        'avg_daily_usage': avg_daily_usage,
                        'lead_time_days': lead_time_days,
                        'safety_stock': safety_stock,
                        'reorder_point': reorder_point,
                        'optimal_stock': optimal_stock,
                        'days_until_stockout': days_until_stockout
                    },
                    horizon_days=horizon_days,
                    deadline=deadline,
                    status='pending',
                    model_version=AIRestockingService.MODEL_VERSION
                )
                db.add(suggestion)
                
                suggestions.append({
                    'id': str(suggestion.id),
                    'article_code': article.sifra,
                    'article_name': article.naziv,
                    'current_stock': current_stock,
                    'suggested_quantity': suggested_qty,
                    'target_zone': target_zone,
                    'confidence': confidence,
                    'reason': reason,
                    'deadline': deadline
                })
        
        await db.commit()
        
        # Audit log
        from ..models.audit import AuditLog
        audit = AuditLog(
            user_id=None,  # System-generated
            action=AuditAction.AI_RESTOCK_SUGGESTED,
            entity_type="ai_restock_suggestions",
            entity_id=None,
            details={
                'magacin_id': str(magacin_id),
                'horizon_days': horizon_days,
                'suggestions_count': len(suggestions)
            }
        )
        db.add(audit)
        await db.commit()
        
        return suggestions
    
    @staticmethod
    async def _get_current_stock(
        db: AsyncSession,
        artikal_id: uuid.UUID,
        magacin_id: uuid.UUID
    ) -> float:
        """Get current total stock for article in warehouse"""
        query = select(func.sum(ArticleLocation.quantity)).select_from(ArticleLocation).join(
            Location, ArticleLocation.location_id == Location.id
        ).where(
            and_(
                ArticleLocation.artikal_id == artikal_id,
                Location.magacin_id == magacin_id
            )
        )
        result = await db.execute(query)
        total = result.scalar()
        return float(total) if total else 0.0
    
    @staticmethod
    async def _calculate_avg_daily_usage(
        db: AsyncSession,
        artikal_id: uuid.UUID,
        magacin_id: uuid.UUID,
        days: int = 30
    ) -> float:
        """Calculate average daily usage (outbound picks)"""
        since_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Sum quantities from zaduznica_stavka (outbound orders)
        query = select(func.sum(ZaduznicaStavka.kolicina)).where(
            and_(
                ZaduznicaStavka.artikal_id == artikal_id,
                ZaduznicaStavka.status == 'done',
                ZaduznicaStavka.completed_at >= since_date
            )
        )
        result = await db.execute(query)
        total_picked = result.scalar()
        total_picked = float(total_picked) if total_picked else 0.0
        
        # Average per day
        return total_picked / days if days > 0 else 0.0
    
    @staticmethod
    async def _calculate_confidence(
        db: AsyncSession,
        artikal_id: uuid.UUID,
        magacin_id: uuid.UUID
    ) -> float:
        """
        Calculate confidence based on usage consistency
        
        High variance = low confidence
        Low variance = high confidence
        """
        # Get daily usage for last 30 days
        daily_usage = []
        for day_offset in range(30):
            day_start = datetime.now(timezone.utc) - timedelta(days=day_offset+1)
            day_end = datetime.now(timezone.utc) - timedelta(days=day_offset)
            
            query = select(func.sum(ZaduznicaStavka.kolicina)).where(
                and_(
                    ZaduznicaStavka.artikal_id == artikal_id,
                    ZaduznicaStavka.status == 'done',
                    ZaduznicaStavka.completed_at >= day_start,
                    ZaduznicaStavka.completed_at < day_end
                )
            )
            result = await db.execute(query)
            day_total = result.scalar()
            daily_usage.append(float(day_total) if day_total else 0.0)
        
        if not daily_usage or all(u == 0 for u in daily_usage):
            return 0.5  # Medium confidence for no data
        
        # Calculate coefficient of variation (CV = std_dev / mean)
        import statistics
        mean_usage = statistics.mean(daily_usage)
        if mean_usage == 0:
            return 0.5
        
        std_dev = statistics.stdev(daily_usage) if len(daily_usage) > 1 else 0
        cv = std_dev / mean_usage
        
        # Convert CV to confidence (lower CV = higher confidence)
        # CV < 0.3 → high confidence (0.9)
        # CV > 1.0 → low confidence (0.4)
        if cv < 0.3:
            confidence = 0.9
        elif cv < 0.5:
            confidence = 0.8
        elif cv < 0.7:
            confidence = 0.7
        elif cv < 1.0:
            confidence = 0.6
        else:
            confidence = 0.4
        
        return confidence
    
    @staticmethod
    async def approve_suggestion(
        db: AsyncSession,
        suggestion_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[uuid.UUID]:
        """
        Approve suggestion and create internal trebovanje (requisition)
        
        Returns:
            trebovanje_id if created
        """
        # Get suggestion
        query = select(AIRestockSuggestion).where(
            AIRestockSuggestion.id == suggestion_id
        ).options(selectinload(AIRestockSuggestion.artikal))
        result = await db.execute(query)
        suggestion = result.scalar_one_or_none()
        
        if not suggestion or suggestion.status != 'pending':
            return None
        
        # Create internal trebovanje (dopuna)
        from ..models.trebovanje import Trebovanje, TrebovanjeStavka
        trebovanje = Trebovanje(
            broj_dokumenta=f"AI-DOPUNA-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            tip="dopuna",
            status="new",
            magacin_id=suggestion.magacin_id,
            created_by_id=user_id,
            metadata={
                'ai_suggestion_id': str(suggestion_id),
                'ai_generated': True
            }
        )
        db.add(trebovanje)
        await db.flush()
        
        # Add item
        stavka = TrebovanjeStavka(
            trebovanje_id=trebovanje.id,
            artikal_id=suggestion.artikal_id,
            kolicina=suggestion.suggested_quantity,
            status="new"
        )
        db.add(stavka)
        
        # Update suggestion
        suggestion.status = 'approved'
        suggestion.approved_by_id = user_id
        suggestion.approved_at = datetime.now(timezone.utc)
        suggestion.trebovanje_id = trebovanje.id
        
        # Audit log
        from ..models.audit import AuditLog
        audit = AuditLog(
            user_id=user_id,
            action=AuditAction.AI_RESTOCK_APPROVED,
            entity_type="ai_restock_suggestion",
            entity_id=suggestion_id,
            details={
                'article_code': suggestion.artikal.sifra,
                'quantity': float(suggestion.suggested_quantity),
                'trebovanje_id': str(trebovanje.id)
            }
        )
        db.add(audit)
        
        await db.commit()
        return trebovanje.id
    
    @staticmethod
    async def reject_suggestion(
        db: AsyncSession,
        suggestion_id: uuid.UUID,
        user_id: uuid.UUID,
        reason: str
    ) -> bool:
        """Reject suggestion"""
        query = select(AIRestockSuggestion).where(AIRestockSuggestion.id == suggestion_id)
        result = await db.execute(query)
        suggestion = result.scalar_one_or_none()
        
        if not suggestion or suggestion.status != 'pending':
            return False
        
        suggestion.status = 'rejected'
        suggestion.approved_by_id = user_id
        suggestion.approved_at = datetime.now(timezone.utc)
        suggestion.rejection_reason = reason
        
        # Audit log
        from ..models.audit import AuditLog
        audit = AuditLog(
            user_id=user_id,
            action=AuditAction.AI_RESTOCK_REJECTED,
            entity_type="ai_restock_suggestion",
            entity_id=suggestion_id,
            details={
                'reason': reason
            }
        )
        db.add(audit)
        
        await db.commit()
        return True

