from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Request
from sqlalchemy.orm import Session

from ..models.audit import AuditLog
from ..models.enums import AuditAction


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log_action(
        self,
        action: AuditAction,
        user_id: Optional[uuid.UUID] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        payload: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log an audit action"""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        
        return audit_log

    def log_login_success(
        self,
        user_id: uuid.UUID,
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log successful login"""
        return self.log_action(
            action=AuditAction.LOGIN_SUCCESS,
            user_id=user_id,
            payload={"timestamp": datetime.now(timezone.utc).isoformat()},
            ip_address=self._get_client_ip(request) if request else None,
            user_agent=self._get_user_agent(request) if request else None
        )

    def log_login_failed(
        self,
        email: str,
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log failed login attempt"""
        return self.log_action(
            action=AuditAction.LOGIN_FAILED,
            entity_type="user",
            entity_id=email,
            payload={
                "email": email,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            ip_address=self._get_client_ip(request) if request else None,
            user_agent=self._get_user_agent(request) if request else None
        )

    def log_logout(
        self,
        user_id: uuid.UUID,
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log user logout"""
        return self.log_action(
            action=AuditAction.LOGOUT,
            user_id=user_id,
            payload={"timestamp": datetime.now(timezone.utc).isoformat()},
            ip_address=self._get_client_ip(request) if request else None,
            user_agent=self._get_user_agent(request) if request else None
        )

    def log_user_created(
        self,
        created_by: uuid.UUID,
        new_user_id: uuid.UUID,
        new_user_email: str,
        new_user_role: str
    ) -> AuditLog:
        """Log user creation"""
        return self.log_action(
            action=AuditAction.USER_CREATED,
            user_id=created_by,
            entity_type="user",
            entity_id=str(new_user_id),
            payload={
                "new_user_id": str(new_user_id),
                "new_user_email": new_user_email,
                "new_user_role": new_user_role,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    def log_user_role_changed(
        self,
        changed_by: uuid.UUID,
        target_user_id: uuid.UUID,
        old_role: str,
        new_role: str
    ) -> AuditLog:
        """Log user role change"""
        return self.log_action(
            action=AuditAction.USER_ROLE_CHANGED,
            user_id=changed_by,
            entity_type="user",
            entity_id=str(target_user_id),
            payload={
                "target_user_id": str(target_user_id),
                "old_role": old_role,
                "new_role": new_role,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    def log_user_deactivated(
        self,
        deactivated_by: uuid.UUID,
        target_user_id: uuid.UUID,
        target_user_email: str
    ) -> AuditLog:
        """Log user deactivation"""
        return self.log_action(
            action=AuditAction.USER_DEACTIVATED,
            user_id=deactivated_by,
            entity_type="user",
            entity_id=str(target_user_id),
            payload={
                "target_user_id": str(target_user_id),
                "target_user_email": target_user_email,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    def log_password_reset(
        self,
        user_id: uuid.UUID,
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log password reset"""
        return self.log_action(
            action=AuditAction.PASSWORD_RESET,
            user_id=user_id,
            payload={"timestamp": datetime.now(timezone.utc).isoformat()},
            ip_address=self._get_client_ip(request) if request else None,
            user_agent=self._get_user_agent(request) if request else None
        )

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP address from request"""
        if not request:
            return None
        
        # Check for forwarded headers first (for load balancers/proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        return request.client.host if request.client else None

    def _get_user_agent(self, request: Request) -> Optional[str]:
        """Extract user agent from request"""
        if not request:
            return None
        return request.headers.get("User-Agent")
