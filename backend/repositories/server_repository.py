"""
Server Repository
=================

Data access layer for Server model operations.
"""

from typing import List, Optional

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.server import Server
from backend.repositories.base import BaseRepository


class ServerRepository(BaseRepository[Server]):
    """Repository for Server CRUD and query operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Server, session)
    
    async def get_by_hostname(
        self, hostname: str
    ) -> Optional[Server]:
        """Find a server by its hostname."""
        result = await self._session.execute(
            select(Server).where(Server.hostname == hostname)
        )
        return result.scalar_one_or_none()
    
    async def get_active_servers(self) -> List[Server]:
        """Get all active, non-deleted servers."""
        result = await self._session.execute(
            select(Server).where(
                Server.is_active == True,
                Server.is_deleted == False,
            )
        )
        return list(result.scalars().all())
    
    async def get_failed_servers(self) -> List[Server]:
        """Get servers whose last collection failed."""
        result = await self._session.execute(
            select(Server).where(
                Server.is_active == True,
                Server.is_deleted == False,
                Server.last_collection_status == "failed",
            )
        )
        return list(result.scalars().all())
    
    async def search(self, query: str) -> List[Server]:
        """Search servers by hostname, IP, or tags."""
        pattern = f"%{query}%"
        result = await self._session.execute(
            select(Server).where(
                Server.is_deleted == False,
                or_(
                    Server.hostname.ilike(pattern),
                    Server.ip_address.ilike(pattern),
                    Server.tags.ilike(pattern),
                    Server.os_family.ilike(pattern),
                    Server.environment.ilike(pattern),
                )
            )
        )
        return list(result.scalars().all())
