"""
Picking route optimization service
Manhattan Active WMS - Directed Picking
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.zaduznica import Zaduznica, ZaduznicaStavka
from ..models.locations import Location, ArticleLocation
from ..models.enums import LocationType
from ..schemas.locations import (
    PickRouteGenerateRequest,
    PickRouteResponse,
    PickTaskLocation,
)


class PickingService:
    """
    Route optimization using:
    - Nearest Neighbor algorithm (fast, 80-90% optimal)
    - TSP (Traveling Salesman) heuristic for smaller batches
    """
    
    @staticmethod
    async def generate_pick_route(
        db: AsyncSession,
        request: PickRouteGenerateRequest
    ) -> PickRouteResponse:
        """Generate optimized picking route for zaduznica"""
        
        # Get zaduznica with items
        query = select(Zaduznica).where(Zaduznica.id == request.zaduznica_id).options(
            selectinload(Zaduznica.stavke).selectinload(ZaduznicaStavka.artikal)
        )
        result = await db.execute(query)
        zaduznica = result.scalar_one_or_none()
        
        if not zaduznica:
            raise ValueError(f"Zaduznica {request.zaduznica_id} not found")
        
        # Get location for each item (primary location or first available)
        tasks = []
        for stavka in zaduznica.stavke:
            # Find article location with enough quantity
            query = select(ArticleLocation).where(
                and_(
                    ArticleLocation.artikal_id == stavka.artikal_id,
                    ArticleLocation.quantity >= stavka.kolicina
                )
            ).options(selectinload(ArticleLocation.location)).order_by(
                ArticleLocation.is_primary_location.desc(),
                ArticleLocation.quantity.desc()
            )
            result = await db.execute(query)
            article_loc = result.scalars().first()
            
            if article_loc:
                tasks.append({
                    'stavka_id': stavka.id,
                    'artikal_sifra': stavka.artikal.sifra,
                    'artikal_naziv': stavka.artikal.naziv,
                    'location_id': article_loc.location_id,
                    'location': article_loc.location,
                    'quantity': stavka.kolicina
                })
        
        # Optimize route
        if request.algorithm == 'tsp' and len(tasks) <= 10:
            # Use TSP for small batches
            optimized_tasks = await PickingService._optimize_route_tsp(tasks)
        else:
            # Use nearest neighbor (default)
            optimized_tasks = await PickingService._optimize_route_nearest_neighbor(tasks)
        
        # Assign pick_sequence to zaduznica_stavke
        for idx, task in enumerate(optimized_tasks, start=1):
            query = select(ZaduznicaStavka).where(ZaduznicaStavka.id == task['stavka_id'])
            result = await db.execute(query)
            stavka = result.scalar_one_or_none()
            if stavka:
                stavka.pick_sequence = idx
                stavka.pick_location_id = task['location_id']
        
        # Create pick_route record
        from ..models.locations import PickRoute
        route_data = [
            {
                'sequence': idx,
                'stavka_id': str(task['stavka_id']),
                'location_id': str(task['location_id']),
                'location_code': task['location'].code
            }
            for idx, task in enumerate(optimized_tasks, start=1)
        ]
        
        pick_route = PickRoute(
            zaduznica_id=zaduznica.id,
            route_data=route_data,
            total_distance_meters=None,  # TODO: Calculate based on coordinates
            estimated_time_minutes=len(tasks) * 2  # 2 min per pick
        )
        db.add(pick_route)
        
        await db.commit()
        await db.refresh(pick_route)
        
        # Build response
        pick_tasks = [
            PickTaskLocation(
                stavka_id=task['stavka_id'],
                artikal_sifra=task['artikal_sifra'],
                artikal_naziv=task['artikal_naziv'],
                location_id=task['location_id'],
                location_code=task['location'].code,
                location_full_path=task['location'].full_path,
                quantity=task['quantity'],
                sequence=idx
            )
            for idx, task in enumerate(optimized_tasks, start=1)
        ]
        
        return PickRouteResponse(
            zaduznica_id=zaduznica.id,
            route_id=pick_route.id,
            tasks=pick_tasks,
            total_distance_meters=pick_route.total_distance_meters,
            estimated_time_minutes=pick_route.estimated_time_minutes,
            created_at=pick_route.created_at
        )
    
    @staticmethod
    async def _optimize_route_nearest_neighbor(tasks: List[dict]) -> List[dict]:
        """
        Nearest Neighbor algorithm for route optimization
        O(n²) complexity, fast and 80-90% optimal
        """
        if not tasks:
            return []
        
        # Start from receiving dock (assume zone A, lowest X/Y)
        current_location = None
        optimized = []
        remaining = tasks.copy()
        
        while remaining:
            if current_location is None:
                # Start with zone A, smallest coordinates
                remaining.sort(key=lambda t: (
                    t['location'].zona or 'Z',
                    float(t['location'].x_coordinate or 999),
                    float(t['location'].y_coordinate or 999)
                ))
                next_task = remaining.pop(0)
            else:
                # Find nearest location
                nearest_idx = 0
                min_distance = float('inf')
                
                for idx, task in enumerate(remaining):
                    dist = PickingService._calculate_distance(
                        current_location,
                        task['location']
                    )
                    if dist < min_distance:
                        min_distance = dist
                        nearest_idx = idx
                
                next_task = remaining.pop(nearest_idx)
            
            optimized.append(next_task)
            current_location = next_task['location']
        
        return optimized
    
    @staticmethod
    async def _optimize_route_tsp(tasks: List[dict]) -> List[dict]:
        """
        Simple TSP heuristic (2-opt improvement on nearest neighbor)
        For small batches (<=10 items)
        """
        # Start with nearest neighbor
        route = await PickingService._optimize_route_nearest_neighbor(tasks)
        
        if len(route) <= 2:
            return route
        
        # 2-opt improvement (limited iterations)
        improved = True
        iterations = 0
        max_iterations = min(len(route) * 2, 50)
        
        while improved and iterations < max_iterations:
            improved = False
            iterations += 1
            
            for i in range(1, len(route) - 1):
                for j in range(i + 1, len(route)):
                    # Try reversing segment [i:j]
                    new_route = route[:i] + route[i:j][::-1] + route[j:]
                    
                    # Compare distances
                    old_dist = PickingService._total_route_distance(route)
                    new_dist = PickingService._total_route_distance(new_route)
                    
                    if new_dist < old_dist:
                        route = new_route
                        improved = True
                        break
                
                if improved:
                    break
        
        return route
    
    @staticmethod
    def _calculate_distance(loc1: Location, loc2: Location) -> float:
        """Calculate distance between two locations (Manhattan distance)"""
        if loc1.x_coordinate and loc1.y_coordinate and loc2.x_coordinate and loc2.y_coordinate:
            dx = abs(float(loc1.x_coordinate) - float(loc2.x_coordinate))
            dy = abs(float(loc1.y_coordinate) - float(loc2.y_coordinate))
            return dx + dy  # Manhattan distance for warehouse grid
        
        # Fallback: zone-based heuristic
        if loc1.zona != loc2.zona:
            return 100  # Different zones = far
        elif loc1.parent_id != loc2.parent_id:
            return 20   # Different regals = medium
        else:
            return 5    # Same regal = close
    
    @staticmethod
    def _total_route_distance(route: List[dict]) -> float:
        """Calculate total route distance"""
        if len(route) <= 1:
            return 0.0
        
        total = 0.0
        for i in range(len(route) - 1):
            total += PickingService._calculate_distance(
                route[i]['location'],
                route[i + 1]['location']
            )
        return total
    
    @staticmethod
    async def get_pick_route(
        db: AsyncSession,
        zaduznica_id: uuid.UUID
    ) -> Optional[PickRouteResponse]:
        """Get existing pick route for zaduznica"""
        from ..models.locations import PickRoute
        
        query = select(PickRoute).where(PickRoute.zaduznica_id == zaduznica_id)
        result = await db.execute(query)
        pick_route = result.scalar_one_or_none()
        
        if not pick_route:
            return None
        
        # Reconstruct tasks from route_data
        tasks = []
        for item in pick_route.route_data:
            stavka_id = uuid.UUID(item['stavka_id'])
            location_id = uuid.UUID(item['location_id'])
            
            # Get stavka details
            query = select(ZaduznicaStavka).where(ZaduznicaStavka.id == stavka_id).options(
                selectinload(ZaduznicaStavka.artikal)
            )
            result = await db.execute(query)
            stavka = result.scalar_one_or_none()
            
            # Get location details
            query = select(Location).where(Location.id == location_id)
            result = await db.execute(query)
            location = result.scalar_one_or_none()
            
            if stavka and location:
                tasks.append(PickTaskLocation(
                    stavka_id=stavka.id,
                    artikal_sifra=stavka.artikal.sifra,
                    artikal_naziv=stavka.artikal.naziv,
                    location_id=location.id,
                    location_code=location.code,
                    location_full_path=location.full_path,
                    quantity=stavka.kolicina,
                    sequence=item['sequence']
                ))
        
        # Sort by sequence
        tasks.sort(key=lambda t: t.sequence)
        
        return PickRouteResponse(
            zaduznica_id=pick_route.zaduznica_id,
            route_id=pick_route.id,
            tasks=tasks,
            total_distance_meters=pick_route.total_distance_meters,
            estimated_time_minutes=pick_route.estimated_time_minutes,
            created_at=pick_route.created_at
        )

