"""
Credential Profile Model
=========================

Represents a reusable SSH credential configuration.
Servers reference a profile instead of storing credentials directly.
This enables key rotation without modifying individual server records.
"""

from typing import Optional, List

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin, SoftDeleteMixin, generate_uuid


class CredentialProfile(Base, TimestampMixin, SoftDeleteMixin):
    """
    SSH credential profile shared by one or more servers.
    
    Secrets (private keys, passphrases) are never stored in the database.
    Only the ARN/reference to the secrets provider is stored.
    
    Attributes:
        id: Unique profile identifier (UUID).
        name: Human-readable profile name (e.g., "Production Linux").
        description: Description of when/where this profile is used.
        ssh_username: SSH username for connections.
        ssh_port: Default SSH port for servers using this profile.
        secret_arn: ARN or reference in the secrets provider for the SSH key.
        passphrase_secret_arn: ARN for the key passphrase (if applicable).
        connection_timeout: Connection timeout in seconds.
        command_timeout: Per-command timeout in seconds.
        max_retries: Maximum connection retry attempts.
        retry_delay_seconds: Delay between retry attempts.
        is_active: Whether this profile is currently usable.
    """
    
    __tablename__ = "credential_profiles"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    ssh_username: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    ssh_port: Mapped[int] = mapped_column(
        Integer, nullable=False, default=22
    )
    secret_arn: Mapped[str] = mapped_column(
        String(512), nullable=False,
        comment="ARN or reference to SSH private key in secrets provider"
    )
    passphrase_secret_arn: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True,
        comment="ARN for key passphrase in secrets provider"
    )
    connection_timeout: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30,
        comment="Connection timeout in seconds"
    )
    command_timeout: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60,
        comment="Command execution timeout in seconds"
    )
    max_retries: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3
    )
    retry_delay_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )
    
    # Relationships
    servers: Mapped[List["Server"]] = relationship(
        "Server", back_populates="credential_profile", lazy="dynamic"
    )
    
    def __repr__(self) -> str:
        return f"<CredentialProfile(name={self.name}, user={self.ssh_username})>"
