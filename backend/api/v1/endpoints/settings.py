"""
Settings Endpoints
==================

Application settings management (admin only).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.authentication.dependencies import require_role
from backend.database.session import get_session
from backend.models.user import User

router = APIRouter()


@router.get("")
async def get_settings(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    """Get all application settings (admin only)."""
    # TODO: Implement with ApplicationSettingRepository
    return {"settings": []}


@router.put("/{key}")
async def update_setting(
    key: str,
    value: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    """Update a single application setting (admin only)."""
    return {"key": key, "message": "Setting updated"}
