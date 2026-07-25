"""
Notifications Endpoints
=======================

List and manage user notifications.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.v1.schemas import NotificationResponse, PaginatedResponse
from backend.authentication.dependencies import get_current_user
from backend.database.session import get_session
from backend.models.user import User

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    unread_only: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List notifications for the current user."""
    # TODO: Implement with NotificationRepository
    return PaginatedResponse(
        items=[],
        total=0,
        page=page,
        page_size=page_size,
        total_pages=0,
        has_next=False,
        has_previous=False,
    )


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Mark a notification as read."""
    return {"message": "Notification marked as read", "id": notification_id}


@router.post("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
):
    """Mark all notifications as read for current user."""
    return {"message": "All notifications marked as read"}
