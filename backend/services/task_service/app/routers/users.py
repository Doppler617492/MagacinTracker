from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app_common.db import get_db

from ..models.enums import Role
from ..schemas.user import (
    UserCreate,
    UserListResponse,
    UserPasswordReset,
    UserResponse,
    UserUpdate,
)
from ..services.audit_service import AuditService
from ..services.user_service import UserService
from .auth_test import get_current_user, require_role

router = APIRouter()


@router.get("/admin/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    role_filter: Optional[Role] = Query(None),
    active_filter: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    current_user: UserResponse = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db)
) -> UserListResponse:
    """List all users with pagination and filters (ADMIN only)"""
    user_service = UserService(db)
    users, total = user_service.list_users(
        page=page,
        per_page=per_page,
        role_filter=role_filter,
        active_filter=active_filter,
        search=search
    )
    
    return UserListResponse(
        users=[UserResponse.from_orm(user) for user in users],
        total=total,
        page=page,
        per_page=per_page
    )


@router.post("/admin/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: UserResponse = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db)
) -> UserResponse:
    """Create a new user (ADMIN only)"""
    user_service = UserService(db)
    audit_service = AuditService(db)
    
    try:
        user = user_service.create_user(user_data, current_user.id)
        
        # Log user creation
        audit_service.log_user_created(
            created_by=current_user.id,
            new_user_id=user.id,
            new_user_email=user.email,
            new_user_role=user.role.value
        )
        
        return UserResponse.from_orm(user)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/admin/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    current_user: UserResponse = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db)
) -> UserResponse:
    """Get user by ID (ADMIN only)"""
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)


@router.patch("/admin/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    current_user: UserResponse = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db)
) -> UserResponse:
    """Update user information (ADMIN only)"""
    user_service = UserService(db)
    audit_service = AuditService(db)
    
    # Get current user data for audit logging
    existing_user = user_service.get_user_by_id(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update user
    updated_user = user_service.update_user(user_id, user_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Log role change if role was updated
    if user_data.role is not None and user_data.role != existing_user.role:
        audit_service.log_user_role_changed(
            changed_by=current_user.id,
            target_user_id=user_id,
            old_role=existing_user.role.value,
            new_role=user_data.role.value
        )
    
    return UserResponse.from_orm(updated_user)


@router.delete("/admin/users/{user_id}")
async def deactivate_user(
    user_id: uuid.UUID,
    current_user: UserResponse = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db)
) -> dict:
    """Deactivate user (soft delete) (ADMIN only)"""
    user_service = UserService(db)
    audit_service = AuditService(db)
    
    # Get user for audit logging
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-deactivation
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    # Deactivate user
    deactivated_user = user_service.deactivate_user(user_id)
    if not deactivated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Log deactivation
    audit_service.log_user_deactivated(
        deactivated_by=current_user.id,
        target_user_id=user_id,
        target_user_email=user.email
    )
    
    return {"message": "User deactivated successfully"}


@router.post("/admin/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: uuid.UUID,
    password_data: UserPasswordReset,
    current_user: UserResponse = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db)
) -> dict:
    """Reset user password (ADMIN only)"""
    user_service = UserService(db)
    audit_service = AuditService(db)
    
    # Reset password
    user = user_service.reset_user_password(user_id, password_data.new_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Log password reset
    audit_service.log_password_reset(user_id)
    
    return {"message": "Password reset successfully"}


@router.get("/admin/users/stats")
async def get_user_stats(
    current_user: UserResponse = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db)
) -> dict:
    """Get user statistics (ADMIN only)"""
    user_service = UserService(db)
    
    active_users_count = user_service.get_active_users_count()
    users_by_role = user_service.get_users_count_by_role()
    
    return {
        "active_users_total": active_users_count,
        "role_distribution": users_by_role
    }
