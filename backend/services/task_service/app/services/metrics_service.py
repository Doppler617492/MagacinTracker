from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from ..models.audit import AuditLog
from ..models.enums import AuditAction, Role
from ..models.user import UserAccount


class MetricsService:
    def __init__(self, db: Session):
        self.db = db

    def get_auth_metrics(self) -> Dict[str, Any]:
        """Get authentication-related metrics"""
        # Login success/failure counts
        login_success_count = self.db.query(AuditLog).filter(
            AuditLog.action == AuditAction.LOGIN_SUCCESS
        ).count()
        
        login_failed_count = self.db.query(AuditLog).filter(
            AuditLog.action == AuditAction.LOGIN_FAILED
        ).count()
        
        # Active users count
        active_users_count = self.db.query(UserAccount).filter(
            UserAccount.is_active == True
        ).count()
        
        # Role distribution
        role_distribution = self.db.query(
            UserAccount.role,
            func.count(UserAccount.id)
        ).filter(
            UserAccount.is_active == True
        ).group_by(UserAccount.role).all()
        
        role_counts = {role.value: count for role, count in role_distribution}
        
        # Recent login activity (last 24 hours)
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        
        recent_logins = self.db.query(AuditLog).filter(
            and_(
                AuditLog.action == AuditAction.LOGIN_SUCCESS,
                AuditLog.created_at >= yesterday
            )
        ).count()
        
        return {
            "auth_login_success_total": login_success_count,
            "auth_login_failed_total": login_failed_count,
            "active_users_total": active_users_count,
            "role_distribution_total": role_counts,
            "recent_logins_24h": recent_logins,
        }

    def get_user_activity_metrics(self) -> Dict[str, Any]:
        """Get user activity metrics"""
        # Users with recent activity (last 7 days)
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        
        recent_activity_users = self.db.query(
            func.count(func.distinct(AuditLog.user_id))
        ).filter(
            and_(
                AuditLog.user_id.isnot(None),
                AuditLog.created_at >= week_ago
            )
        ).scalar() or 0
        
        # Most active users (by audit log count)
        most_active_users = self.db.query(
            AuditLog.user_id,
            func.count(AuditLog.id).label('activity_count')
        ).filter(
            AuditLog.user_id.isnot(None)
        ).group_by(
            AuditLog.user_id
        ).order_by(
            func.count(AuditLog.id).desc()
        ).limit(10).all()
        
        # Get user details for most active users
        user_activity = []
        for user_id, activity_count in most_active_users:
            user = self.db.query(UserAccount).filter(UserAccount.id == user_id).first()
            if user:
                user_activity.append({
                    "user_id": str(user_id),
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role.value,
                    "activity_count": activity_count
                })
        
        return {
            "recent_activity_users_7d": recent_activity_users,
            "most_active_users": user_activity,
        }

    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security-related metrics"""
        # Failed login attempts in last hour
        hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        recent_failed_logins = self.db.query(AuditLog).filter(
            and_(
                AuditLog.action == AuditAction.LOGIN_FAILED,
                AuditLog.created_at >= hour_ago
            )
        ).count()
        
        # Password resets in last 24 hours
        day_ago = datetime.now(timezone.utc) - timedelta(days=1)
        recent_password_resets = self.db.query(AuditLog).filter(
            and_(
                AuditLog.action == AuditAction.PASSWORD_RESET,
                AuditLog.created_at >= day_ago
            )
        ).count()
        
        # User deactivations in last 30 days
        month_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_deactivations = self.db.query(AuditLog).filter(
            and_(
                AuditLog.action == AuditAction.USER_DEACTIVATED,
                AuditLog.created_at >= month_ago
            )
        ).count()
        
        return {
            "failed_logins_last_hour": recent_failed_logins,
            "password_resets_last_24h": recent_password_resets,
            "user_deactivations_last_30d": recent_deactivations,
        }

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics combined"""
        return {
            "auth": self.get_auth_metrics(),
            "user_activity": self.get_user_activity_metrics(),
            "security": self.get_security_metrics(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
