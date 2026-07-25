"""
Repositories Module
===================

Data access layer implementing the Repository Pattern.
Each repository encapsulates database operations for a specific model.
Business logic should never directly access the database.
"""

from backend.repositories.base import BaseRepository
from backend.repositories.server_repository import ServerRepository
from backend.repositories.credential_profile_repository import CredentialProfileRepository
from backend.repositories.collection_repository import CollectionRepository
from backend.repositories.snapshot_repository import SnapshotRepository
from backend.repositories.change_history_repository import ChangeHistoryRepository
from backend.repositories.user_repository import UserRepository
from backend.repositories.audit_log_repository import AuditLogRepository

__all__ = [
    "BaseRepository",
    "ServerRepository",
    "CredentialProfileRepository",
    "CollectionRepository",
    "SnapshotRepository",
    "ChangeHistoryRepository",
    "UserRepository",
    "AuditLogRepository",
]
