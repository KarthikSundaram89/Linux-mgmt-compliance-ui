"""
Snapshot Repository
===================

Data access layer for InventorySnapshot model operations.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.inventory_snapshot import InventorySnapshot
from backend.repositories.base import BaseRepository


class SnapshotRepository(BaseRepository[InventorySnapshot]):
    """Repository for InventorySnapshot CRUD and query operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(InventorySnapshot, session)
    
    async def get_latest_for_server(
        self, server_id: str
    ) -> Optional[InventorySnapshot]:
        """Get the most recent snapshot for a server."""
        result = await self._session.execute(
            select(InventorySnapshot)
            .where(InventorySnapshot.server_id == server_id)
            .order_by(InventorySnapshot.collected_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_previous_snapshot(
        self, server_id: str, before_snapshot_id: str
    ) -> Optional[InventorySnapshot]:
        """Get the snapshot immediately before the given one."""
        current = await self.get_by_id(before_snapshot_id)
        if not current:
            return None
        result = await self._session.execute(
            select(InventorySnapshot)
            .where(
                InventorySnapshot.server_id == server_id,
                InventorySnapshot.collected_at < current.collected_at,
            )
            .order_by(InventorySnapshot.collected_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_server_history(
        self, server_id: str, limit: int = 30
    ) -> List[InventorySnapshot]:
        """Get snapshot history for a server."""
        result = await self._session.execute(
            select(InventorySnapshot)
            .where(InventorySnapshot.server_id == server_id)
            .order_by(InventorySnapshot.collected_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
