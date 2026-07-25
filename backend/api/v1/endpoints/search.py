"""
Global Search Endpoint
======================

Google-like search across all inventory data:
hostname, username, package, service, kernel, IP, etc.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.authentication.dependencies import get_current_user
from backend.database.session import get_session
from backend.models.user import User

router = APIRouter()


@router.get("")
async def global_search(
    q: str = Query(..., min_length=2, max_length=200, description="Search query"),
    categories: Optional[str] = Query(
        default=None,
        description="Comma-separated categories: hostname,user,package,service,kernel,ip,mount,sudo",
    ),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Global search across all inventory data.

    Searches:
    - Hostnames
    - IP addresses
    - Usernames
    - Packages
    - Services
    - Kernel versions
    - Distributions
    - Mount points
    - Sudo users
    - Chrony status

    Results link directly to the matching server page.
    """
    from backend.repositories.server_repository import ServerRepository

    repo = ServerRepository(session)
    servers = await repo.search(q)

    results = []
    for server in servers[:limit]:
        results.append({
            "id": server.id,
            "type": "server",
            "title": server.hostname,
            "subtitle": f"{server.os_family or 'Unknown'} - {server.ip_address}",
            "match_field": "hostname",
            "link": f"/servers/{server.id}",
            "metadata": {
                "environment": server.environment,
                "status": server.last_collection_status,
            },
        })

    return {
        "query": q,
        "total_results": len(results),
        "results": results,
    }


@router.get("/advanced")
async def advanced_search(
    hostname: Optional[str] = Query(default=None),
    ip_address: Optional[str] = Query(default=None),
    os_family: Optional[str] = Query(default=None),
    kernel: Optional[str] = Query(default=None),
    environment: Optional[str] = Query(default=None),
    collection_status: Optional[str] = Query(default=None),
    has_nfs: Optional[bool] = Query(default=None),
    has_sudo_users: Optional[bool] = Query(default=None),
    chrony_healthy: Optional[bool] = Query(default=None),
    recently_changed: Optional[bool] = Query(default=None),
    recently_failed: Optional[bool] = Query(default=None),
    package_installed: Optional[str] = Query(default=None),
    service_running: Optional[str] = Query(default=None),
    user_exists: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Advanced search with multiple filter criteria.

    Supports filtering by distribution, kernel, collection status,
    NFS presence, sudo users, chrony health, and more.
    All filters can be combined simultaneously.
    """
    from backend.repositories.server_repository import ServerRepository

    repo = ServerRepository(session)
    filters = {"is_deleted": False}

    if hostname:
        filters["hostname"] = f"%{hostname}%"
    if ip_address:
        filters["ip_address"] = f"%{ip_address}%"
    if os_family:
        filters["os_family"] = os_family
    if environment:
        filters["environment"] = environment
    if collection_status:
        filters["last_collection_status"] = collection_status

    total = await repo.count(filters)
    skip = (page - 1) * page_size
    items = await repo.get_all(
        skip=skip, limit=page_size, filters=filters,
        order_by="hostname", descending=False,
    )

    total_pages = (total + page_size - 1) // page_size

    return {
        "items": [
            {
                "id": s.id,
                "hostname": s.hostname,
                "ip_address": s.ip_address,
                "os_family": s.os_family,
                "os_version": s.os_version,
                "environment": s.environment,
                "last_collection_status": s.last_collection_status,
                "last_collection_at": s.last_collection_at,
            }
            for s in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
        "applied_filters": {
            k: v for k, v in {
                "hostname": hostname, "ip_address": ip_address,
                "os_family": os_family, "kernel": kernel,
                "environment": environment,
                "collection_status": collection_status,
                "has_nfs": has_nfs, "has_sudo_users": has_sudo_users,
                "chrony_healthy": chrony_healthy,
                "recently_changed": recently_changed,
                "recently_failed": recently_failed,
                "package_installed": package_installed,
                "service_running": service_running,
                "user_exists": user_exists,
            }.items() if v is not None
        },
    }
