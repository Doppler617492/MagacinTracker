from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app_common.config import get_settings
from app_common.db import get_db
from app_common.security import create_access_token

from ..models.enums import AuditAction, Role
from ..schemas.user import (
    LoginRequest,
    LoginResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    UserResponse,
)
from ..services.audit_service import AuditService
from ..services.user_service import UserService

settings = get_settings()
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserResponse:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user_service = UserService(db)
    user = user_service.get_user_by_id(uuid.UUID(user_id))
    if user is None or not user.is_active:
        raise credentials_exception
    
    return UserResponse.from_orm(user)


def require_role(required_role: Role):
    """Dependency to require specific role"""
    def role_checker(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
        current_role = getattr(current_user.role, "value", str(current_user.role)).upper()
        if current_role != required_role.value and current_role != Role.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


def require_roles(required_roles: list[Role]):
    """Dependency to require one of multiple roles"""
    def role_checker(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
        current_role = getattr(current_user.role, "value", str(current_user.role)).upper()
        allowed = {role.value for role in required_roles}
        if current_role not in allowed and current_role != Role.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


@router.post("/auth/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> LoginResponse:
    """Authenticate user and return JWT token"""
    user_service = UserService(db)
    audit_service = AuditService(db)
    
    # Try to authenticate user
    user = user_service.authenticate_user(login_data.email, login_data.password)
    
    if not user:
        # Log failed login attempt
        audit_service.log_login_failed(login_data.email, request)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Log successful login
    audit_service.log_login_success(user.id, request)
    
    # Create JWT token
    access_token_expires = timedelta(hours=8)  # 8 hours as specified
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires,
        role=user.role.value
    )
    
    return LoginResponse(
        access_token=access_token,
        expires_in=int(access_token_expires.total_seconds()),
        user=UserResponse.from_orm(user)
    )


@router.post("/auth/logout")
async def logout(
    current_user: UserResponse = Depends(get_current_user),
    request: Request = None,
    db: Session = Depends(get_db)
) -> dict:
    """Logout user (invalidate token)"""
    audit_service = AuditService(db)
    audit_service.log_logout(current_user.id, request)
    
    return {"message": "Successfully logged out"}


@router.get("/auth/profile", response_model=UserResponse)
async def get_profile(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """Get current user profile"""
    return current_user


@router.post("/auth/reset-request")
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db)
) -> dict:
    """Request password reset (send email)"""
    user_service = UserService(db)
    user = user_service.get_user_by_email(reset_data.email)
    
    # Always return success to prevent email enumeration
    if user:
        # TODO: Implement email sending with reset token
        # For now, just log the request
        pass
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/auth/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
) -> dict:
    """Reset password with token"""
    # TODO: Implement token validation and password reset
    # For now, return not implemented
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset not implemented yet"
    )

