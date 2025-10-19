"""
Put-away service - AI-powered location suggestions
Manhattan Active WMS - Directed Put-Away
"""
import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.locations import Location, ArticleLocation
from ..models.artikal import Artikal
from ..models.enums import LocationType
from ..schemas.locations import (
    PutAwaySuggestRequest,
    PutAwaySuggestResponse,
    PutAwayLocationSuggestion,
    PutAwayExecuteRequest,
    PutAwayExecuteResponse,
    ArticleLocationCreate,
)
from .location_service import LocationService


class PutAwayService:
    """
    AI-powered put-away suggestions using 5-factor scoring:
    1. Zone compatibility (article class → zone type)
    2. Distance from receiving dock
    3. Available capacity
    4. Current occupancy (prefer partially filled for consolidation)
    5. Article already stored there (consolidation bonus)
    """
    
    # Zone compatibility rules
    ZONE_RULES = {
        'A': ['brza_prodaja', 'hitno', 'default'],  # Fast-moving zone
        'B': ['standardno', 'sezonsko', 'default'],  # Standard zone
        'C': ['sporo', 'rezerve', 'default'],        # Slow-moving zone
    }
    
    @staticmethod
    async def suggest_locations(
        db: AsyncSession,
        request: PutAwaySuggestRequest
    ) -> PutAwaySuggestResponse:
        """Generate top 5 location suggestions for put-away"""
        
        # Get article details
        query = select(Artikal).where(Artikal.id == request.artikal_id)
        result = await db.execute(query)
        artikal = result.scalar_one_or_none()
        
        if not artikal:
            raise ValueError(f"Article {request.artikal_id} not found")
        
        # Get article class (from metadata or default)
        article_class = artikal.metadata.get('klasa', 'default') if artikal.metadata else 'default'
        
        # Get available bins
        query = select(Location).where(
            and_(
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
            if available_capacity < float(request.quantity):
                continue  # Skip if insufficient capacity
            
            score, reason = await PutAwayService._score_location(
                db=db,
                bin_loc=bin_loc,
                artikal_id=request.artikal_id,
                article_class=article_class,
                quantity=float(request.quantity),
                from_location_id=request.from_location_id
            )
            
            scored_bins.append({
                'location': bin_loc,
                'score': score,
                'reason': reason,
                'available_capacity': Decimal(str(available_capacity))
            })
        
        # Sort by score descending
        scored_bins.sort(key=lambda x: x['score'], reverse=True)
        
        # Top 5
        top_suggestions = scored_bins[:5]
        
        suggestions = [
            PutAwayLocationSuggestion(
                location_id=item['location'].id,
                location_code=item['location'].code,
                location_naziv=item['location'].naziv,
                score=round(item['score'], 2),
                distance_meters=None,  # TODO: Calculate based on coordinates
                available_capacity=item['available_capacity'],
                occupancy_percentage=item['location'].occupancy_percentage,
                reason=item['reason']
            )
            for item in top_suggestions
        ]
        
        return PutAwaySuggestResponse(
            artikal_id=artikal.id,
            artikal_sifra=artikal.sifra,
            artikal_naziv=artikal.naziv,
            quantity=request.quantity,
            suggestions=suggestions
        )
    
    @staticmethod
    async def _score_location(
        db: AsyncSession,
        bin_loc: Location,
        artikal_id: uuid.UUID,
        article_class: str,
        quantity: float,
        from_location_id: Optional[uuid.UUID]
    ) -> tuple[float, str]:
        """
        Score a location for put-away (0-100)
        Returns (score, reason_in_serbian)
        """
        score = 0.0
        reasons = []
        
        # Factor 1: Zone compatibility (30 points)
        zona = bin_loc.zona or 'B'
        compatible_classes = PutAwayService.ZONE_RULES.get(zona, ['default'])
        if article_class in compatible_classes:
            score += 30
            reasons.append(f"Kompatibilna zona ({zona})")
        else:
            score += 10
            reasons.append(f"Neutralna zona ({zona})")
        
        # Factor 2: Distance from dock (20 points)
        # TODO: Calculate actual distance using coordinates
        # For now, use simple zone-based heuristic
        if zona == 'A' and bin_loc.x_coordinate and bin_loc.x_coordinate < 20:
            score += 20
            reasons.append("Blizu ulaza")
        elif zona == 'B':
            score += 15
            reasons.append("Srednja udaljenost")
        else:
            score += 10
            reasons.append("Dalja lokacija")
        
        # Factor 3: Available capacity (20 points)
        available = float(bin_loc.capacity_max or 0) - float(bin_loc.capacity_current)
        capacity_ratio = quantity / available if available > 0 else 0
        if 0.5 <= capacity_ratio <= 0.9:
            # Good utilization
            score += 20
            reasons.append("Optimalno popunjavanje")
        elif capacity_ratio < 0.5:
            score += 15
            reasons.append("Dosta prostora")
        else:
            score += 10
            reasons.append("Tesno ali staje")
        
        # Factor 4: Current occupancy (10 points)
        # Prefer bins that are 30-70% full (consolidation)
        occupancy = bin_loc.occupancy_percentage
        if 30 <= occupancy <= 70:
            score += 10
            reasons.append("Dobra popunjenost")
        elif occupancy < 30:
            score += 5
            reasons.append("Prazan bin")
        else:
            score += 3
        
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
            score += 20
            reasons.append("Artikal već tu (konsolidacija)")
        else:
            score += 0
        
        reason_text = " • ".join(reasons)
        return score, reason_text
    
    @staticmethod
    async def execute_putaway(
        db: AsyncSession,
        request: PutAwayExecuteRequest
    ) -> PutAwayExecuteResponse:
        """Execute put-away to selected location"""
        
        # Validate location exists and has capacity
        location = await LocationService.get_location_by_id(db, request.location_id)
        if not location:
            return PutAwayExecuteResponse(
                success=False,
                message="Lokacija ne postoji"
            )
        
        if not location.can_store(float(request.quantity)):
            return PutAwayExecuteResponse(
                success=False,
                message=f"Nedovoljno kapaciteta (dostupno: {location.capacity_max - location.capacity_current})"
            )
        
        # Get receiving item to extract article_id
        from ..models.receiving import ReceivingItem
        query = select(ReceivingItem).where(ReceivingItem.id == request.receiving_item_id)
        result = await db.execute(query)
        receiving_item = result.scalar_one_or_none()
        
        if not receiving_item:
            return PutAwayExecuteResponse(
                success=False,
                message="Receiving stavka ne postoji"
            )
        
        # Assign article to location
        assign_data = ArticleLocationCreate(
            artikal_id=receiving_item.artikal_id,
            location_id=request.location_id,
            quantity=request.quantity,
            uom=receiving_item.jm
        )
        
        article_loc = await LocationService.assign_article_to_location(db, assign_data)
        
        # Update receiving_item with actual location
        receiving_item.actual_location_id = request.location_id
        receiving_item.putaway_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(location)
        
        return PutAwayExecuteResponse(
            success=True,
            message=f"Uskladišteno u {location.code}",
            article_location_id=article_loc.id,
            new_occupancy_percentage=location.occupancy_percentage
        )

