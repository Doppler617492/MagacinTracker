from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..dependencies.http import get_task_service_client
from ..schemas import TokenResponse, UserLoginRequest
from ..services.auth import get_current_user

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    payload: UserLoginRequest,
    request: Request,
    task_client = Depends(get_task_service_client)
) -> TokenResponse:
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
        login_data = response.json()
        return TokenResponse(
            access_token=login_data["access_token"],
            token_type=login_data.get("token_type", "bearer")
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


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
