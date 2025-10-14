from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_common.db import get_db
from app_common.security import get_password_hash
from .auth_test import get_current_user, require_role

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: str
    is_active: Optional[bool] = True  # Optional field, defaults to True


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class PasswordReset(BaseModel):
    new_password: str


@router.get("/admin/users")
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    role_filter: Optional[str] = Query(None),
    active_filter: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    current_user: dict = Depends(require_role("menadzer")),  # Using menadzer as admin
    db: AsyncSession = Depends(get_db)
):
    """List all users with pagination and filters (ADMIN only)"""
    
    # Build query
    where_conditions = []
    params = {}
    
    if role_filter:
        where_conditions.append("role = :role_filter")
        params["role_filter"] = role_filter.upper()  # Convert to uppercase for DB enum
    
    if active_filter is not None:
        where_conditions.append("is_active = :active_filter")
        params["active_filter"] = active_filter
    
    if search:
        where_conditions.append("(LOWER(first_name) LIKE :search OR LOWER(last_name) LIKE :search OR LOWER(email) LIKE :search)")
        params["search"] = f"%{search.lower()}%"
    
    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
    
    # Get total count
    count_query = f"SELECT COUNT(*) FROM users WHERE {where_clause}"
    result = await db.execute(text(count_query), params)
    total = result.scalar()
    
    # Get users with pagination
    offset = (page - 1) * per_page
    users_query = f"""
        SELECT id, email, first_name, last_name, role, is_active, created_at, updated_at, last_login, created_by
        FROM users 
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """
    params.update({"limit": per_page, "offset": offset})
    
    result = await db.execute(text(users_query), params)
    users = result.fetchall()
    
    # Format response
    user_list = []
    for user in users:
        user_list.append({
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "created_by": str(user.created_by) if user.created_by else None,
            "full_name": f"{user.first_name} {user.last_name}"
        })
    
    return {
        "users": user_list,
        "total": total,
        "page": page,
        "per_page": per_page
    }


