"""
AI Bin Allocation Service - Smart location suggestions
Manhattan Active WMS - Phase 4
"""
import uuid
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.ai_models import AIBinSuggestion
from ..models.locations import Location, ArticleLocation
from ..models.artikal import Artikal
from ..models.receiving import ReceivingItem
from ..models.enums import LocationType, AuditAction


class AIBinAllocationService:
    """
    AI-powered bin allocation using 5-factor scoring:
    1. Zone compatibility (30 pts) - article class → zone type
    2. Distance from dock (20 pts) - coordinate-based
    3. Available capacity (20 pts) - optimal utilization
    4. Current occupancy (10 pts) - prefer 30-70% full
    5. Article consolidation (20 pts) - same article already there
    """
    
    # Model version
    MODEL_VERSION = "heuristic_v1"
    
    # Weights for scoring factors
    WEIGHTS = {
        'zone_compatibility': 30.0,
        'distance': 20.0,
        'capacity': 20.0,
        'occupancy': 10.0,
        'consolidation': 20.0,
    }
    
    # Zone compatibility rules
    ZONE_RULES = {
        'A': ['brza_prodaja', 'hitno', 'default'],  # Fast-moving zone
        'B': ['standardno', 'sezonsko', 'default'],  # Standard zone
        'C': ['sporo', 'rezerve', 'default'],        # Slow-moving zone
    }
    
    @staticmethod
    async def suggest_bins(
        db: AsyncSession,
        receiving_item_id: uuid.UUID,
        artikal_id: uuid.UUID,
        quantity: Decimal,
        magacin_id: uuid.UUID
    ) -> List[dict]:
        """
        Generate top 3 bin suggestions for receiving item
        
        Returns:
            List of suggestions with rank, score, confidence, reason
        """
        start_time = time.time()
        
        # Get article details
        query = select(Artikal).where(Artikal.id == artikal_id)
        result = await db.execute(query)
        artikal = result.scalar_one_or_none()
        
        if not artikal:
            raise ValueError(f"Article {artikal_id} not found")
        
        # Get article class from metadata
        article_class = artikal.metadata.get('klasa', 'default') if artikal.metadata else 'default'
        
        # Get all available bins in warehouse
        query = select(Location).where(
            and_(
                Location.magacin_id == magacin_id,
                Location.tip == LocationType.BIN,
                Location.is_active == True,
                Location.capacity_max.isnot(None)
            )
        )
        result = await db.execute(query)
        bins = result.scalars().all()
        
        # Score each bin
        scored_bins = []
        for bin_loc in bins:
            # Check capacity
            available_capacity = float(bin_loc.capacity_max or 0) - float(bin_loc.capacity_current)
            if available_capacity < float(quantity):
                continue  # Skip if insufficient capacity
            
            score, reason, details = await AIBinAllocationService._score_location(
                db=db,
                bin_loc=bin_loc,
                artikal_id=artikal_id,
                article_class=article_class,
                quantity=float(quantity)
            )
            
            # Calculate confidence (higher score = higher confidence)
            confidence = min(score / 100.0, 1.0)
            
            scored_bins.append({
                'location': bin_loc,
                'score': score,
                'confidence': confidence,
                'reason': reason,
                'details': details,
                'available_capacity': Decimal(str(available_capacity))
            })
        
        # Sort by score descending
        scored_bins.sort(key=lambda x: x['score'], reverse=True)
        
        # Top 3
        top_suggestions = scored_bins[:3]
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Save suggestions to database
        for rank, suggestion in enumerate(top_suggestions, start=1):
            ai_suggestion = AIBinSuggestion(
                receiving_item_id=receiving_item_id,
                artikal_id=artikal_id,
                suggested_location_id=suggestion['location'].id,
                rank=rank,
                score=Decimal(str(suggestion['score'])),
                confidence=Decimal(str(suggestion['confidence'])),
                reason=suggestion['reason'],
                details=suggestion['details'],
                model_version=AIBinAllocationService.MODEL_VERSION,
                latency_ms=latency_ms
            )
            db.add(ai_suggestion)
        
        await db.commit()
        
        # Build response
        suggestions = [
            {
                'rank': rank,
                'location_id': str(s['location'].id),
                'location_code': s['location'].code,
                'location_path': s['location'].full_path,
                'score': round(s['score'], 2),
                'confidence': round(s['confidence'], 2),
                'reason': s['reason'],
                'available_capacity': float(s['available_capacity']),
                'occupancy_percentage': s['location'].occupancy_percentage
            }
            for rank, s in enumerate(top_suggestions, start=1)
        ]
        
        return suggestions
    
    @staticmethod
    async def _score_location(
        db: AsyncSession,
        bin_loc: Location,
        artikal_id: uuid.UUID,
        article_class: str,
        quantity: float
    ) -> Tuple[float, str, dict]:
        """
        Score a location using 5 factors
        
        Returns:
            (score, reason_in_serbian, details_dict)
        """
        score = 0.0
        reasons = []
        details = {}
        
        # Factor 1: Zone compatibility (30 points)
        zona = bin_loc.zona or 'B'
        compatible_classes = AIBinAllocationService.ZONE_RULES.get(zona, ['default'])
        if article_class in compatible_classes:
            score += AIBinAllocationService.WEIGHTS['zone_compatibility']
            reasons.append(f"Kompatibilna zona ({zona})")
            details['zone_match'] = True
        else:
            score += AIBinAllocationService.WEIGHTS['zone_compatibility'] * 0.33
            reasons.append(f"Neutralna zona ({zona})")
            details['zone_match'] = False
        
        # Factor 2: Distance from dock (20 points)
        # Heuristic: Zone A near entrance, B medium, C far
        if zona == 'A' and bin_loc.x_coordinate and bin_loc.x_coordinate < 20:
            score += AIBinAllocationService.WEIGHTS['distance']
            reasons.append("Blizu ulaza")
            details['distance_category'] = 'near'
        elif zona == 'B':
            score += AIBinAllocationService.WEIGHTS['distance'] * 0.75
            reasons.append("Srednja udaljenost")
            details['distance_category'] = 'medium'
        else:
            score += AIBinAllocationService.WEIGHTS['distance'] * 0.5
            reasons.append("Dalja lokacija")
            details['distance_category'] = 'far'
        
        # Factor 3: Available capacity (20 points)
        available = float(bin_loc.capacity_max or 0) - float(bin_loc.capacity_current)
        capacity_ratio = quantity / available if available > 0 else 0
        if 0.5 <= capacity_ratio <= 0.9:
            # Good utilization
            score += AIBinAllocationService.WEIGHTS['capacity']
            reasons.append("Optimalno popunjavanje")
            details['capacity_utilization'] = 'optimal'
        elif capacity_ratio < 0.5:
            score += AIBinAllocationService.WEIGHTS['capacity'] * 0.75
            reasons.append("Dosta prostora")
            details['capacity_utilization'] = 'plenty'
        else:
            score += AIBinAllocationService.WEIGHTS['capacity'] * 0.5
            reasons.append("Tesno ali staje")
            details['capacity_utilization'] = 'tight'
        
        # Factor 4: Current occupancy (10 points)
        # Prefer bins that are 30-70% full (consolidation)
        occupancy = bin_loc.occupancy_percentage
        if 30 <= occupancy <= 70:
            score += AIBinAllocationService.WEIGHTS['occupancy']
            reasons.append("Dobra popunjenost")
            details['occupancy_match'] = True
        elif occupancy < 30:
            score += AIBinAllocationService.WEIGHTS['occupancy'] * 0.5
            reasons.append("Prazan bin")
            details['occupancy_match'] = False
        else:
            score += AIBinAllocationService.WEIGHTS['occupancy'] * 0.3
            details['occupancy_match'] = False
        
        # Factor 5: Same article already there (20 points)
        query = select(ArticleLocation).where(
            and_(
                ArticleLocation.location_id == bin_loc.id,
                ArticleLocation.artikal_id == artikal_id,
                ArticleLocation.quantity > 0
            )
        )
        result = await db.execute(query)
        same_article = result.scalar_one_or_none()
        
        if same_article:
            score += AIBinAllocationService.WEIGHTS['consolidation']
            reasons.append("Artikal već tu (konsolidacija)")
            details['consolidation'] = True
        else:
            details['consolidation'] = False
        
        reason_text = " • ".join(reasons)
        return score, reason_text, details
    
    @staticmethod
    async def accept_suggestion(
        db: AsyncSession,
        receiving_item_id: uuid.UUID,
        location_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """
        Mark suggestion as accepted and execute put-away
        
        Returns:
            True if successful
        """
        # Find suggestion
        query = select(AIBinSuggestion).where(
            and_(
                AIBinSuggestion.receiving_item_id == receiving_item_id,
                AIBinSuggestion.suggested_location_id == location_id,
                AIBinSuggestion.accepted.is_(None)
            )
        )
        result = await db.execute(query)
        suggestion = result.scalar_one_or_none()
        
        if not suggestion:
            return False
        
        # Mark as accepted
        suggestion.accepted = True
        suggestion.accepted_by_id = user_id
        suggestion.accepted_at = datetime.now(timezone.utc)
        
        # Audit log
        from ..models.audit import AuditLog
        audit = AuditLog(
            user_id=user_id,
            action=AuditAction.AI_BIN_ACCEPTED,
            entity_type="ai_bin_suggestion",
            entity_id=suggestion.id,
            details={
                'receiving_item_id': str(receiving_item_id),
                'location_id': str(location_id),
                'location_code': suggestion.suggested_location.code,
                'rank': suggestion.rank,
                'score': float(suggestion.score)
            }
        )
        db.add(audit)
        
        await db.commit()
        return True
    
    @staticmethod
    async def reject_suggestion(
        db: AsyncSession,
        receiving_item_id: uuid.UUID,
        user_id: uuid.UUID,
        reason: str
    ) -> bool:
        """
        Mark all suggestions for receiving item as rejected
        
        Returns:
            True if successful
        """
        # Find all suggestions for receiving item
        query = select(AIBinSuggestion).where(
            and_(
                AIBinSuggestion.receiving_item_id == receiving_item_id,
                AIBinSuggestion.accepted.is_(None)
            )
        )
        result = await db.execute(query)
        suggestions = result.scalars().all()
        
        if not suggestions:
            return False
        
        # Mark all as rejected
        for suggestion in suggestions:
            suggestion.accepted = False
            suggestion.accepted_by_id = user_id
            suggestion.accepted_at = datetime.now(timezone.utc)
            suggestion.rejection_reason = reason
        
        # Audit log
        from ..models.audit import AuditLog
        audit = AuditLog(
            user_id=user_id,
            action=AuditAction.AI_BIN_REJECTED,
            entity_type="ai_bin_suggestion",
            entity_id=suggestions[0].id,
            details={
                'receiving_item_id': str(receiving_item_id),
                'reason': reason,
                'count': len(suggestions)
            }
        )
        db.add(audit)
        
        await db.commit()
        return True

