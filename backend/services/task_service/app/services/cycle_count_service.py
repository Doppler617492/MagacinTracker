"""
Cycle count service - Inventory accuracy verification
Manhattan Active WMS - Cycle Counting
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.locations import Location, ArticleLocation, CycleCount, CycleCountItem
from ..models.artikal import Artikal
from ..models.enums import LocationType, CycleCountStatus
from ..schemas.locations import (
    CycleCountCreate,
    CycleCountResponse,
    CycleCountItemResponse,
    CycleCountComplete,
    CycleCountSummary,
)


class CycleCountService:
    """Service for cycle counting operations"""
    
    @staticmethod
    async def create_cycle_count(
        db: AsyncSession,
        data: CycleCountCreate
    ) -> CycleCount:
        """Create new cycle count task"""
        
        # Create cycle count header
        cycle_count = CycleCount(
            location_id=data.location_id,
            count_type=data.count_type,
            scheduled_at=data.scheduled_at,
            assigned_to_id=data.assigned_to_id,
            status="scheduled"
        )
        db.add(cycle_count)
        await db.flush()
        
        # Generate count items based on count_type
        if data.count_type == 'zone' and data.location_id:
            # Count all bins in zone
            await CycleCountService._generate_items_for_zone(db, cycle_count, data.location_id)
        elif data.count_type == 'regal' and data.location_id:
            # Count all bins in regal
            await CycleCountService._generate_items_for_regal(db, cycle_count, data.location_id)
        elif data.count_type == 'article':
            # Count specific article across all locations
            # TODO: Extend CycleCountCreate to include article_id
            pass
        elif data.count_type == 'random':
            # Random bin selection (ABC analysis)
            await CycleCountService._generate_random_items(db, cycle_count, count=10)
        
        await db.commit()
        await db.refresh(cycle_count)
        return cycle_count
    
    @staticmethod
    async def _generate_items_for_zone(
        db: AsyncSession,
        cycle_count: CycleCount,
        zone_location_id: uuid.UUID
    ):
        """Generate count items for all bins in zone"""
        # Get all bins in zone (via parent hierarchy)
        query = select(Location).where(
            and_(
                Location.parent_id.in_(
                    select(Location.id).where(
                        or_(
                            Location.id == zone_location_id,
                            Location.parent_id == zone_location_id,
                            Location.parent_id.in_(
                                select(Location.id).where(Location.parent_id == zone_location_id)
                            )
                        )
                    )
                ),
                Location.tip == LocationType.BIN
            )
        )
        result = await db.execute(query)
        bins = result.scalars().all()
        
        # Get all articles in these bins
        for bin_loc in bins:
            query = select(ArticleLocation).where(
                and_(
                    ArticleLocation.location_id == bin_loc.id,
                    ArticleLocation.quantity > 0
                )
            )
            result = await db.execute(query)
            article_locs = result.scalars().all()
            
            for al in article_locs:
                item = CycleCountItem(
                    cycle_count_id=cycle_count.id,
                    artikal_id=al.artikal_id,
                    location_id=al.location_id,
                    system_quantity=al.quantity
                )
                db.add(item)
    
    @staticmethod
    async def _generate_items_for_regal(
        db: AsyncSession,
        cycle_count: CycleCount,
        regal_location_id: uuid.UUID
    ):
        """Generate count items for all bins in regal"""
        # Get all bins in regal
        query = select(Location).where(
            and_(
                Location.parent_id.in_(
                    select(Location.id).where(
                        or_(
                            Location.id == regal_location_id,
                            Location.parent_id == regal_location_id
                        )
                    )
                ),
                Location.tip == LocationType.BIN
            )
        )
        result = await db.execute(query)
        bins = result.scalars().all()
        
        # Get all articles in these bins
        for bin_loc in bins:
            query = select(ArticleLocation).where(
                and_(
                    ArticleLocation.location_id == bin_loc.id,
                    ArticleLocation.quantity > 0
                )
            )
            result = await db.execute(query)
            article_locs = result.scalars().all()
            
            for al in article_locs:
                item = CycleCountItem(
                    cycle_count_id=cycle_count.id,
                    artikal_id=al.artikal_id,
                    location_id=al.location_id,
                    system_quantity=al.quantity
                )
                db.add(item)
    
    @staticmethod
    async def _generate_random_items(
        db: AsyncSession,
        cycle_count: CycleCount,
        count: int = 10
    ):
        """Generate random count items (ABC analysis - prioritize slow movers)"""
        # Get random article locations
        query = select(ArticleLocation).where(
            ArticleLocation.quantity > 0
        ).order_by(func.random()).limit(count)
        
        result = await db.execute(query)
        article_locs = result.scalars().all()
        
        for al in article_locs:
            item = CycleCountItem(
                cycle_count_id=cycle_count.id,
                artikal_id=al.artikal_id,
                location_id=al.location_id,
                system_quantity=al.quantity
            )
            db.add(item)
    
    @staticmethod
    async def get_cycle_counts(
        db: AsyncSession,
        status: Optional[str] = None,
        assigned_to_id: Optional[uuid.UUID] = None
    ) -> List[CycleCountSummary]:
        """Get cycle counts with filters"""
        query = select(CycleCount).options(
            selectinload(CycleCount.location),
            selectinload(CycleCount.items)
        )
        
        filters = []
        if status:
            filters.append(CycleCount.status == status)
        if assigned_to_id:
            filters.append(CycleCount.assigned_to_id == assigned_to_id)
        
        if filters:
            query = query.where(and_(*filters))
        
        result = await db.execute(query)
        counts = result.scalars().all()
        
        return [
            CycleCountSummary(
                id=cc.id,
                location_code=cc.location.code if cc.location else None,
                count_type=cc.count_type,
                scheduled_at=cc.scheduled_at,
                status=cc.status,
                accuracy_percentage=cc.accuracy_percentage,
                total_items=len(cc.items),
                discrepancies_count=sum(1 for item in cc.items if item.is_discrepancy)
            )
            for cc in counts
        ]
    
    @staticmethod
    async def get_cycle_count_detail(
        db: AsyncSession,
        cycle_count_id: uuid.UUID
    ) -> Optional[CycleCountResponse]:
        """Get cycle count with items"""
        query = select(CycleCount).where(CycleCount.id == cycle_count_id).options(
            selectinload(CycleCount.location),
            selectinload(CycleCount.items).selectinload(CycleCountItem.artikal),
            selectinload(CycleCount.items).selectinload(CycleCountItem.location)
        )
        result = await db.execute(query)
        cycle_count = result.scalar_one_or_none()
        
        if not cycle_count:
            return None
        
        items = [
            CycleCountItemResponse(
                id=item.id,
                artikal_id=item.artikal_id,
                artikal_sifra=item.artikal.sifra,
                artikal_naziv=item.artikal.naziv,
                location_id=item.location_id,
                location_code=item.location.code,
                system_quantity=item.system_quantity,
                counted_quantity=item.counted_quantity,
                variance=item.variance,
                variance_percent=item.variance_percent,
                is_discrepancy=item.is_discrepancy,
                requires_recount=item.requires_recount,
                reason=item.reason,
                counted_at=item.counted_at
            )
            for item in cycle_count.items
        ]
        
        return CycleCountResponse(
            id=cycle_count.id,
            location_id=cycle_count.location_id,
            location_code=cycle_count.location.code if cycle_count.location else None,
            location_naziv=cycle_count.location.naziv if cycle_count.location else None,
            scheduled_at=cycle_count.scheduled_at,
            started_at=cycle_count.started_at,
            completed_at=cycle_count.completed_at,
            status=cycle_count.status,
            count_type=cycle_count.count_type,
            accuracy_percentage=cycle_count.accuracy_percentage,
            items=items,
            created_at=cycle_count.created_at
        )
    
    @staticmethod
    async def start_cycle_count(
        db: AsyncSession,
        cycle_count_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[CycleCount]:
        """Start cycle count"""
        query = select(CycleCount).where(CycleCount.id == cycle_count_id)
        result = await db.execute(query)
        cycle_count = result.scalar_one_or_none()
        
        if not cycle_count:
            return None
        
        cycle_count.status = "in_progress"
        cycle_count.started_at = datetime.now(timezone.utc)
        cycle_count.assigned_to_id = user_id
        
        await db.commit()
        await db.refresh(cycle_count)
        return cycle_count
    
    @staticmethod
    async def complete_cycle_count(
        db: AsyncSession,
        cycle_count_id: uuid.UUID,
        data: CycleCountComplete,
        user_id: uuid.UUID
    ) -> Optional[CycleCount]:
        """Complete cycle count with counted quantities"""
        query = select(CycleCount).where(CycleCount.id == cycle_count_id)
        result = await db.execute(query)
        cycle_count = result.scalar_one_or_none()
        
        if not cycle_count:
            return None
        
        # Update each count item
        for count_data in data.counts:
            query = select(CycleCountItem).where(CycleCountItem.id == count_data.item_id)
            result = await db.execute(query)
            item = result.scalar_one_or_none()
            
            if item:
                item.counted_quantity = count_data.counted_quantity
                item.variance = count_data.counted_quantity - item.system_quantity
                
                # Calculate variance percentage
                if item.system_quantity > 0:
                    item.variance_percent = (item.variance / item.system_quantity) * 100
                else:
                    item.variance_percent = Decimal('0')
                
                item.reason = count_data.reason
                item.counted_by_id = user_id
                item.counted_at = datetime.now(timezone.utc)
                
                # Update ArticleLocation with counted quantity (inventory adjustment)
                if abs(item.variance) > 0:
                    query = select(ArticleLocation).where(
                        and_(
                            ArticleLocation.artikal_id == item.artikal_id,
                            ArticleLocation.location_id == item.location_id
                        )
                    )
                    result = await db.execute(query)
                    article_loc = result.scalar_one_or_none()
                    
                    if article_loc:
                        article_loc.quantity = count_data.counted_quantity
                        article_loc.last_counted_at = datetime.now(timezone.utc)
                        
                        # Update location capacity
                        location = await db.get(Location, item.location_id)
                        if location:
                            location.capacity_current += item.variance
        
        # Mark cycle count complete
        cycle_count.status = "completed"
        cycle_count.completed_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(cycle_count)
        return cycle_count
    
    @staticmethod
    async def cancel_cycle_count(
        db: AsyncSession,
        cycle_count_id: uuid.UUID
    ) -> Optional[CycleCount]:
        """Cancel cycle count"""
        query = select(CycleCount).where(CycleCount.id == cycle_count_id)
        result = await db.execute(query)
        cycle_count = result.scalar_one_or_none()
        
        if not cycle_count:
            return None
        
        cycle_count.status = "cancelled"
        
        await db.commit()
        await db.refresh(cycle_count)
        return cycle_count

