"""
Subject/Partner models for Pantheon ERP integration
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .enums import SubjectType


class Subject(Base):
    """
    Subject/Partner model (synchronized from Pantheon ERP via GetSubjectWMS)
    Represents suppliers, customers, and warehouses
    """
    __tablename__ = "subjects"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[SubjectType] = mapped_column(index=True)
    
    # Contact details
    pib: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    
    # Status
    aktivan: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Sync tracking
    time_chg_ts: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="PANTHEON")

