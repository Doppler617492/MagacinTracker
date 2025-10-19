from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app_common.config import get_settings
from app_common.db import get_db

from ..schemas import TvSnapshot
from ..services.tv import build_tv_snapshot

settings = get_settings()
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_device_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Get device user from JWT token - for TV dashboard access"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        device_id: str = payload.get("sub")
        role: str = payload.get("role")
        if device_id is None:
            raise credentials_exception
    except JWTError as exc:  # noqa: BLE001
        raise credentials_exception from exc
    
    # For device tokens, we don't need to look up in database
    # Just validate the role is appropriate for TV access
    if role not in ["MENADZER", "ADMIN", "SEF"]:
        raise credentials_exception
    
    return {
        "id": device_id,
        "role": role,
        "device_id": device_id,
    }


@router.get("/tv/snapshot", response_model=TvSnapshot)
async def tv_snapshot(
    current_user: dict = Depends(get_device_user),
    db=Depends(get_db),
) -> TvSnapshot:
    """Get TV dashboard snapshot - accessible by authenticated devices and users"""
    return await build_tv_snapshot(db)
