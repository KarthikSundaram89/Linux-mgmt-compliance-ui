"""
Audit Log Repository
====================

Data access layer for AuditLog model operations.
Audit logs are append-only and should never be modified or deleted.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.audit_log import AuditLog
from backend.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for AuditLog operations (append-only)."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(AuditLog, session)
    
    async def get_by_user(
        self, user_id: str, limit: int = 100
    ) -> List[AuditLog]:
        """Get audit entries for a specific user."""
        result = await self._session.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_action(
        self, action: str, limit: int = 100
    ) -> List[AuditLog]:
        """Get audit entries by action type."""
        result = await self._session.execute(
            select(AuditLog)
            .where(AuditLog.action == action)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_recent(
        self, hours: int = 24, limit: int = 200
    ) -> List[AuditLog]:
        """Get recent audit log entries."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        result = await self._session.execute(
            select(AuditLog)
            .where(AuditLog.timestamp >= cutoff)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_failed_logins(
        self, limit: int = 50
    ) -> List[AuditLog]:
        """Get failed login attempts for security review."""
        result = await self._session.execute(
            select(AuditLog)
            .where(
                AuditLog.action == "login",
                AuditLog.status == "failure",
            )
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
