from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app_common.db import get_db

from ..dependencies import require_roles, require_service_token
from ..models.enums import Role
from ..schemas import (
    CatalogArticleListResponse,
    CatalogArticleResponse,
    CatalogArticleUpdate,
    CatalogLookupResponse,
    CatalogUpsertRequest,
    CatalogUpsertResponse,
)
from ..services.catalog import CatalogService

router = APIRouter()


@router.post(
    "/internal/catalog/upsert-batch",
    response_model=CatalogUpsertResponse,
    status_code=status.HTTP_200_OK,
)
async def upsert_catalog_batch(
    request: CatalogUpsertRequest,
    service_token: None = Depends(require_service_token),
    db=Depends(get_db),
) -> CatalogUpsertResponse:
    service = CatalogService(db)
    response, cached = await service.upsert_batch(request, executed_by=None)
    if cached:
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=response.model_dump(),
            headers={"X-Cached": "true"},
        )
    return response


@router.get("/internal/catalog/lookup", response_model=CatalogLookupResponse)
async def lookup_catalog_item(
    sifra: str = Query(..., min_length=1),
    service_token: None = Depends(require_service_token),
    db=Depends(get_db),
) -> CatalogLookupResponse:
    service = CatalogService(db)
    return await service.lookup(sifra)


@router.get("/api/catalog/articles", response_model=CatalogArticleListResponse)
async def list_catalog_articles(
    user=Depends(require_roles(Role.menadzer, Role.sef, Role.komercijalista)),
    db=Depends(get_db),
    search: Optional[str] = Query(default=None, min_length=1),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=25, ge=1, le=100),
) -> CatalogArticleListResponse:
    service = CatalogService(db)
    articles, total = await service.list_articles(search, page, size)
    return CatalogArticleListResponse(
        items=articles,
        total=total,
        page=page,
        page_size=size,
    )


@router.patch("/api/catalog/articles/{article_id}", response_model=CatalogArticleResponse)
async def update_catalog_article(
    article_id: UUID,
    payload: CatalogArticleUpdate,
    user=Depends(require_roles(Role.menadzer, Role.sef)),
    db=Depends(get_db),
) -> CatalogArticleResponse:
    service = CatalogService(db)
    try:
        return await service.update_article(article_id, payload, actor_id=user.id)
    except ValueError as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
