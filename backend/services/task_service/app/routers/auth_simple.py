from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_common.config import get_settings
from app_common.db import get_db
from app_common.security import create_access_token, get_password_hash, verify_password

from ..models.enums import AuditAction, Role
from ..schemas.user import (
    LoginRequest,
    LoginResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    UserResponse,
)

settings = get_settings()
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
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
    except JWTError as exc:  # noqa: BLE001
        raise credentials_exception from exc
    
    # Get user from database
    result = await db.execute(
        text("SELECT id, email, first_name, last_name, role, is_active FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    )
    user_row = result.fetchone()
    
    if user_row is None or not user_row.is_active:
        raise credentials_exception
    
    return UserResponse(
        id=user_row.id,
        email=user_row.email,
        first_name=user_row.first_name,
        last_name=user_row.last_name,
        role=user_row.role,
        is_active=user_row.is_active,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_login=None,
        created_by=None,
        full_name=f"{user_row.first_name} {user_row.last_name}"
    )


def require_role(required_role: Role):
    """Dependency to require specific role"""
    def role_checker(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
        if current_user.role != required_role.value and current_user.role != "menadzer":  # menadzer as admin for now
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


def require_roles(required_roles: list[Role]):
    """Dependency to require one of multiple roles"""
    def role_checker(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
        role_values = [role.value for role in required_roles]
        if current_user.role not in role_values and current_user.role != "menadzer":  # menadzer as admin for now
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
    db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """Authenticate user and return JWT token"""
    
    # Get user from database
    result = await db.execute(
        text("SELECT id, email, first_name, last_name, role, password_hash, is_active FROM users WHERE email = :email"),
        {"email": login_data.email.lower()}
    )
    user_row = result.fetchone()
    
    if not user_row or not user_row.is_active:
        # Log failed login attempt
        await db.execute(
            text("""
                INSERT INTO audit_log (action, entity_type, entity_id, payload, ip_address, user_agent)
                VALUES (:action, :entity_type, :entity_id, :payload, :ip_address, :user_agent)
            """),
            {
                "action": AuditAction.LOGIN_FAILED.value,
                "entity_type": "user",
                "entity_id": login_data.email,
                "payload": {"email": login_data.email, "timestamp": datetime.now(timezone.utc).isoformat()},
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("User-Agent")
            }
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(login_data.password, user_row.password_hash):
        # Log failed login attempt
        await db.execute(
            text("""
                INSERT INTO audit_log (action, entity_type, entity_id, payload, ip_address, user_agent)
                VALUES (:action, :entity_type, :entity_id, :payload, :ip_address, :user_agent)
            """),
            {
                "action": AuditAction.LOGIN_FAILED.value,
                "entity_type": "user",
                "entity_id": login_data.email,
                "payload": {"email": login_data.email, "timestamp": datetime.now(timezone.utc).isoformat()},
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("User-Agent")
            }
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Log successful login
    await db.execute(
        text("""
            INSERT INTO audit_log (user_id, action, payload, ip_address, user_agent)
            VALUES (:user_id, :action, :payload, :ip_address, :user_agent)
        """),
        {
            "user_id": user_row.id,
            "action": AuditAction.LOGIN_SUCCESS.value,
            "payload": {"timestamp": datetime.now(timezone.utc).isoformat()},
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent")
        }
    )
    
    # Update last login
    await db.execute(
        text("UPDATE users SET last_login = :last_login WHERE id = :user_id"),
        {"last_login": datetime.now(timezone.utc), "user_id": user_row.id}
    )
    
    await db.commit()
    
    # Create JWT token
    access_token_expires = timedelta(hours=8)  # 8 hours as specified
    access_token = create_access_token(
        subject=str(user_row.id),
        expires_delta=access_token_expires,
        role=user_row.role
    )
    
    return LoginResponse(
        access_token=access_token,
        expires_in=int(access_token_expires.total_seconds()),
        user=UserResponse(
            id=user_row.id,
            email=user_row.email,
            first_name=user_row.first_name,
            last_name=user_row.last_name,
            role=user_row.role,
            is_active=user_row.is_active,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc),
            created_by=None,
            full_name=f"{user_row.first_name} {user_row.last_name}"
        )
    )


@router.post("/auth/logout")
async def logout(
    current_user: UserResponse = Depends(get_current_user),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Logout user (invalidate token)"""
    await db.execute(
        text("""
            INSERT INTO audit_log (user_id, action, payload, ip_address, user_agent)
            VALUES (:user_id, :action, :payload, :ip_address, :user_agent)
        """),
        {
            "user_id": current_user.id,
            "action": AuditAction.LOGOUT.value,
            "payload": {"timestamp": datetime.now(timezone.utc).isoformat()},
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent")
        }
    )
    await db.commit()
    
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
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Request password reset (send email)"""
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/auth/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Reset password with token"""
    # TODO: Implement token validation and password reset
    # For now, return not implemented
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset not implemented yet"
    )
