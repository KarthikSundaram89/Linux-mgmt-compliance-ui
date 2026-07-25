"""
Database Models
===============

SQLAlchemy ORM models representing the application's data layer.
All models inherit from the declarative base defined in database.base.
"""

from backend.models.base import Base, TimestampMixin, SoftDeleteMixin
from backend.models.server import Server
from backend.models.credential_profile import CredentialProfile
from backend.models.collection import Collection
from backend.models.inventory_snapshot import InventorySnapshot
from backend.models.change_history import ChangeHistory
from backend.models.audit_log import AuditLog
from backend.models.notification import Notification
from backend.models.application_setting import ApplicationSetting
from backend.models.user import User
from backend.models.role import Role, Permission, RolePermission

__all__ = [
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",
    "Server",
    "CredentialProfile",
    "Collection",
    "InventorySnapshot",
    "ChangeHistory",
    "AuditLog",
    "Notification",
    "ApplicationSetting",
    "User",
    "Role",
    "Permission",
    "RolePermission",
]
