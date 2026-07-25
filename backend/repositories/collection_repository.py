"""
Collection Repository
=====================

Data access layer for Collection model operations.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.collection import Collection
from backend.repositories.base import BaseRepository


class CollectionRepository(BaseRepository[Collection]):
    """Repository for Collection CRUD and query operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Collection, session)
    
    async def get_latest_for_server(
        self, server_id: str
    ) -> Optional[Collection]:
        """Get the most recent collection for a server."""
        result = await self._session.execute(
            select(Collection)
            .where(Collection.server_id == server_id)
            .order_by(Collection.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_failed_collections(self) -> List[Collection]:
        """Get all collections with failed status."""
        result = await self._session.execute(
            select(Collection).where(
                Collection.status == "failed"
            )
        )
        return list(result.scalars().all())
    
    async def get_collections_in_range(
        self,
        server_id: str,
        start: datetime,
        end: datetime,
    ) -> List[Collection]:
        """Get collections for a server within a time range."""
        result = await self._session.execute(
            select(Collection).where(
                and_(
                    Collection.server_id == server_id,
                    Collection.created_at >= start,
                    Collection.created_at <= end,
                )
            ).order_by(Collection.created_at.desc())
        )
        return list(result.scalars().all())
