"""
Credential Profile Repository
==============================

Data access layer for CredentialProfile model operations.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.credential_profile import CredentialProfile
from backend.repositories.base import BaseRepository


class CredentialProfileRepository(BaseRepository[CredentialProfile]):
    """Repository for CredentialProfile CRUD and query operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(CredentialProfile, session)
    
    async def get_by_name(
        self, name: str
    ) -> Optional[CredentialProfile]:
        """Find a credential profile by name."""
        result = await self._session.execute(
            select(CredentialProfile).where(
                CredentialProfile.name == name
            )
        )
        return result.scalar_one_or_none()
    
    async def get_active_profiles(self) -> List[CredentialProfile]:
        """Get all active credential profiles."""
        result = await self._session.execute(
            select(CredentialProfile).where(
                CredentialProfile.is_active == True,
                CredentialProfile.is_deleted == False,
            )
        )
        return list(result.scalars().all())
