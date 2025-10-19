from __future__ import annotations

import httpx
from fastapi import HTTPException, status

from ..config import settings


class CatalogLookupService:
    """Service for looking up catalog items by SKU or barcode."""
    
    def __init__(self):
        self.task_service_url = settings.task_service_internal_url
        self.service_token = settings.service_token
    
    async def lookup(self, search: str) -> dict:
        """
        Lookup a catalog item by SKU or barcode.
        Calls the task service internal lookup endpoint.
        """
        if not search or not search.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search term is required"
            )
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.task_service_url}/internal/catalog/lookup",
                    params={"code": search.strip()},
                    headers={"Authorization": f"Bearer {self.service_token}"}
                )
                
                if response.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Item not found"
                    )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Lookup failed: {response.text}"
                    )
                
                return response.json()
                
            except httpx.TimeoutException:
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="Lookup service timeout"
                )
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Lookup service unavailable: {str(e)}"
                )
