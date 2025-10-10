from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app_common.db import get_db
from ..services.metrics_service import MetricsService
from .auth_test import require_role
from ..models.enums import Role

router = APIRouter()


@router.get("/metrics/auth")
async def get_auth_metrics(
    db: Session = Depends(get_db),
    _ = Depends(require_role(Role.ADMIN))
):
    """Get authentication metrics (ADMIN only)"""
    metrics_service = MetricsService(db)
    return metrics_service.get_auth_metrics()


@router.get("/metrics/user-activity")
async def get_user_activity_metrics(
    db: Session = Depends(get_db),
    _ = Depends(require_role(Role.ADMIN))
):
    """Get user activity metrics (ADMIN only)"""
    metrics_service = MetricsService(db)
    return metrics_service.get_user_activity_metrics()


@router.get("/metrics/security")
async def get_security_metrics(
    db: Session = Depends(get_db),
    _ = Depends(require_role(Role.ADMIN))
):
    """Get security metrics (ADMIN only)"""
    metrics_service = MetricsService(db)
    return metrics_service.get_security_metrics()


@router.get("/metrics/all")
async def get_all_metrics(
    db: Session = Depends(get_db),
    _ = Depends(require_role(Role.ADMIN))
):
    """Get all metrics (ADMIN only)"""
    metrics_service = MetricsService(db)
    return metrics_service.get_all_metrics()
