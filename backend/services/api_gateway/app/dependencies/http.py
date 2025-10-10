from __future__ import annotations

import httpx
from fastapi import Request

from ..config import settings


def create_http_clients() -> dict[str, httpx.AsyncClient]:
    return {
        "task": httpx.AsyncClient(base_url=settings.task_service_url, timeout=30.0),
        "catalog": httpx.AsyncClient(base_url=settings.catalog_service_url, timeout=30.0),
        "import": httpx.AsyncClient(base_url=settings.import_service_url, timeout=60.0),
    }


def get_task_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_clients["task"]


def get_task_service_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_clients["task"]


def get_catalog_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_clients["catalog"]


def get_import_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_clients["import"]


def build_forward_headers(request: Request, user: dict) -> dict[str, str]:
    headers = {}
    
    # Forward JWT token if present
    auth_header = request.headers.get("Authorization")
    if auth_header:
        headers["Authorization"] = auth_header
    
    # Also forward user context headers for compatibility
    roles = user.get("roles") or user.get("role")
    if isinstance(roles, str):
        role_header = roles
    elif isinstance(roles, (list, tuple, set)):
        role_header = ",".join(str(role) for role in roles)
    else:
        role_header = ""

    headers.update({
        "X-User-Id": str(user.get("id")),
        "X-User-Roles": role_header,
    })
    
    correlation_id = request.headers.get("X-Correlation-ID")
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    return headers
