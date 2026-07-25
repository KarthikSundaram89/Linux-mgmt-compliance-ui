"""
Server Endpoints
================

CRUD operations and search for Linux servers.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.v1.schemas import (
    PaginatedResponse,
    ServerCreate,
    ServerResponse,
    ServerUpdate,
)
from backend.authentication.dependencies import get_current_user, require_permission
from backend.database.session import get_session
from backend.models.server import Server
from backend.models.user import User
from backend.repositories.server_repository import ServerRepository

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_servers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    search: str = Query(default=None),
    environment: str = Query(default=None),
    os_family: str = Query(default=None),
    is_active: bool = Query(default=None),
    sort_by: str = Query(default="hostname"),
    sort_order: str = Query(default="asc"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    List all servers with pagination, filtering, and search.
    
    Supports filtering by environment, OS family, and active status.
    Supports search across hostname, IP, and tags.
    """
    repo = ServerRepository(session)
    
    # Build filters
    filters = {"is_deleted": False}
    if environment:
        filters["environment"] = environment
    if os_family:
        filters["os_family"] = os_family
    if is_active is not None:
        filters["is_active"] = is_active
    
    # If search is provided, use search method
    if search:
        items = await repo.search(search)
        total = len(items)
        # Manual pagination for search results
        start = (page - 1) * page_size
        items = items[start:start + page_size]
    else:
        total = await repo.count(filters)
        skip = (page - 1) * page_size
        items = await repo.get_all(
            skip=skip,
            limit=page_size,
            filters=filters,
            order_by=sort_by,
            descending=(sort_order == "desc"),
        )
    
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=[ServerResponse.model_validate(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )


@router.get("/{server_id}", response_model=ServerResponse)
async def get_server(
    server_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a single server by ID."""
    repo = ServerRepository(session)
    server = await repo.get_by_id(server_id)
    
    if not server or server.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )
    
    return ServerResponse.model_validate(server)


@router.post("", response_model=ServerResponse, status_code=status.HTTP_201_CREATED)
async def create_server(
    data: ServerCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("servers", "write")),
):
    """Create a new server."""
    repo = ServerRepository(session)
    
    # Check for duplicate hostname
    existing = await repo.get_by_hostname(data.hostname)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Server with hostname '{data.hostname}' already exists",
        )
    
    server = Server(**data.model_dump())
    server = await repo.create(server)
    return ServerResponse.model_validate(server)


@router.put("/{server_id}", response_model=ServerResponse)
async def update_server(
    server_id: str,
    data: ServerUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("servers", "write")),
):
    """Update an existing server."""
    repo = ServerRepository(session)
    server = await repo.get_by_id(server_id)
    
    if not server or server.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )
    
    update_data = data.model_dump(exclude_unset=True)
    server = await repo.update(server, update_data)
    return ServerResponse.model_validate(server)


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("servers", "delete")),
):
    """Soft-delete a server."""
    repo = ServerRepository(session)
    server = await repo.get_by_id(server_id)
    
    if not server or server.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )
    
    await repo.soft_delete(server)
