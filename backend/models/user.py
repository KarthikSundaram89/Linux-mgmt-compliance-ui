"""
User Model
==========

Represents an application user with local authentication.
Designed to support future integration with Azure AD, LDAP, etc.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin, generate_uuid


class User(Base, TimestampMixin):
    """
    Application user account.
    
    Attributes:
        id: Unique user identifier (UUID).
        username: Unique login username.
        email: User email address.
        full_name: Display name.
        hashed_password: Bcrypt-hashed password.
        role_id: Foreign key to the user's role.
        is_active: Whether the account is enabled.
        is_locked: Whether the account is locked.
        auth_provider: Authentication provider (local, azure_ad, ldap).
        external_id: External provider user ID.
        last_login_at: Timestamp of last successful login.
        failed_login_attempts: Count of consecutive failed logins.
        password_changed_at: When the password was last changed.
    """
    
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    username: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(
        String(200), nullable=False
    )
    hashed_password: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        comment="Null for external auth providers"
    )
    role_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("roles.id"),
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )
    is_locked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    auth_provider: Mapped[str] = mapped_column(
        String(50), nullable=False, default="local",
        comment="local, azure_ad, ldap, aws_sso"
    )
    external_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        comment="External provider user ID"
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        default=0, nullable=False
    )
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Relationships
    role: Mapped[Optional["Role"]] = relationship(
        "Role", back_populates="users", lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<User(username={self.username}, role_id={self.role_id})>"
