from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app_common.config import get_settings

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        role = payload.get("role")
        
        if user_id is None or role is None:
            raise credentials_exception
            
        return {
            "id": user_id,
            "role": role,
        }
        
    except JWTError as exc:  # noqa: BLE001
        raise credentials_exception from exc


def require_role(required_role: str):
    """Dependency to require specific role"""
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] != required_role and current_user["role"] != "menadzer":  # menadzer as admin
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


def require_roles(required_roles: list[str]):
    """Dependency to require one of multiple roles"""
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in required_roles and current_user["role"] != "menadzer":  # menadzer as admin
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


def require_authenticated():
    """Dependency to require any authenticated user"""
    return Depends(get_current_user)
