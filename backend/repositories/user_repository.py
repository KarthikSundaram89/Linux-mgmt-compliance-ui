"""
User Repository
===============

Data access layer for User model operations.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user import User
from backend.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User CRUD and query operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def get_by_username(
        self, username: str
    ) -> Optional[User]:
        """Find a user by username."""
        result = await self._session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Find a user by email."""
        result = await self._session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_active_users(self):
        """Get all active, non-locked users."""
        result = await self._session.execute(
            select(User).where(
                User.is_active == True,
                User.is_locked == False,
            )
        )
        return list(result.scalars().all())
