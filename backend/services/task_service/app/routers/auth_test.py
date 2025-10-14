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
from app_common.security import create_access_token, verify_password

from ..schemas.user import (
    LoginRequest,
    LoginResponse,
    UserResponse,
)

settings = get_settings()
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(login_data.password, user_row.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
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


def require_role(required_role: str):
    """Dependency to require specific role"""
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = str(current_user.get("role", "")).upper()
        required_upper = str(required_role).upper()
        
        # ADMIN and MENADZER have full access
        admin_roles = ["ADMIN", "MENADZER"]
        
        if user_role not in admin_roles and user_role != required_upper:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> dict:
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
    
    return {
        "id": str(user_row.id),
        "email": user_row.email,
        "first_name": user_row.first_name,
        "last_name": user_row.last_name,
        "role": user_row.role,
        "is_active": user_row.is_active,
        "full_name": f"{user_row.first_name} {user_row.last_name}"
    }


@router.get("/auth/profile")
async def get_profile(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Get current user profile"""
    return current_user
