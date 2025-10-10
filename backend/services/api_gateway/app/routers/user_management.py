from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from typing import Optional
import httpx

from ..dependencies.http import get_task_service_client
from ..services.auth import require_role

router = APIRouter()


@router.get("/admin/users")
async def list_users(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    role_filter: Optional[str] = Query(None),
    active_filter: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    current_user: dict = Depends(require_role("menadzer")),  # Using menadzer as admin
    task_client = Depends(get_task_service_client)
):
    """List all users (ADMIN only)"""
    try:
        params = {
            "page": page,
            "per_page": per_page
        }
        if role_filter:
            params["role_filter"] = role_filter
        if active_filter is not None:
            params["active_filter"] = active_filter
        if search:
            params["search"] = search
            
        # Forward the Authorization header from the original request
        auth_header = request.headers.get("Authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
            
        response = await task_client.get("/api/admin/users", params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )


@router.post("/admin/users")
async def create_user(
    request: Request,
    user_data: dict,
    current_user: dict = Depends(require_role("menadzer")),  # Using menadzer as admin
    task_client = Depends(get_task_service_client)
):
    """Create a new user (ADMIN only)"""
    try:
        auth_header = request.headers.get("Authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        response = await task_client.post("/api/admin/users", json=user_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get("/admin/users/{user_id}")
async def get_user(
    user_id: str,
    current_user: dict = Depends(require_role("menadzer")),  # Using menadzer as admin
    task_client = Depends(get_task_service_client)
):
    """Get user by ID (ADMIN only)"""
    try:
        response = await task_client.get(f"/api/admin/users/{user_id}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.patch("/admin/users/{user_id}")
async def update_user(
    request: Request,
    user_id: str,
    user_data: dict,
    current_user: dict = Depends(require_role("menadzer")),  # Using menadzer as admin
    task_client = Depends(get_task_service_client)
):
    """Update user (ADMIN only)"""
    try:
        # Forward the Authorization header
        auth_header = request.headers.get("Authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
            
        response = await task_client.patch(f"/api/admin/users/{user_id}", json=user_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.delete("/admin/users/{user_id}")
async def deactivate_user(
    request: Request,
    user_id: str,
    current_user: dict = Depends(require_role("menadzer")),  # Using menadzer as admin
    task_client = Depends(get_task_service_client)
):
    """Deactivate user (ADMIN only)"""
    try:
        # Forward the Authorization header from the original request
        auth_header = request.headers.get("Authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
            
        response = await task_client.delete(f"/api/admin/users/{user_id}", headers=headers)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        # Convert httpx status error to HTTPException with original status code
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        elif e.response.status_code == 400:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.response.text or "Bad request"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate user"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )


@router.post("/admin/users/{user_id}/reset-password")
async def reset_user_password(
    request: Request,
    user_id: str,
    password_data: dict,
    current_user: dict = Depends(require_role("menadzer")),  # Using menadzer as admin
    task_client = Depends(get_task_service_client)
):
    """Reset user password (ADMIN only)"""
    try:
        # Forward the Authorization header
        auth_header = request.headers.get("Authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
            
        response = await task_client.post(
            f"/api/admin/users/{user_id}/reset-password",
            json=password_data,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )


@router.get("/admin/users/stats")
async def get_user_stats(
    current_user: dict = Depends(require_role("menadzer")),  # Using menadzer as admin
    task_client = Depends(get_task_service_client)
):
    """Get user statistics (ADMIN only)"""
    try:
        response = await task_client.get("/api/admin/users/stats")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user statistics"
        )
