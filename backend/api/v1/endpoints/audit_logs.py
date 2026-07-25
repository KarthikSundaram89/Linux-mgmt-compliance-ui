"""
Audit Log Endpoints
===================

Read-only access to the audit trail.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.authentication.dependencies import require_role
from backend.database.session import get_session
from backend.models.user import User
from backend.repositories.audit_log_repository import AuditLogRepository

router = APIRouter()


@router.get("")
async def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    action: str = Query(default=None),
    user_id: str = Query(default=None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin", "auditor")),
):
    """
    List audit log entries with pagination.
    
    Only accessible by admins and auditors.
    """
    repo = AuditLogRepository(session)
    filters = {}
    if action:
        filters["action"] = action
    if user_id:
        filters["user_id"] = user_id
    
    total = await repo.count(filters)
    skip = (page - 1) * page_size
    items = await repo.get_all(
        skip=skip, limit=page_size, filters=filters,
        order_by="timestamp", descending=True,
    )
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "items": [
            {
                "id": log.id,
                "timestamp": log.timestamp,
                "user_id": log.user_id,
                "username": log.username,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "status": log.status,
                "ip_address": log.ip_address,
            }
            for log in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }
