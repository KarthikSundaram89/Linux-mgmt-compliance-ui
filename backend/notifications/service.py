"""
Notification Service
====================

Creates and delivers notifications for system events.
Supports in-app notifications and email delivery.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from backend.models.notification import Notification
from backend.models.base import generate_uuid

logger = logging.getLogger("app")


class NotificationService:
    """
    Manages system notifications.
    
    Creates notifications for:
    - Collection failures
    - Critical changes detected
    - Security events
    - Scheduler status changes
    
    Delivery channels:
    - In-app (stored in database)
    - Email (via SMTP, future implementation)
    """
    
    async def create_notification(
        self,
        title: str,
        message: str,
        severity: str = "info",
        category: str = "system",
        source: Optional[str] = None,
        target_user_id: Optional[str] = None,
        server_id: Optional[str] = None,
        link: Optional[str] = None,
    ) -> Notification:
        """
        Create a new notification.
        
        Args:
            title: Short notification title.
            message: Full message content.
            severity: info, warning, error, critical.
            category: collection, change, security, system.
            source: What generated this notification.
            target_user_id: Specific user (None = all admins).
            server_id: Related server if applicable.
            link: URL to related resource.
        
        Returns:
            Created Notification instance.
        """
        notification = Notification(
            id=generate_uuid(),
            title=title,
            message=message,
            severity=severity,
            category=category,
            source=source,
            target_user_id=target_user_id,
            server_id=server_id,
            link=link,
        )
        
        logger.info(
            f"Notification created: {title}",
            extra={
                "severity": severity,
                "category": category,
            },
        )
        
        return notification
    
    async def notify_collection_failure(
        self,
        hostname: str,
        server_id: str,
        error_message: str,
    ) -> Notification:
        """Create a notification for a failed collection."""
        return await self.create_notification(
            title=f"Collection failed: {hostname}",
            message=f"Failed to collect inventory: {error_message}",
            severity="error",
            category="collection",
            source="collector",
            server_id=server_id,
            link=f"/servers/{server_id}",
        )
    
    async def notify_critical_change(
        self,
        hostname: str,
        server_id: str,
        change_description: str,
    ) -> Notification:
        """Create a notification for a critical change."""
        return await self.create_notification(
            title=f"Critical change: {hostname}",
            message=change_description,
            severity="critical",
            category="change",
            source="change_detection",
            server_id=server_id,
            link=f"/servers/{server_id}/changes",
        )
