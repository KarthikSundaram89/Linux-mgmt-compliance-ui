"""
Collection Endpoints
====================

View collection history and trigger manual collections.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.v1.schemas import CollectionResponse, PaginatedResponse
from backend.authentication.dependencies import get_current_user, require_permission
from backend.database.session import get_session
from backend.models.user import User
from backend.repositories.collection_repository import CollectionRepository

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_collections(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    server_id: str = Query(default=None),
    status_filter: str = Query(default=None, alias="status"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    List collections with pagination and optional filters.
    
    Can filter by server_id and collection status.
    """
    repo = CollectionRepository(session)
    filters = {}
    if server_id:
        filters["server_id"] = server_id
    if status_filter:
        filters["status"] = status_filter
    
    total = await repo.count(filters)
    skip = (page - 1) * page_size
    items = await repo.get_all(
        skip=skip, limit=page_size, filters=filters,
        order_by="created_at", descending=True,
    )
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=[CollectionResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a single collection by ID."""
    repo = CollectionRepository(session)
    collection = await repo.get_by_id(collection_id)
    
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    return CollectionResponse.model_validate(collection)


@router.post("/trigger/{server_id}", status_code=202)
async def trigger_collection(
    server_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("collections", "execute")),
):
    """
    Manually trigger a collection for a specific server.
    
    Returns 202 Accepted; collection runs asynchronously.
    """
    # TODO: Integrate with CollectionService in Phase 2
    return {
        "message": "Collection triggered",
        "server_id": server_id,
        "triggered_by": current_user.username,
    }


@router.post("/trigger-all", status_code=202)
async def trigger_full_collection(
    current_user: User = Depends(require_permission("collections", "execute")),
):
    """
    Manually trigger collection for all active servers.
    
    Returns 202 Accepted; collection runs asynchronously.
    """
    # TODO: Integrate with SchedulerManager.trigger_collection_now()
    return {
        "message": "Full collection triggered",
        "triggered_by": current_user.username,
    }
