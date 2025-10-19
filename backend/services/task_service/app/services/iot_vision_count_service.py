"""
Vision Count Service - Photo-based cycle counting
Manhattan Active WMS - Phase 5
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.iot_models import VisionCountTask
from ..models.enums import AuditAction


class VisionCountService:
    """
    Vision-based cycle counting:
    - Worker takes photo of bin/shelf
    - Manually enters quantity
    - Manager reviews photo + quantity
    - Approves or rejects
    """
    
    @staticmethod
    async def create_vision_count(
        db: AsyncSession,
        location_id: uuid.UUID,
        artikal_id: Optional[uuid.UUID] = None,
        system_quantity: Optional[Decimal] = None,
        assigned_to_id: Optional[uuid.UUID] = None
    ) -> VisionCountTask:
        """Create new vision count task"""
        task = VisionCountTask(
            location_id=location_id,
            artikal_id=artikal_id,
            system_quantity=system_quantity,
            status='pending',
            assigned_to_id=assigned_to_id
        )
        db.add(task)
        
        # Audit
        from ..models.audit import AuditLog
        audit = AuditLog(
            user_id=assigned_to_id,
            action=AuditAction.VISION_COUNT_STARTED,
            entity_type='vision_count_task',
            entity_id=task.id,
            details={
                'location_id': str(location_id),
                'artikal_id': str(artikal_id) if artikal_id else None
            }
        )
        db.add(audit)
        
        await db.commit()
        await db.refresh(task)
        
        return task
    
    @staticmethod
    async def submit_vision_count(
        db: AsyncSession,
        task_id: uuid.UUID,
        counted_quantity: Decimal,
        photo_ids: List[uuid.UUID],
        comment: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None
    ) -> VisionCountTask:
        """
        Submit vision count with photo and quantity
        
        Args:
            task_id: Vision count task ID
            counted_quantity: Manually entered quantity
            photo_ids: List of uploaded photo IDs (max 5)
            comment: Required if variance exists
            user_id: Worker who counted
        
        Returns:
            Updated VisionCountTask
        """
        task = await db.get(VisionCountTask, task_id)
        if not task:
            raise ValueError('Vision count task ne postoji')
        
        # Calculate variance
        if task.system_quantity is not None:
            task.variance = counted_quantity - task.system_quantity
        
        # Update task
        task.counted_quantity = counted_quantity
        task.photo_ids = [str(photo_id) for photo_id in photo_ids[:5]]  # Max 5
        task.comment = comment
        task.status = 'submitted'
        task.submitted_at = datetime.now(timezone.utc)
        
        # Validate: comment required if variance
        if task.has_variance and not comment:
            raise ValueError('Komentar obavezan kada postoji odstupanje')
        
        # Audit
        from ..models.audit import AuditLog
        audit = AuditLog(
            user_id=user_id,
            action=AuditAction.VISION_COUNT_SUBMITTED,
            entity_type='vision_count_task',
            entity_id=task_id,
            details={
                'counted_quantity': float(counted_quantity),
                'variance': float(task.variance) if task.variance else None,
                'photo_count': len(task.photo_ids),
                'comment': comment
            }
        )
        db.add(audit)
        
        await db.commit()
        await db.refresh(task)
        
        return task
    
    @staticmethod
    async def approve_vision_count(
        db: AsyncSession,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        review_note: Optional[str] = None
    ) -> VisionCountTask:
        """
        Approve vision count and adjust inventory
        
        Args:
            task_id: Vision count task ID
            user_id: Manager who approved
            review_note: Optional note
        
        Returns:
            Approved VisionCountTask
        """
        task = await db.get(VisionCountTask, task_id)
        if not task or task.status != 'submitted':
            raise ValueError('Vision count task nije u stanju za odobravanje')
        
        # Update task
        task.status = 'approved'
        task.reviewed_by_id = user_id
        task.reviewed_at = datetime.now(timezone.utc)
        task.review_note = review_note
        
        # Adjust inventory if variance exists
        if task.has_variance and task.artikal_id:
            from ..models.locations import ArticleLocation
            
            query = select(ArticleLocation).where(
                and_(
                    ArticleLocation.artikal_id == task.artikal_id,
                    ArticleLocation.location_id == task.location_id
                )
            )
            result = await db.execute(query)
            article_loc = result.scalar_one_or_none()
            
            if article_loc:
                # Adjust quantity
                article_loc.quantity = task.counted_quantity
                article_loc.last_counted_at = datetime.now(timezone.utc)
        
        # Audit
        from ..models.audit import AuditLog
        audit = AuditLog(
            user_id=user_id,
            action=AuditAction.VISION_COUNT_APPROVED,
            entity_type='vision_count_task',
            entity_id=task_id,
            details={
                'counted_quantity': float(task.counted_quantity),
                'variance': float(task.variance) if task.variance else None,
                'review_note': review_note
            }
        )
        db.add(audit)
        
        await db.commit()
        await db.refresh(task)
        
        return task
    
    @staticmethod
    async def reject_vision_count(
        db: AsyncSession,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        review_note: str
    ) -> VisionCountTask:
        """
        Reject vision count (send back to worker)
        
        Args:
            task_id: Vision count task ID
            user_id: Manager who rejected
            review_note: Reason for rejection (required)
        
        Returns:
            Rejected VisionCountTask (status = 'pending' again)
        """
        task = await db.get(VisionCountTask, task_id)
        if not task or task.status != 'submitted':
            raise ValueError('Vision count task nije u stanju za odbijanje')
        
        # Reset to pending
        task.status = 'pending'
        task.reviewed_by_id = user_id
        task.reviewed_at = datetime.now(timezone.utc)
        task.review_note = review_note
        # Clear submission data
        task.submitted_at = None
        task.counted_quantity = None
        task.variance = None
        task.photo_ids = []
        task.comment = None
        
        # Audit
        from ..models.audit import AuditLog
        audit = AuditLog(
            user_id=user_id,
            action=AuditAction.VISION_COUNT_REJECTED,
            entity_type='vision_count_task',
            entity_id=task_id,
            details={
                'review_note': review_note
            }
        )
        db.add(audit)
        
        await db.commit()
        await db.refresh(task)
        
        return task
    
    @staticmethod
    async def get_pending_vision_counts(
        db: AsyncSession,
        status: Optional[str] = None,
        assigned_to_id: Optional[uuid.UUID] = None
    ) -> List[VisionCountTask]:
        """Get vision count tasks"""
        query = select(VisionCountTask)
        
        filters = []
        if status:
            filters.append(VisionCountTask.status == status)
        if assigned_to_id:
            filters.append(VisionCountTask.assigned_to_id == assigned_to_id)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.order_by(VisionCountTask.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()

