"""
Model Base Classes
==================

Provides the SQLAlchemy declarative base and reusable mixins
for timestamps, soft-delete, and UUID primary keys.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base for all models.
    
    All ORM models must inherit from this base class.
    Provides a consistent foundation for table mapping.
    """
    pass


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamp columns.
    
    Automatically sets created_at on insert and updated_at on every update.
    Uses UTC timezone for all timestamps.
    """
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SoftDeleteMixin:
    """
    Mixin that adds soft-delete capability.
    
    Instead of physically deleting rows, marks them as deleted
    with a timestamp. Queries should filter on is_deleted=False.
    """
    
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


def generate_uuid() -> str:
    """Generate a new UUID4 string for use as primary key."""
    return str(uuid.uuid4())
