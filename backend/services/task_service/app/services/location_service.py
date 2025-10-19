"""
Location service - CRUD and hierarchy operations
Manhattan Active WMS - Enterprise location management
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.locations import Location, ArticleLocation
from ..models.enums import LocationType
from ..schemas.locations import (
    LocationCreate,
    LocationUpdate,
    LocationTreeNode,
    ArticleLocationCreate,
    ArticleLocationUpdate,
    ArticleInLocationDetail,
)


class LocationService:
    """Service for location management"""
    
    @staticmethod
    async def get_locations(
        db: AsyncSession,
        magacin_id: Optional[uuid.UUID] = None,
        zona: Optional[str] = None,
        tip: Optional[LocationType] = None,
        is_active: Optional[bool] = None,
        parent_id: Optional[uuid.UUID] = None,
    ) -> List[Location]:
        """Get locations with filters"""
        query = select(Location)
        
        filters = []
        if magacin_id:
            filters.append(Location.magacin_id == magacin_id)
        if zona:
            filters.append(Location.zona == zona)
        if tip:
            filters.append(Location.tip == tip)
        if is_active is not None:
            filters.append(Location.is_active == is_active)
        if parent_id is not None:
            filters.append(Location.parent_id == parent_id)
        
        if filters:
            query = query.where(and_(*filters))
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_location_tree(
        db: AsyncSession,
        magacin_id: uuid.UUID,
        zona: Optional[str] = None
    ) -> List[LocationTreeNode]:
        """Get location hierarchy as tree structure"""
        # Get all locations
        query = select(Location).where(Location.magacin_id == magacin_id)
        if zona:
            query = query.where(Location.zona == zona)
        
        result = await db.execute(query)
        all_locations = result.scalars().all()
        
        # Build lookup dict
        loc_dict = {loc.id: loc for loc in all_locations}
        
        # Build tree structure
        def build_node(location: Location) -> LocationTreeNode:
            children_locs = [loc for loc in all_locations if loc.parent_id == location.id]
            children_nodes = [build_node(child) for child in children_locs]
            
            return LocationTreeNode(
                id=location.id,
                naziv=location.naziv,
                code=location.code,
                tip=location.tip,
                capacity_max=location.capacity_max,
                capacity_current=location.capacity_current,
                occupancy_percentage=location.occupancy_percentage,
                status_color=location.status_color,
                is_active=location.is_active,
                children=children_nodes
            )
        
        # Get root nodes (zones - no parent)
        root_locations = [loc for loc in all_locations if loc.parent_id is None]
        return [build_node(root) for root in root_locations]
    
    @staticmethod
    async def get_location_by_id(db: AsyncSession, location_id: uuid.UUID) -> Optional[Location]:
        """Get location by ID"""
        query = select(Location).where(Location.id == location_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_location_by_code(db: AsyncSession, code: str) -> Optional[Location]:
        """Get location by code"""
        query = select(Location).where(Location.code == code)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_location(db: AsyncSession, data: LocationCreate) -> Location:
        """Create new location"""
        # Validate parent exists if specified
        if data.parent_id:
            parent = await LocationService.get_location_by_id(db, data.parent_id)
            if not parent:
                raise ValueError(f"Parent location {data.parent_id} not found")
            
            # Auto-set zona from parent
            if parent.zona:
                data.zona = parent.zona
        
        # Create location
        location = Location(**data.model_dump())
        db.add(location)
        await db.commit()
        await db.refresh(location)
        return location
    
    @staticmethod
    async def update_location(
        db: AsyncSession,
        location_id: uuid.UUID,
        data: LocationUpdate
    ) -> Optional[Location]:
        """Update location"""
        location = await LocationService.get_location_by_id(db, location_id)
        if not location:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(location, field, value)
        
        await db.commit()
        await db.refresh(location)
        return location
    
    @staticmethod
    async def delete_location(db: AsyncSession, location_id: uuid.UUID) -> bool:
        """Delete location (soft delete - set is_active=false)"""
        location = await LocationService.get_location_by_id(db, location_id)
        if not location:
            return False
        
        # Check if location has inventory
        query = select(ArticleLocation).where(
            and_(
                ArticleLocation.location_id == location_id,
                ArticleLocation.quantity > 0
            )
        )
        result = await db.execute(query)
        has_inventory = result.scalar_one_or_none() is not None
        
        if has_inventory:
            raise ValueError("Cannot delete location with inventory. Move articles first.")
        
        location.is_active = False
        await db.commit()
        return True
    
    @staticmethod
    async def get_available_bins(
        db: AsyncSession,
        magacin_id: uuid.UUID,
        zona: Optional[str] = None,
        min_capacity: Optional[float] = None
    ) -> List[Location]:
        """Get available bins with capacity"""
        query = select(Location).where(
            and_(
                Location.magacin_id == magacin_id,
                Location.tip == LocationType.BIN,
                Location.is_active == True
            )
        )
        
        if zona:
            query = query.where(Location.zona == zona)
        
        result = await db.execute(query)
        bins = result.scalars().all()
        
        # Filter by available capacity
        if min_capacity:
            bins = [
                b for b in bins
                if not b.capacity_max or (float(b.capacity_max) - float(b.capacity_current)) >= min_capacity
            ]
        
        return bins
    
    # ========================================================================
    # Article Location Management
    # ========================================================================
    
    @staticmethod
    async def assign_article_to_location(
        db: AsyncSession,
        data: ArticleLocationCreate
    ) -> ArticleLocation:
        """Assign article to location"""
        # Check if assignment already exists
        query = select(ArticleLocation).where(
            and_(
                ArticleLocation.artikal_id == data.artikal_id,
                ArticleLocation.location_id == data.location_id
            )
        )
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update quantity
            existing.quantity += data.quantity
            existing.last_moved_at = datetime.now(timezone.utc)
        else:
            # Create new assignment
            existing = ArticleLocation(**data.model_dump())
            existing.last_moved_at = datetime.now(timezone.utc)
            db.add(existing)
        
        # Update location capacity
        location = await LocationService.get_location_by_id(db, data.location_id)
        if location:
            location.capacity_current += data.quantity
        
        await db.commit()
        await db.refresh(existing)
        return existing
    
    @staticmethod
    async def get_articles_in_location(
        db: AsyncSession,
        location_id: uuid.UUID
    ) -> List[ArticleInLocationDetail]:
        """Get all articles in a location"""
        query = select(ArticleLocation).where(
            and_(
                ArticleLocation.location_id == location_id,
                ArticleLocation.quantity > 0
            )
        ).options(selectinload(ArticleLocation.artikal))
        
        result = await db.execute(query)
        article_locs = result.scalars().all()
        
        return [
            ArticleInLocationDetail(
                artikal_id=al.artikal_id,
                sifra=al.artikal.sifra,
                naziv=al.artikal.naziv,
                quantity=al.quantity,
                uom=al.uom,
                is_primary_location=al.is_primary_location,
                last_counted_at=al.last_counted_at
            )
            for al in article_locs
        ]
    
    @staticmethod
    async def get_article_locations(
        db: AsyncSession,
        artikal_id: uuid.UUID
    ) -> List[ArticleLocation]:
        """Get all locations for an article"""
        query = select(ArticleLocation).where(
            and_(
                ArticleLocation.artikal_id == artikal_id,
                ArticleLocation.quantity > 0
            )
        ).options(selectinload(ArticleLocation.location))
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def move_article(
        db: AsyncSession,
        artikal_id: uuid.UUID,
        from_location_id: uuid.UUID,
        to_location_id: uuid.UUID,
        quantity: Decimal
    ) -> tuple[ArticleLocation, ArticleLocation]:
        """Move article from one location to another"""
        # Get source article location
        query = select(ArticleLocation).where(
            and_(
                ArticleLocation.artikal_id == artikal_id,
                ArticleLocation.location_id == from_location_id
            )
        )
        result = await db.execute(query)
        source = result.scalar_one_or_none()
        
        if not source or source.quantity < quantity:
            raise ValueError("Insufficient quantity in source location")
        
        # Reduce source
        source.quantity -= quantity
        source.last_moved_at = datetime.now(timezone.utc)
        
        # Update source location capacity
        from_location = await LocationService.get_location_by_id(db, from_location_id)
        if from_location:
            from_location.capacity_current -= quantity
        
        # Add to destination
        dest_data = ArticleLocationCreate(
            artikal_id=artikal_id,
            location_id=to_location_id,
            quantity=quantity,
            uom=source.uom
        )
        dest = await LocationService.assign_article_to_location(db, dest_data)
        
        await db.commit()
        return source, dest

