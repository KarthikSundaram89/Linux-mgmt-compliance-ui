"""
Dashboard Endpoints
===================

Provides summary statistics and compliance overview.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.v1.schemas import DashboardStats
from backend.authentication.dependencies import get_current_user
from backend.database.session import get_session
from backend.models.user import User
from backend.repositories.server_repository import ServerRepository

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Get dashboard summary statistics.
    
    Returns counts for servers, collections, and changes.
    """
    repo = ServerRepository(session)
    
    total = await repo.count({"is_deleted": False})
    active = await repo.count({"is_active": True, "is_deleted": False})
    
    return DashboardStats(
        total_servers=total,
        active_servers=active,
        servers_online=active,  # Refined in Phase 2
        servers_failed=0,
        total_collections_today=0,
        total_changes_today=0,
        critical_changes=0,
        pending_notifications=0,
    )
