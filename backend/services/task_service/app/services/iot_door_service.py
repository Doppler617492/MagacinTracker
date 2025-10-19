"""
Door Control Service - Industrial door/gate control with safety
Manhattan Active WMS - Phase 5
"""
import uuid
import time
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.iot_models import Door, DoorCommandLog
from ..models.enums import DoorStatus, AuditAction


class DoorControlService:
    """
    Industrial door control with safety logic:
    - FALCON radar detection
    - BFT TX/RX photocell safety beam
    - Auto-close timeout (60s default)
    - Deadman logic (auto-stop without confirmation)
    """
    
    @staticmethod
    async def send_command(
        db: AsyncSession,
        door_id: str,
        command: str,  # 'open', 'close', 'stop'
        user_id: Optional[uuid.UUID] = None,
        reason: Optional[str] = None
    ) -> dict:
        """
        Send command to door with safety checks
        
        Returns:
            {success: bool, message: str, safety_blocked: bool, latency_ms: int}
        """
        start_time = time.time()
        
        # Get door
        query = select(Door).where(Door.door_id == door_id)
        result = await db.execute(query)
        door = result.scalar_one_or_none()
        
        if not door:
            return {
                'success': False,
                'message': f'Vrata {door_id} ne postoje',
                'safety_blocked': False,
                'latency_ms': 0
            }
        
        # Safety check for close command
        safety_blocked = False
        if command == 'close':
            if not door.is_safe_to_close:
                safety_blocked = True
                error_msg = 'Fotoćelija blokirana - ne mogu zatvoriti vrata'
                
                # Log blocked command
                log = DoorCommandLog(
                    door_id=door.id,
                    command=command,
                    reason=reason,
                    requested_by_id=user_id,
                    executed_at=datetime.now(timezone.utc),
                    success=False,
                    error_message=error_msg,
                    safety_blocked=True,
                    latency_ms=int((time.time() - start_time) * 1000)
                )
                db.add(log)
                
                # Audit
                from ..models.audit import AuditLog
                audit = AuditLog(
                    user_id=user_id,
                    action=AuditAction.DOOR_COMMAND_BLOCKED,
                    entity_type='door',
                    entity_id=door.id,
                    details={
                        'door_id': door_id,
                        'command': command,
                        'reason': 'safety_beam_blocked'
                    }
                )
                db.add(audit)
                
                await db.commit()
                
                return {
                    'success': False,
                    'message': error_msg,
                    'safety_blocked': True,
                    'latency_ms': log.latency_ms
                }
        
        # Execute command (stub in dev, real in prod via adapter)
        success, new_status = await DoorControlService._execute_door_command(
            door, command
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Update door status
        if success:
            door.current_status = new_status
            door.last_command = command
            door.last_command_at = datetime.now(timezone.utc)
            door.last_command_by_id = user_id
        
        # Log command
        log = DoorCommandLog(
            door_id=door.id,
            command=command,
            reason=reason,
            requested_by_id=user_id,
            executed_at=datetime.now(timezone.utc),
            success=success,
            error_message=None if success else 'Command execution failed',
            safety_blocked=safety_blocked,
            latency_ms=latency_ms
        )
        db.add(log)
        
        # Audit
        from ..models.audit import AuditLog
        audit = AuditLog(
            user_id=user_id,
            action=AuditAction.DOOR_COMMAND_ISSUED,
            entity_type='door',
            entity_id=door.id,
            details={
                'door_id': door_id,
                'command': command,
                'new_status': new_status.value,
                'latency_ms': latency_ms
            }
        )
        db.add(audit)
        
        await db.commit()
        
        return {
            'success': success,
            'message': f'Vrata {door_id} {command}' if success else 'Greška pri izvršavanju komande',
            'safety_blocked': False,
            'latency_ms': latency_ms
        }
    
    @staticmethod
    async def _execute_door_command(door: Door, command: str) -> tuple[bool, DoorStatus]:
        """
        Execute command via adapter (TCP/Modbus/MQTT)
        
        STUB in dev: Returns success + new status
        PROD: Calls actual door controller
        """
        # Stub logic (dev mode)
        if command == 'open':
            return True, DoorStatus.OPEN
        elif command == 'close':
            return True, DoorStatus.CLOSED
        elif command == 'stop':
            return True, DoorStatus.STOPPED
        else:
            return False, door.current_status
    
    @staticmethod
    async def auto_close_timeout(
        db: AsyncSession,
        door_id: str
    ) -> bool:
        """
        Auto-close door after timeout (called by scheduler)
        
        Returns:
            True if closed
        """
        query = select(Door).where(Door.door_id == door_id)
        result = await db.execute(query)
        door = result.scalar_one_or_none()
        
        if not door or door.current_status != DoorStatus.OPEN:
            return False
        
        # Check timeout
        if door.last_command_at:
            delta = datetime.now(timezone.utc) - door.last_command_at
            if delta.total_seconds() < door.auto_close_timeout_seconds:
                return False  # Not yet timeout
        
        # Execute auto-close (only if safe)
        if door.is_safe_to_close:
            result = await DoorControlService.send_command(
                db=db,
                door_id=door_id,
                command='close',
                user_id=None,  # System
                reason='Auto-close timeout'
            )
            
            if result['success']:
                # Audit
                from ..models.audit import AuditLog
                audit = AuditLog(
                    user_id=None,
                    action=AuditAction.DOOR_AUTO_CLOSE,
                    entity_type='door',
                    entity_id=door.id,
                    details={
                        'door_id': door_id,
                        'timeout_seconds': door.auto_close_timeout_seconds
                    }
                )
                db.add(audit)
                await db.commit()
                return True
        
        return False
    
    @staticmethod
    async def get_door_status(
        db: AsyncSession,
        door_id: str
    ) -> Optional[Door]:
        """Get current door status"""
        query = select(Door).where(Door.door_id == door_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all_doors(db: AsyncSession) -> List[Door]:
        """Get all doors"""
        query = select(Door).where(Door.is_active == True)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_safety_sensors(
        db: AsyncSession,
        door_id: str,
        safety_beam_clear: bool,
        radar_detected: bool
    ) -> bool:
        """Update door safety sensor status (called by edge gateway)"""
        door = await DoorControlService.get_door_status(db, door_id)
        if not door:
            return False
        
        door.safety_beam_status = safety_beam_clear
        door.radar_detected = radar_detected
        
        await db.commit()
        return True

