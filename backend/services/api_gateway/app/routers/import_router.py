from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from ..dependencies import get_import_client
from ..services.auth import get_current_user, require_roles

router = APIRouter()


@router.get("/import/health")
async def import_health(
    client: httpx.AsyncClient = Depends(get_import_client),
) -> dict:
    """Health check for import service."""
    response = await client.get("/health")
    response.raise_for_status()
    return response.json()


@router.post("/import/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_import_file(
    file: UploadFile = File(...),
    user: dict = Depends(require_roles(["admin", "menadzer", "komercijalista", "sef"])),
    client: httpx.AsyncClient = Depends(get_import_client),
) -> dict:
    """Upload import file (ADMIN, MENADZER, KOMERCIJALISTA, and SEF)"""
    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is required"
        )

    allowed_extensions = {".csv", ".xlsx", ".xlsm", ".pdf"}
    file_extension = file.filename.lower().split(".")[-1] if "." in file.filename else ""
    if f".{file_extension}" not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Forward the file to the import service
    files = {"file": (file.filename, file.file, file.content_type)}
    
    response = await client.post(
        "/api/import/manual",
        files=files,
        headers={
            "X-User-Id": user.get("id"),
            "X-User-Role": user.get("role"),
        },
    )
    
    if response.status_code not in (200, 202):
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text
        )
    
    return response.json()
