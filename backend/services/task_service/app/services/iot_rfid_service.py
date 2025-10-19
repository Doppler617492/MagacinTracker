"""
RFID Gateway Service - Event processing & tag binding
Manhattan Active WMS - Phase 5
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import and_, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.iot_models import RFIDEvent, RFIDTagBinding
from ..models.enums import RFIDEventType, AuditAction


class RFIDService:
    """
    RFID Gateway integration for:
    - Entry/exit tracking (vehicles, pallets, roll-containers)
    - Dock door activity monitoring
    - Document/location binding
    """
    
    # Antenna zone mapping (example - configure per warehouse)
    ANTENNA_ZONES = {
        'ANT01': 'DOCK-D1',  # Prijem
        'ANT02': 'DOCK-D2',  # Otprema
        'ANT03': 'COLD-01',  # Hladnjača
    }
    
    @staticmethod
    async def process_rfid_event(
        db: AsyncSession,
        gateway_id: str,
        antenna_id: Optional[str],
        tag_id: str,
        rssi: Optional[int],
        timestamp: datetime,
        event_type: RFIDEventType = RFIDEventType.READ,
        raw_data: dict = None
    ) -> RFIDEvent:
        """
        Process incoming RFID event
        
        Returns:
            RFIDEvent record
        """
        # Determine zone from antenna
        zone = RFIDService.ANTENNA_ZONES.get(antenna_id or '', None)
        
        # Create event
        event = RFIDEvent(
            gateway_id=gateway_id,
            antenna_id=antenna_id,
            tag_id=tag_id,
            event_type=event_type,
            rssi=rssi,
            zone=zone,
            raw_data=raw_data or {},
            timestamp=timestamp,
            processed_at=datetime.now(timezone.utc)
        )
        db.add(event)
        
        # Check if tag is bound to entity
        binding = await RFIDService.get_active_binding(db, tag_id)
        
        if binding:
            # Trigger entity-specific logic
            if binding.entity_type == 'prijem':
                # Mark receiving as "container at dock"
                await RFIDService._process_prijem_arrival(db, binding.entity_id, zone)
            elif binding.entity_type == 'otprema':
                # Confirm presence for outbound
                await RFIDService._process_otprema_confirmation(db, binding.entity_id, zone)
            elif binding.entity_type == 'lokacija':
                # Asset tracking (container at location)
                pass  # Future enhancement
        
        # Audit log
        from ..models.audit import AuditLog
        audit = AuditLog(
            user_id=None,  # System event
            action=AuditAction.RFID_EVENT_RECEIVED,
            entity_type='rfid_event',
            entity_id=event.id,
            details={
                'gateway_id': gateway_id,
                'tag_id': tag_id,
                'event_type': event_type.value,
                'zone': zone,
                'bound_entity': f"{binding.entity_type}:{binding.entity_id}" if binding else None
            }
        )
        db.add(audit)
        
        await db.commit()
        await db.refresh(event)
        
        return event
    
    @staticmethod
    async def _process_prijem_arrival(
        db: AsyncSession,
        prijem_id: uuid.UUID,
        zone: Optional[str]
    ):
        """Mark receiving document as 'container at dock'"""
        from ..models.receiving import ReceivingHeader
        
        prijem = await db.get(ReceivingHeader, prijem_id)
        if prijem:
            prijem.metadata = prijem.metadata or {}
            prijem.metadata['rfid_confirmed'] = True
            prijem.metadata['rfid_zone'] = zone
            prijem.metadata['rfid_confirmed_at'] = datetime.now(timezone.utc).isoformat()
            # Optionally trigger put-away suggestion flow
    
    @staticmethod
    async def _process_otprema_confirmation(
        db: AsyncSession,
        zaduznica_id: uuid.UUID,
        zone: Optional[str]
    ):
        """Confirm outbound document presence at dock"""
        from ..models.zaduznica import Zaduznica
        
        zaduznica = await db.get(Zaduznica, zaduznica_id)
        if zaduznica:
            zaduznica.metadata = zaduznica.metadata or {}
            zaduznica.metadata['rfid_confirmed'] = True
            zaduznica.metadata['rfid_zone'] = zone
            zaduznica.metadata['rfid_confirmed_at'] = datetime.now(timezone.utc).isoformat()
    
    @staticmethod
    async def bind_tag(
        db: AsyncSession,
        tag_id: str,
        entity_type: str,
        entity_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None
    ) -> RFIDTagBinding:
        """
        Bind RFID tag to entity (prijem, otprema, lokacija)
        
        Returns:
            RFIDTagBinding record
        """
        # Unbind existing if any
        existing = await RFIDService.get_active_binding(db, tag_id)
        if existing:
            existing.is_active = False
            existing.unbound_at = datetime.now(timezone.utc)
        
        # Create new binding
        binding = RFIDTagBinding(
            tag_id=tag_id,
            entity_type=entity_type,
            entity_id=entity_id,
            bound_by_id=user_id,
            bound_at=datetime.now(timezone.utc),
            is_active=True
        )
        db.add(binding)
        
        # Audit log
        from ..models.audit import AuditLog
        audit = AuditLog(
            user_id=user_id,
            action=AuditAction.RFID_TAG_BOUND,
            entity_type='rfid_tag_binding',
            entity_id=binding.id,
            details={
                'tag_id': tag_id,
                'bound_to_type': entity_type,
                'bound_to_id': str(entity_id)
            }
        )
        db.add(audit)
        
        await db.commit()
        await db.refresh(binding)
        
        return binding
    
    @staticmethod
    async def unbind_tag(
        db: AsyncSession,
        tag_id: str,
        user_id: Optional[uuid.UUID] = None
    ) -> bool:
        """Unbind RFID tag"""
        binding = await RFIDService.get_active_binding(db, tag_id)
        if not binding:
            return False
        
        binding.is_active = False
        binding.unbound_at = datetime.now(timezone.utc)
        
        # Audit log
        from ..models.audit import AuditLog
        audit = AuditLog(
            user_id=user_id,
            action=AuditAction.RFID_TAG_UNBOUND,
            entity_type='rfid_tag_binding',
            entity_id=binding.id,
            details={
                'tag_id': tag_id
            }
        )
        db.add(audit)
        
        await db.commit()
        return True
    
    @staticmethod
    async def get_active_binding(
        db: AsyncSession,
        tag_id: str
    ) -> Optional[RFIDTagBinding]:
        """Get active binding for tag"""
        query = select(RFIDTagBinding).where(
            and_(
                RFIDTagBinding.tag_id == tag_id,
                RFIDTagBinding.is_active == True
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_recent_events(
        db: AsyncSession,
        minutes: int = 60,
        gateway_id: Optional[str] = None,
        zone: Optional[str] = None
    ) -> List[RFIDEvent]:
        """Get recent RFID events"""
        since_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        
        from datetime import timedelta
        query = select(RFIDEvent).where(RFIDEvent.timestamp >= since_time)
        
        if gateway_id:
            query = query.where(RFIDEvent.gateway_id == gateway_id)
        if zone:
            query = query.where(RFIDEvent.zone == zone)
        
        query = query.order_by(desc(RFIDEvent.timestamp)).limit(100)
        
        result = await db.execute(query)
        return result.scalars().all()

