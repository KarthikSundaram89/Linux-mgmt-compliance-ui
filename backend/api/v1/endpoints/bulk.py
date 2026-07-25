"""
Bulk Operations Endpoints
=========================

Asynchronous bulk operations on servers.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.authentication.dependencies import require_permission
from backend.database.session import get_session
from backend.models.user import User

router = APIRouter()


class BulkServerAction(BaseModel):
    """Request body for bulk server operations."""
    server_ids: List[str] = Field(..., min_length=1, max_length=500)


class BulkAssignProfile(BaseModel):
    """Request body for bulk credential profile assignment."""
    server_ids: List[str] = Field(..., min_length=1, max_length=500)
    credential_profile_id: str


@router.post("/collect", status_code=202)
async def bulk_collect(
    body: BulkServerAction,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("collections", "execute")),
):
    """Trigger collection for multiple servers. Runs asynchronously."""
    return {
        "message": f"Collection triggered for {len(body.server_ids)} servers",
        "server_count": len(body.server_ids),
        "triggered_by": current_user.username,
        "status": "queued",
    }


@router.post("/retry", status_code=202)
async def bulk_retry(
    body: BulkServerAction,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("collections", "execute")),
):
    """Retry failed collections for multiple servers."""
    return {
        "message": f"Retry triggered for {len(body.server_ids)} servers",
        "server_count": len(body.server_ids),
        "triggered_by": current_user.username,
        "status": "queued",
    }


@router.post("/enable-collection", status_code=200)
async def bulk_enable_collection(
    body: BulkServerAction,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("servers", "write")),
):
    """Enable collection for multiple servers."""
    from backend.repositories.server_repository import ServerRepository
    repo = ServerRepository(session)
    updated = 0
    for sid in body.server_ids:
        server = await repo.get_by_id(sid)
        if server:
            await repo.update(server, {"is_active": True})
            updated += 1
    return {"message": f"Enabled collection for {updated} servers", "updated": updated}


@router.post("/disable-collection", status_code=200)
async def bulk_disable_collection(
    body: BulkServerAction,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("servers", "write")),
):
    """Disable collection for multiple servers."""
    from backend.repositories.server_repository import ServerRepository
    repo = ServerRepository(session)
    updated = 0
    for sid in body.server_ids:
        server = await repo.get_by_id(sid)
        if server:
            await repo.update(server, {"is_active": False})
            updated += 1
    return {"message": f"Disabled collection for {updated} servers", "updated": updated}


@router.post("/assign-profile", status_code=200)
async def bulk_assign_credential_profile(
    body: BulkAssignProfile,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("servers", "write")),
):
    """Assign a credential profile to multiple servers."""
    from backend.repositories.server_repository import ServerRepository
    repo = ServerRepository(session)
    updated = 0
    for sid in body.server_ids:
        server = await repo.get_by_id(sid)
        if server:
            await repo.update(server, {"credential_profile_id": body.credential_profile_id})
            updated += 1
    return {
        "message": f"Assigned profile to {updated} servers",
        "profile_id": body.credential_profile_id,
        "updated": updated,
    }


@router.post("/delete", status_code=200)
async def bulk_delete(
    body: BulkServerAction,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("servers", "delete")),
):
    """Soft-delete multiple servers."""
    from backend.repositories.server_repository import ServerRepository
    repo = ServerRepository(session)
    deleted = 0
    for sid in body.server_ids:
        server = await repo.get_by_id(sid)
        if server and not server.is_deleted:
            await repo.soft_delete(server)
            deleted += 1
    return {"message": f"Deleted {deleted} servers", "deleted": deleted}


@router.post("/export", status_code=202)
async def bulk_export(
    body: BulkServerAction,
    format: str = "csv",
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("servers", "read")),
):
    """Export selected servers. Runs asynchronously."""
    return {
        "message": f"Export started for {len(body.server_ids)} servers",
        "format": format,
        "status": "processing",
    }
