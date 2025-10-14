from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple, List

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
        result = await self.db.execute(select(UserAccount).where(UserAccount.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[UserAccount]:
        """Get user by email (case-insensitive)"""
        result = await self.db.execute(
            select(UserAccount).where(func.lower(UserAccount.email) == email.lower())
        )
        return result.scalar_one_or_none()

    async def authenticate_user(self, email: str, password: str) -> Optional[UserAccount]:
        """Authenticate user with email and password"""
        user = await self.get_user_by_email(email)
        if not user or not user.is_active:
            return None

        if not verify_password(password, user.password_hash):
            return None

        # Update last login
        user.last_login = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def create_user(self, user_data: UserCreate, created_by: uuid.UUID) -> UserAccount:
        """Create a new user"""
        # Check if user already exists
        existing_user = await self.get_user_by_email(user_data.email)
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
            created_by=created_by,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def update_user(self, user_id: uuid.UUID, user_data: UserUpdate) -> Optional[UserAccount]:
        """Update user information"""
        user = await self.get_user_by_id(user_id)
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

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def reset_user_password(self, user_id: uuid.UUID, new_password: str) -> Optional[UserAccount]:
        """Reset user password"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        # Hash new password
        password_hash = get_password_hash(new_password)
        user.password_hash = password_hash
        user.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def deactivate_user(self, user_id: uuid.UUID) -> Optional[UserAccount]:
        """Deactivate user (soft delete)"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def list_users(
        self,
        page: int = 1,
        per_page: int = 50,
        role_filter: Optional[Role] = None,
        active_filter: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[UserAccount], int]:
        """List users with pagination and filters"""
        conditions = []
        if role_filter:
            conditions.append(UserAccount.role == role_filter)
        if active_filter is not None:
            conditions.append(UserAccount.is_active == active_filter)
        if search:
            search_term = f"%{search.lower()}%"
            conditions.append(
                or_(
                    func.lower(UserAccount.first_name).like(search_term),
                    func.lower(UserAccount.last_name).like(search_term),
                    func.lower(UserAccount.email).like(search_term),
                )
            )

        stmt = select(UserAccount)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        rows = await self.db.execute(stmt)
        users = list(rows.scalars().all())

        count_stmt = select(func.count()).select_from(UserAccount)
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total = (await self.db.execute(count_stmt)).scalar_one()

        return users, int(total)

    async def get_users_by_role(self, role: Role) -> List[UserAccount]:
        """Get all users with a specific role"""
        stmt = select(UserAccount).where(and_(UserAccount.role == role, UserAccount.is_active.is_(True)))
        rows = await self.db.execute(stmt)
        return list(rows.scalars().all())

    async def get_active_users_count(self) -> int:
        """Get count of active users"""
        stmt = select(func.count()).select_from(UserAccount).where(UserAccount.is_active.is_(True))
        return int((await self.db.execute(stmt)).scalar_one())

    async def get_users_count_by_role(self) -> dict[Role, int]:
        """Get count of users by role"""
        stmt = (
            select(UserAccount.role, func.count(UserAccount.id))
            .where(UserAccount.is_active.is_(True))
            .group_by(UserAccount.role)
        )
        rows = await self.db.execute(stmt)
        return {role: count for role, count in rows.all()}