@router.post("/admin/users")
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(require_role("menadzer")),  # Using menadzer as admin
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (ADMIN only)"""
    
    # Check if user with this email already exists
    result = await db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": user_data.email}
    )
    existing_user = result.fetchone()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Validate role (accept both uppercase and lowercase, convert to uppercase for DB enum)
    role_lower = user_data.role.lower()
    valid_roles = ["magacioner", "sef", "komercijalista", "menadzer", "admin"]
    if role_lower not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )
    
    # Convert to uppercase for database enum
    role_upper = user_data.role.upper()
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create new user
    user_id = uuid.uuid4()
    created_by = uuid.UUID(current_user["id"])
    now = datetime.utcnow()
    is_active = user_data.is_active  # Use the value from input
    
    await db.execute(
        text("""
            INSERT INTO users (id, email, password_hash, first_name, last_name, role, is_active, created_at, updated_at, created_by)
            VALUES (:id, :email, :password_hash, :first_name, :last_name, :role, :is_active, :created_at, :updated_at, :created_by)
        """),
        {
            "id": user_id,
            "email": user_data.email,
            "password_hash": hashed_password,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "role": role_upper,  # Use uppercase role for DB enum
            "is_active": is_active,
            "created_at": now,
            "updated_at": now,
            "created_by": created_by
        }
    )
    await db.commit()
    
    return {
        "id": str(user_id),
        "email": user_data.email,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "role": role_upper,  # Return uppercase role to match DB
        "is_active": is_active,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "created_by": str(created_by),
        "full_name": f"{user_data.first_name} {user_data.last_name}"
    }


@router.get("/admin/users/stats")
async def get_user_stats(
    current_user: dict = Depends(require_role("menadzer")),  # Using menadzer as admin
    db: AsyncSession = Depends(get_db)
):
    """Get user statistics (ADMIN only)"""
    
    # Get active users count
    result = await db.execute(text("SELECT COUNT(*) FROM users WHERE is_active = true"))
    active_users_count = result.scalar()
    
    # Get role distribution
    result = await db.execute(text("SELECT role, COUNT(*) FROM users WHERE is_active = true GROUP BY role"))
    role_distribution = {row.role: row.count for row in result.fetchall()}
    
    return {
        "active_users_total": active_users_count,
        "role_distribution": role_distribution
    }


@router.patch("/admin/users/{user_id}")
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: dict = Depends(require_role("menadzer")),
    db: AsyncSession = Depends(get_db)
):
    """Update user information (ADMIN only)"""
    
    # Validate UUID
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    # Check if user exists
    result = await db.execute(
        text("SELECT id, email FROM users WHERE id = :user_id"),
        {"user_id": user_uuid}
    )
    user = result.fetchone()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Build update query dynamically
    update_fields = []
    params = {"user_id": user_uuid}
    
    if user_data.first_name is not None:
        update_fields.append("first_name = :first_name")
        params["first_name"] = user_data.first_name
    
    if user_data.last_name is not None:
        update_fields.append("last_name = :last_name")
        params["last_name"] = user_data.last_name
    
    if user_data.role is not None:
        role_lower = user_data.role.lower()
        valid_roles = ["magacioner", "sef", "komercijalista", "menadzer", "admin"]
        if role_lower not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        update_fields.append("role = :role")
        params["role"] = role_lower
    
    if user_data.is_active is not None:
        update_fields.append("is_active = :is_active")
        params["is_active"] = user_data.is_active
    
    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    update_fields.append("updated_at = NOW()")
    
    # Execute update
    update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = :user_id"
    await db.execute(text(update_query), params)
    await db.commit()
    
    # Fetch updated user
    result = await db.execute(
        text("SELECT id, email, first_name, last_name, role, is_active, created_at, updated_at FROM users WHERE id = :user_id"),
        {"user_id": user_uuid}
    )
    updated_user = result.fetchone()
    
    return {
        "id": str(updated_user.id),
        "email": updated_user.email,
        "first_name": updated_user.first_name,
        "last_name": updated_user.last_name,
        "role": updated_user.role,
        "is_active": updated_user.is_active,
        "created_at": updated_user.created_at.isoformat() if updated_user.created_at else None,
        "updated_at": updated_user.updated_at.isoformat() if updated_user.updated_at else None,
        "full_name": f"{updated_user.first_name} {updated_user.last_name}"
    }


@router.post("/admin/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    password_data: PasswordReset,
    current_user: dict = Depends(require_role("menadzer")),
    db: AsyncSession = Depends(get_db)
):
    """Reset user password (ADMIN only)"""
    
    # Validate UUID
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    # Check if user exists
    result = await db.execute(
        text("SELECT id, email FROM users WHERE id = :user_id"),
        {"user_id": user_uuid}
    )
    user = result.fetchone()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Hash new password
    hashed_password = get_password_hash(password_data.new_password)
    
    # Update password
    await db.execute(
        text("UPDATE users SET password_hash = :password_hash, updated_at = NOW() WHERE id = :user_id"),
        {"password_hash": hashed_password, "user_id": user_uuid}
    )
    await db.commit()
    
    return {"message": "Password reset successfully", "user_id": str(user_uuid)}


@router.delete("/admin/users/{user_id}")
async def deactivate_user(
    user_id: str,
    current_user: dict = Depends(require_role("menadzer")),  # Using menadzer as admin
    db: AsyncSession = Depends(get_db)
):
    """Deactivate user (soft delete) (ADMIN only)"""
    
    # Validate UUID
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    # Check if user exists
    result = await db.execute(
        text("SELECT id, email, is_active FROM users WHERE id = :user_id"),
        {"user_id": user_uuid}
    )
    user = result.fetchone()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-deactivation
    if str(user_uuid) == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    # Deactivate user (soft delete)
    await db.execute(
        text("UPDATE users SET is_active = false, updated_at = NOW() WHERE id = :user_id"),
        {"user_id": user_uuid}
    )
    await db.commit()
    
    return {"message": "User deactivated successfully", "user_id": str(user_uuid)}
