from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app_common.config import get_settings
from app_common.security import get_password_hash, verify_password

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

_FAKE_USERS = {
    "ana.komercijalista@example.com": {
        "id": "11111111-1111-1111-1111-111111111111",
        "email": "ana.komercijalista@example.com",
        "hashed_password": get_password_hash("Magacin123!"),
        "role": "komercijalista",
        "full_name": "Ana Komercijalista",
    },
    "marko.sef@example.com": {
        "id": "22222222-2222-2222-2222-222222222222",
        "email": "marko.sef@example.com",
        "hashed_password": get_password_hash("Magacin123!"),
        "role": "sef",
        "full_name": "Marko Šef",
    },
    "luka.magacioner@example.com": {
        "id": "33333333-3333-3333-3333-333333333333",
        "email": "luka.magacioner@example.com",
        "hashed_password": get_password_hash("Magacin123!"),
        "role": "magacioner",
        "full_name": "Luka Magacioner",
    },
    "vanja.menadzer@example.com": {
        "id": "66666666-6666-6666-6666-666666666666",
        "email": "vanja.menadzer@example.com",
        "hashed_password": get_password_hash("Magacin123!"),
        "role": "menadzer",
        "full_name": "Vanja Menadžer",
    },
}


def _verify_credentials(email: str, password: str) -> Optional[dict[str, Any]]:
    user = _FAKE_USERS.get(email)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


async def authenticate_user(email: str, password: str) -> Optional[dict[str, Any]]:
    return _verify_credentials(email, password)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        role = payload.get("role")
        if user_id is None:
            raise credentials_exception
    except JWTError as exc:  # noqa: BLE001
        raise credentials_exception from exc

    for user in _FAKE_USERS.values():
        if user["id"] == user_id:
            resolved_role = role or user["role"]
            return {
                "id": user_id,
                "email": user["email"],
                "role": resolved_role,
                "roles": [resolved_role],
            }
    raise credentials_exception
