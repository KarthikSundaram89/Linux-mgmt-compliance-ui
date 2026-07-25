"""
Audit Log Model
===============

Immutable audit trail for all significant actions in the system.
Supports security review and compliance reporting.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, generate_uuid


class AuditLog(Base):
    """
    Immutable audit log entry.
    
    Records all significant actions including:
    - Authentication events (login, logout, failed attempts)
    - Data modifications (server added, profile changed)
    - Administrative actions (user created, role modified)
    - System events (scheduler paused, collection triggered)
    
    Attributes:
        id: Unique audit entry identifier (UUID).
        timestamp: When the action occurred (UTC).
        user_id: ID of the user who performed the action (null for system).
        username: Username at time of action (denormalized for history).
        action: Action performed (login, create, update, delete, etc.).
        resource_type: Type of resource affected (server, user, profile, etc.).
        resource_id: ID of the affected resource.
        details: JSON string with additional context.
        ip_address: Client IP address.
        user_agent: Client user agent string.
        status: Whether the action succeeded or failed.
    """
    
    __tablename__ = "audit_logs"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, index=True
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    resource_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True
    )
    details: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="JSON-encoded details"
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="success",
        comment="success or failure"
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog(action={self.action}, user={self.username})>"
