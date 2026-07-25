"""
Change History Model
====================

Records detected changes between consecutive inventory snapshots.
Only differences are stored, not full state.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin, generate_uuid


class ChangeHistory(Base, TimestampMixin):
    """
    A single detected change between two inventory snapshots.
    
    Attributes:
        id: Unique change record identifier (UUID).
        server_id: Server where the change was detected.
        snapshot_id: Snapshot that detected this change.
        category: Change category (user, package, service, filesystem, etc.).
        change_type: Type of change (added, removed, modified).
        field_name: Specific field or item that changed.
        old_value: Previous value (null for additions).
        new_value: Current value (null for removals).
        severity: Change severity (info, warning, critical).
        detected_at: When the change was detected.
        acknowledged: Whether an admin has acknowledged this change.
        acknowledged_by: User who acknowledged the change.
    """
    
    __tablename__ = "change_history"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    server_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("servers.id"),
        nullable=False,
        index=True,
    )
    snapshot_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("inventory_snapshots.id"),
        nullable=True,
        index=True,
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="user, package, service, filesystem, kernel, password_policy, network, chrony",
    )
    change_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="added, removed, modified",
    )
    field_name: Mapped[str] = mapped_column(
        String(200), nullable=False,
        comment="Specific field or item that changed"
    )
    old_value: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    new_value: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="info",
        index=True,
        comment="info, warning, critical",
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    acknowledged: Mapped[bool] = mapped_column(
        default=False, nullable=False
    )
    acknowledged_by: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    
    # Relationships
    server: Mapped["Server"] = relationship("Server", lazy="selectin")
    
    def __repr__(self) -> str:
        return (
            f"<ChangeHistory(server_id={self.server_id}, "
            f"category={self.category}, type={self.change_type})>"
        )
