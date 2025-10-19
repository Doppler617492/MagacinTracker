"""Team model for shift-based warehouse operations."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Team(Base):
    """
    Team model representing a pair of workers operating together on a shift.
    Teams are the primary unit of work assignment and performance tracking.
    """
    __tablename__ = "team"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    
    # Team members - exactly 2 workers per team
    worker1_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    worker2_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Shift assignment: 'A' or 'B'
    shift: Mapped[str] = mapped_column(String(1), nullable=False, index=True)
    
    # Team status
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    worker1: Mapped["UserAccount"] = relationship(
        "UserAccount", foreign_keys=[worker1_id], lazy="joined"
    )
    worker2: Mapped["UserAccount"] = relationship(
        "UserAccount", foreign_keys=[worker2_id], lazy="joined"
    )
    
    def __repr__(self) -> str:
        return f"<Team {self.name} - Shift {self.shift}>"
    
    @property
    def members(self) -> list[uuid.UUID]:
        """Return list of team member IDs."""
        return [self.worker1_id, self.worker2_id]
    
    def has_member(self, user_id: uuid.UUID) -> bool:
        """Check if a user is a member of this team."""
        return user_id in [self.worker1_id, self.worker2_id]
    
    def get_partner_id(self, user_id: uuid.UUID) -> Optional[uuid.UUID]:
        """Get the ID of the other team member."""
        if user_id == self.worker1_id:
            return self.worker2_id
        elif user_id == self.worker2_id:
            return self.worker1_id
        return None

