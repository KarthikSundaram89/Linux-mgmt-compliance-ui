"""
Collection Model
================

Represents a single inventory collection attempt against a server.
Tracks status, timing, and links to the resulting snapshot.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin, generate_uuid


class Collection(Base, TimestampMixin):
    """
    An individual collection run against a server.
    
    Attributes:
        id: Unique collection identifier (UUID).
        server_id: Foreign key to the server being collected.
        status: Collection status (pending, in_progress, success, failed).
        started_at: When the collection started.
        completed_at: When the collection finished (success or failure).
        duration_seconds: Total collection duration.
        error_message: Error details if collection failed.
        retry_count: Number of retries attempted for this collection.
        triggered_by: What initiated this collection (scheduler, manual, retry).
        collector_version: Version of the collector framework used.
        snapshot_id: Foreign key to the resulting inventory snapshot.
    """
    
    __tablename__ = "collections"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    server_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("servers.id"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
        comment="pending, in_progress, success, failed",
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_seconds: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    triggered_by: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="scheduler",
        comment="scheduler, manual, retry",
    )
    collector_version: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )
    snapshot_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("inventory_snapshots.id"),
        nullable=True,
        index=True,
    )
    
    # Relationships
    server: Mapped["Server"] = relationship(
        "Server", back_populates="collections", lazy="selectin"
    )
    snapshot: Mapped[Optional["InventorySnapshot"]] = relationship(
        "InventorySnapshot", back_populates="collection", lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Collection(server_id={self.server_id}, status={self.status})>"
