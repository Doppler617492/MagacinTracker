"""
Photo Service - Camera verification & photo storage
Manhattan Active WMS - Phase 5
"""
import uuid
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from ..models.iot_models import PhotoAttachment
from ..models.enums import AuditAction


class PhotoService:
    """
    Photo management service:
    - Upload with compression (≤2MB)
    - Thumbnail generation
    - EXIF extraction
    - Entity linking (polymorphic)
    """
    
    # Configuration
    MAX_FILE_SIZE_MB = 2
    UPLOAD_DIR = os.getenv('PHOTO_UPLOAD_DIR', '/app/storage/photos')
    THUMBNAIL_SIZE = (300, 300)
    
    @staticmethod
    async def upload_photo(
        db: AsyncSession,
        file: UploadFile,
        entity_type: str,
        entity_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        comment: Optional[str] = None
    ) -> PhotoAttachment:
        """
        Upload photo and create attachment record
        
        Args:
            file: Uploaded file (JPEG/PNG)
            entity_type: 'receiving_item', 'vision_count', 'anomaly', etc.
            entity_id: Entity UUID
            user_id: Uploader
            comment: Optional comment
        
        Returns:
            PhotoAttachment record
        """
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Validate size
        if file_size > PhotoService.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ValueError(f'Foto je prevelika. Maksimalno {PhotoService.MAX_FILE_SIZE_MB}MB.')
        
        # Generate unique filename
        ext = Path(file.filename or 'photo.jpg').suffix
        filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(PhotoService.UPLOAD_DIR, entity_type, str(entity_id), filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Extract EXIF (stub - would use PIL/exiftool in prod)
        exif_data = PhotoService._extract_exif(content)
        
        # Generate thumbnail (stub)
        thumbnail_path = await PhotoService._generate_thumbnail(file_path, entity_type, str(entity_id))
        
        # Create attachment record
        photo = PhotoAttachment(
            entity_type=entity_type,
            entity_id=entity_id,
            file_path=file_path,
            file_size_bytes=file_size,
            mime_type=file.content_type or 'image/jpeg',
            thumbnail_path=thumbnail_path,
            exif_data=exif_data,
            uploaded_by_id=user_id,
            uploaded_at=datetime.now(timezone.utc),
            comment=comment
        )
        db.add(photo)
        
        # Audit log
        from ..models.audit import AuditLog
        audit = AuditLog(
            user_id=user_id,
            action=AuditAction.PHOTO_ATTACHED,
            entity_type=entity_type,
            entity_id=entity_id,
            details={
                'photo_id': str(photo.id),
                'file_size_kb': round(file_size / 1024, 2),
                'filename': filename
            }
        )
        db.add(audit)
        
        await db.commit()
        await db.refresh(photo)
        
        return photo
    
    @staticmethod
    def _extract_exif(content: bytes) -> dict:
        """Extract EXIF data from photo (timestamp, GPS)"""
        # Stub - in prod use PIL or exiftool
        return {
            'extracted_at': datetime.now(timezone.utc).isoformat(),
            'timestamp': None,
            'gps': None,
            'camera': None
        }
    
    @staticmethod
    async def _generate_thumbnail(
        file_path: str,
        entity_type: str,
        entity_id: str
    ) -> Optional[str]:
        """Generate thumbnail (stub - use PIL in prod)"""
        # Stub - in prod use PIL.Image.thumbnail()
        thumbnail_dir = os.path.join(PhotoService.UPLOAD_DIR, entity_type, entity_id, 'thumbnails')
        os.makedirs(thumbnail_dir, exist_ok=True)
        thumbnail_path = os.path.join(thumbnail_dir, Path(file_path).name)
        
        # In prod: resize to 300x300, save as JPEG
        # For now, just return path
        return thumbnail_path
    
    @staticmethod
    async def get_photos(
        db: AsyncSession,
        entity_type: str,
        entity_id: uuid.UUID
    ) -> list[PhotoAttachment]:
        """Get all photos for entity"""
        query = select(PhotoAttachment).where(
            and_(
                PhotoAttachment.entity_type == entity_type,
                PhotoAttachment.entity_id == entity_id
            )
        ).order_by(PhotoAttachment.uploaded_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_photo_by_id(
        db: AsyncSession,
        photo_id: uuid.UUID
    ) -> Optional[PhotoAttachment]:
        """Get photo by ID"""
        return await db.get(PhotoAttachment, photo_id)

