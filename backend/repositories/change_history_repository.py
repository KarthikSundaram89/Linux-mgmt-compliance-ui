"""
Change History Repository
=========================

Data access layer for ChangeHistory model operations.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.change_history import ChangeHistory
from backend.repositories.base import BaseRepository


class ChangeHistoryRepository(BaseRepository[ChangeHistory]):
    """Repository for ChangeHistory CRUD and query operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(ChangeHistory, session)
    
    async def get_server_changes(
        self,
        server_id: str,
        category: Optional[str] = None,
        limit: int = 100,
    ) -> List[ChangeHistory]:
        """Get changes for a server, optionally filtered by category."""
        query = select(ChangeHistory).where(
            ChangeHistory.server_id == server_id
        )
        if category:
            query = query.where(ChangeHistory.category == category)
        query = query.order_by(
            ChangeHistory.detected_at.desc()
        ).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def get_recent_changes(
        self, hours: int = 24, limit: int = 100
    ) -> List[ChangeHistory]:
        """Get all changes detected in the last N hours."""
        from datetime import timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        result = await self._session.execute(
            select(ChangeHistory)
            .where(ChangeHistory.detected_at >= cutoff)
            .order_by(ChangeHistory.detected_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_critical_changes(
        self, limit: int = 50
    ) -> List[ChangeHistory]:
        """Get unacknowledged critical severity changes."""
        result = await self._session.execute(
            select(ChangeHistory)
            .where(
                ChangeHistory.severity == "critical",
                ChangeHistory.acknowledged == False,
            )
            .order_by(ChangeHistory.detected_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def count_by_category(self) -> dict:
        """Get change counts grouped by category."""
        result = await self._session.execute(
            select(
                ChangeHistory.category,
                func.count(ChangeHistory.id),
            ).group_by(ChangeHistory.category)
        )
        return dict(result.all())
