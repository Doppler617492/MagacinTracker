from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..dependencies.http import get_task_service_client
from ..schemas import TokenResponse, UserLoginRequest
from ..schemas.auth import LoginResponse, UserProfile, DeviceTokenRequest
from ..services.auth import get_current_user, require_roles
from app_common.security import create_access_token
from app_common.logging import get_logger
from datetime import datetime, timezone

router = APIRouter()
logger = get_logger(__name__)

# Lightweight in-memory device token issue registry (best-effort; non-persistent)
_issued_device_tokens: list[dict] = []
_MAX_DEVICE_HISTORY = 200
_device_rate_limit: dict[str, list[float]] = {}


@router.post("/auth/login", response_model=LoginResponse)
async def login(
    payload: UserLoginRequest,
    request: Request,
    task_client = Depends(get_task_service_client)
) -> LoginResponse:
    """Login endpoint - delegates to task service"""
    try:
        response = await task_client.post(
            "/api/auth/login",
            json={
                "email": payload.username,  # username is actually email
                "password": payload.password
            }
        )
        response.raise_for_status()
        data = response.json()
        # Validate and return unified login response including user if present
        logger.info("gateway.auth.login.success", email=str(payload.username))
        return LoginResponse(
            access_token=data.get("access_token"),
            token_type=data.get("token_type", "bearer"),
            expires_in=data.get("expires_in"),
            user=(UserProfile(**data["user"]) if data.get("user") else None),
        )
    except Exception as e:
        logger.warning("gateway.auth.login.failed", email=str(payload.username))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


@router.post("/auth/device-token", response_model=LoginResponse)
async def device_token(payload: DeviceTokenRequest) -> LoginResponse:
    """Issue a short-lived token for device clients (e.g., TV dashboards).

    Validates device_secret against service config and returns a token with a
    read-only role (MENADZER) suitable for KPI/TV endpoints.
    """
    from ..config import settings

    expected_secret = settings.device_secret or settings.service_token
    if payload.device_secret != expected_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid device secret")

    # Optional allowlist check
    if settings.device_allowlist:
        if payload.device_id not in settings.device_allowlist:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device not allowed")

    # Simple in-memory rate limiting per device_id (per minute)
    now_ts = datetime.now(timezone.utc).timestamp()
    bucket = _device_rate_limit.setdefault(payload.device_id, [])
    # drop entries older than 60 seconds
    cutoff = now_ts - 60
    bucket = [ts for ts in bucket if ts >= cutoff]
    if len(bucket) >= settings.device_token_rate_limit_per_min:
        logger.warning("gateway.auth.device_token.rate_limited", device_id=payload.device_id)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
    bucket.append(now_ts)
    _device_rate_limit[payload.device_id] = bucket

    token = create_access_token(subject=payload.device_id, role="MENADZER")
    # record issuance (best effort)
    try:
        _issued_device_tokens.append({
            "device_id": payload.device_id,
            "issued_at": datetime.now(timezone.utc).isoformat(),
        })
        if len(_issued_device_tokens) > _MAX_DEVICE_HISTORY:
            del _issued_device_tokens[: len(_issued_device_tokens) - _MAX_DEVICE_HISTORY]
    except Exception:
        pass
    logger.info("gateway.auth.device_token.issued", device_id=payload.device_id)
    return LoginResponse(access_token=token, token_type="bearer", expires_in=8 * 60 * 60, user=None)


@router.get("/auth/devices/status")
async def devices_status(
    _: dict = Depends(require_roles(["ADMIN", "MENADZER"]))
):
    """Return recent device token issuance events (in-memory)."""
    return {
        "count": len(_issued_device_tokens),
        "items": list(_issued_device_tokens),
    }


@router.get("/auth/me")
async def me(current_user: dict = Depends(get_current_user)) -> dict:
    """Get current user profile"""
    return current_user


@router.post("/auth/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
    task_client = Depends(get_task_service_client)
) -> dict:
    """Logout endpoint - delegates to task service"""
    try:
        response = await task_client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {current_user.get('token', '')}"}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        # Even if task service fails, we can still return success
        return {"message": "Logged out successfully"}
