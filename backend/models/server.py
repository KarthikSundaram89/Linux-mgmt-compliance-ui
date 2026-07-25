"""
Server Model
============

Represents a Linux server that is inventoried by the platform.
Each server is associated with a credential profile for SSH access.
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin, SoftDeleteMixin, generate_uuid


class Server(Base, TimestampMixin, SoftDeleteMixin):
    """
    A Linux server managed by the inventory platform.
    
    Attributes:
        id: Unique server identifier (UUID).
        hostname: Server hostname (FQDN or short name).
        ip_address: Primary IP address used for SSH connection.
        port: SSH port override (uses credential profile default if null).
        description: Human-readable description of the server.
        environment: Deployment environment (production, staging, development, etc.).
        location: Physical or logical location identifier.
        os_family: Operating system family (rhel, ubuntu, amazon_linux, etc.).
        os_version: Operating system version string.
        credential_profile_id: Foreign key to the credential profile for SSH access.
        is_active: Whether the server is actively collected.
        last_collection_at: Timestamp of last successful collection.
        last_collection_status: Status of the most recent collection attempt.
        tags: Comma-separated tags for categorization.
    """
    
    __tablename__ = "servers"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    hostname: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    ip_address: Mapped[str] = mapped_column(
        String(45), nullable=False, index=True
    )
    port: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="SSH port override"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    environment: Mapped[str] = mapped_column(
        String(50), nullable=False, default="production", index=True
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    os_family: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )
    os_version: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    credential_profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("credential_profiles.id"),
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )
    last_collection_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_collection_status: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="success, failed, in_progress"
    )
    tags: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Comma-separated tags"
    )
    
    # Relationships
    credential_profile: Mapped["CredentialProfile"] = relationship(
        "CredentialProfile", back_populates="servers", lazy="selectin"
    )
    collections: Mapped[List["Collection"]] = relationship(
        "Collection", back_populates="server", lazy="dynamic"
    )
    
    def __repr__(self) -> str:
        return f"<Server(hostname={self.hostname}, ip={self.ip_address})>"
