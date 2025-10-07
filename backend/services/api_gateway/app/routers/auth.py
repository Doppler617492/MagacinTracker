from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from app_common.security import create_access_token

from ..schemas import TokenResponse, UserLoginRequest
from ..services.auth import authenticate_user, get_current_user

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
async def login(payload: UserLoginRequest) -> TokenResponse:
    user = await authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=user["id"], expires_delta=timedelta(minutes=60), role=user["role"])
    return TokenResponse(access_token=token)


@router.get("/auth/me")
async def me(current_user: dict = Depends(get_current_user)) -> dict:
    return current_user
