from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app_common.security import get_password_hash, verify_password

from ..models.enums import Role
from ..models.user import UserAccount
from ..schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[UserAccount]:
        """Get user by ID"""
        result = await self.db.execute(
            select(UserAccount).filter(UserAccount.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[UserAccount]:
        """Get user by email (case-insensitive)"""
        result = await self.db.execute(
            select(UserAccount).filter(
                func.lower(UserAccount.email) == email.lower()
            )
        )
        return result.scalar_one_or_none()

    def authenticate_user(self, email: str, password: str) -> Optional[UserAccount]:
        """Authenticate user with email and password"""
        user = self.get_user_by_email(email)
        if not user or not user.is_active:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        self.db.commit()
        
        return user

    def create_user(self, user_data: UserCreate, created_by: uuid.UUID) -> UserAccount:
        """Create a new user"""
        # Check if user already exists
        existing_user = self.get_user_by_email(user_data.email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Hash password
        password_hash = get_password_hash(user_data.password)
        
        # Create user
        user = UserAccount(
            email=user_data.email.lower(),
            password_hash=password_hash,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role,
            is_active=user_data.is_active,
            created_by=created_by
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user

    def update_user(self, user_id: uuid.UUID, user_data: UserUpdate) -> Optional[UserAccount]:
        """Update user information"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Update fields
        if user_data.first_name is not None:
            user.first_name = user_data.first_name
        if user_data.last_name is not None:
            user.last_name = user_data.last_name
        if user_data.role is not None:
            user.role = user_data.role
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        user.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(user)
        
        return user

    def reset_user_password(self, user_id: uuid.UUID, new_password: str) -> Optional[UserAccount]:
        """Reset user password"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Hash new password
        password_hash = get_password_hash(new_password)
        user.password_hash = password_hash
        user.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(user)
        
        return user

    def deactivate_user(self, user_id: uuid.UUID) -> Optional[UserAccount]:
        """Deactivate user (soft delete)"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(user)
        
        return user

    def list_users(
        self, 
        page: int = 1, 
        per_page: int = 50, 
        role_filter: Optional[Role] = None,
        active_filter: Optional[bool] = None,
        search: Optional[str] = None
    ) -> tuple[list[UserAccount], int]:
        """List users with pagination and filters"""
        query = self.db.query(UserAccount)
        
        # Apply filters
        if role_filter:
            query = query.filter(UserAccount.role == role_filter)
        
        if active_filter is not None:
            query = query.filter(UserAccount.is_active == active_filter)
        
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    func.lower(UserAccount.first_name).like(search_term),
                    func.lower(UserAccount.last_name).like(search_term),
                    func.lower(UserAccount.email).like(search_term)
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        users = query.offset(offset).limit(per_page).all()
        
        return users, total

    def get_users_by_role(self, role: Role) -> list[UserAccount]:
        """Get all users with a specific role"""
        return self.db.query(UserAccount).filter(
            and_(UserAccount.role == role, UserAccount.is_active == True)
        ).all()

    def get_active_users_count(self) -> int:
        """Get count of active users"""
        return self.db.query(UserAccount).filter(UserAccount.is_active == True).count()

    def get_users_count_by_role(self) -> dict[Role, int]:
        """Get count of users by role"""
        result = self.db.query(
            UserAccount.role, 
            func.count(UserAccount.id)
        ).filter(
            UserAccount.is_active == True
        ).group_by(UserAccount.role).all()
        
        return {role: count for role, count in result}
