"""
Application Setting Model
=========================

Key-value store for dynamic application settings
that can be changed at runtime without restart.
"""

from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, TimestampMixin, generate_uuid


class ApplicationSetting(Base, TimestampMixin):
    """
    Dynamic application configuration stored in the database.
    
    Used for settings that administrators can change at runtime
    through the UI, such as concurrent collection limits,
    notification preferences, and retention policies.
    
    Attributes:
        id: Unique setting identifier (UUID).
        key: Setting key (unique, used for lookups).
        value: Setting value (stored as string, parsed by application).
        value_type: Data type hint (string, integer, boolean, json).
        category: Grouping category for UI organization.
        description: Human-readable description of the setting.
        is_sensitive: Whether this setting should be masked in the UI.
        updated_by: User who last modified this setting.
    """
    
    __tablename__ = "application_settings"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    key: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    value: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    value_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="string",
        comment="string, integer, boolean, json"
    )
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, default="general", index=True
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    is_sensitive: Mapped[bool] = mapped_column(
        default=False, nullable=False
    )
    updated_by: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    
    def __repr__(self) -> str:
        return f"<ApplicationSetting(key={self.key})>"
