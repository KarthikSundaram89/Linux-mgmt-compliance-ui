"""
Inventory Snapshot Model
========================

Metadata record pointing to a compressed JSON snapshot file on disk.
The actual inventory data is stored as compressed JSON, not in the database.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin, generate_uuid


class InventorySnapshot(Base, TimestampMixin):
    """
    Metadata for an inventory snapshot stored on disk.
    
    The actual snapshot data is a compressed JSON file stored under
    storage/snapshots/{hostname}/{date}.json.gz
    
    Attributes:
        id: Unique snapshot identifier (UUID).
        server_id: Foreign key to the server this snapshot belongs to.
        file_path: Relative path to the compressed snapshot file.
        file_size_bytes: Size of the compressed snapshot file.
        checksum: SHA-256 checksum of the snapshot file for integrity.
        collected_at: When the data was collected.
        collectors_run: Comma-separated list of collectors that ran.
        os_family: Operating system family detected.
        os_version: Operating system version detected.
        kernel_version: Kernel version at time of collection.
        change_count: Number of changes detected vs. previous snapshot.
    """
    
    __tablename__ = "inventory_snapshots"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    server_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(
        String(500), nullable=False,
        comment="Relative path to snapshot file on disk"
    )
    file_size_bytes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    checksum: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="SHA-256 hash of snapshot file"
    )
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    collectors_run: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Comma-separated collector names"
    )
    os_family: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    os_version: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    kernel_version: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    change_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    
    # Relationships
    collection: Mapped[Optional["Collection"]] = relationship(
        "Collection", back_populates="snapshot", uselist=False
    )
    
    def __repr__(self) -> str:
        return f"<InventorySnapshot(server_id={self.server_id}, file={self.file_path})>"
