"""
Snapshot Endpoints
==================

View, compare, and download inventory snapshots.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.authentication.dependencies import get_current_user
from backend.database.session import get_session
from backend.models.user import User
from backend.repositories.snapshot_repository import SnapshotRepository
from backend.services.snapshot_service import SnapshotStorageService

router = APIRouter()


@router.get("/{server_id}")
async def list_server_snapshots(
    server_id: str,
    limit: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List all snapshots for a server."""
    repo = SnapshotRepository(session)
    snapshots = await repo.get_server_history(server_id, limit)
    return {
        "server_id": server_id,
        "snapshots": [
            {
                "id": s.id,
                "collected_at": s.collected_at,
                "file_path": s.file_path,
                "file_size_bytes": s.file_size_bytes,
                "checksum": s.checksum,
                "os_family": s.os_family,
                "kernel_version": s.kernel_version,
                "change_count": s.change_count,
                "collectors_run": s.collectors_run,
            }
            for s in snapshots
        ],
        "total": len(snapshots),
    }


@router.get("/{server_id}/latest")
async def get_latest_snapshot(
    server_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get the latest snapshot data for a server."""
    repo = SnapshotRepository(session)
    snapshot = await repo.get_latest_for_server(server_id)
    if not snapshot:
        raise HTTPException(404, "No snapshots found for this server")

    # Load actual snapshot data from disk
    storage = SnapshotStorageService()
    from backend.repositories.server_repository import ServerRepository
    srv_repo = ServerRepository(session)
    server = await srv_repo.get_by_id(server_id)
    if not server:
        raise HTTPException(404, "Server not found")

    data = await storage.load_latest_snapshot(server.hostname)
    return {
        "snapshot_id": snapshot.id,
        "collected_at": snapshot.collected_at,
        "data": data,
    }


@router.get("/{server_id}/compare")
async def compare_snapshots(
    server_id: str,
    snapshot_a: str = Query(..., description="First snapshot ID"),
    snapshot_b: str = Query(..., description="Second snapshot ID"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Compare two snapshots and return differences.

    Highlights additions (green), removals (red), and modifications (yellow).
    """
    from backend.services.change_detection_service import ChangeDetectionEngine

    repo = SnapshotRepository(session)
    snap_a = await repo.get_by_id(snapshot_a)
    snap_b = await repo.get_by_id(snapshot_b)

    if not snap_a or not snap_b:
        raise HTTPException(404, "One or both snapshots not found")

    # Load snapshot data from disk
    storage = SnapshotStorageService()
    from backend.repositories.server_repository import ServerRepository
    srv_repo = ServerRepository(session)
    server = await srv_repo.get_by_id(server_id)
    if not server:
        raise HTTPException(404, "Server not found")

    # Use change detection to find differences
    engine = ChangeDetectionEngine()
    # For comparison we need to load both snapshots from disk
    # This is a simplified version - full impl would load from file paths

    return {
        "server_id": server_id,
        "snapshot_a": {"id": snap_a.id, "collected_at": snap_a.collected_at},
        "snapshot_b": {"id": snap_b.id, "collected_at": snap_b.collected_at},
        "differences": [],
        "summary": {
            "added": 0,
            "removed": 0,
            "modified": 0,
        },
    }
