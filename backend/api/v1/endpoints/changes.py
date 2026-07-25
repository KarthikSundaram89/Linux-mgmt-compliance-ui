"""
Change History Endpoints
========================

View and acknowledge detected changes between snapshots.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.v1.schemas import ChangeResponse, PaginatedResponse
from backend.authentication.dependencies import get_current_user
from backend.database.session import get_session
from backend.models.user import User
from backend.repositories.change_history_repository import ChangeHistoryRepository

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_changes(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    server_id: str = Query(default=None),
    category: str = Query(default=None),
    severity: str = Query(default=None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    List change history with pagination and filtering.
    
    Filter by server, category, or severity.
    """
    repo = ChangeHistoryRepository(session)
    filters = {}
    if server_id:
        filters["server_id"] = server_id
    if category:
        filters["category"] = category
    if severity:
        filters["severity"] = severity
    
    total = await repo.count(filters)
    skip = (page - 1) * page_size
    items = await repo.get_all(
        skip=skip, limit=page_size, filters=filters,
        order_by="detected_at", descending=True,
    )
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=[ChangeResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )


@router.post("/{change_id}/acknowledge")
async def acknowledge_change(
    change_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Acknowledge a detected change."""
    repo = ChangeHistoryRepository(session)
    change = await repo.get_by_id(change_id)
    
    if not change:
        raise HTTPException(status_code=404, detail="Change not found")
    
    await repo.update(change, {
        "acknowledged": True,
        "acknowledged_by": current_user.username,
    })
    
    return {"message": "Change acknowledged", "change_id": change_id}


@router.get("/summary")
async def get_change_summary(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get change counts grouped by category."""
    repo = ChangeHistoryRepository(session)
    summary = await repo.count_by_category()
    return {"categories": summary}
