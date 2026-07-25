"""
Collectors Module
=================

Plugin-based Linux inventory data collectors.
Each collector is independent and returns structured JSON.

Architecture:
    SSH Manager → Collector → Parser → Repository → SQLite + Snapshot JSON

Collectors never directly update the database.

Security:
    Every command executed MUST be in the COMMAND_ALLOWLIST.
    No arbitrary or user-supplied commands are permitted.
"""

from backend.collectors.base import (
    BaseCollector,
    CollectorResult,
    LinuxDistro,
    SecurityError,
    is_command_allowed,
    COMMAND_ALLOWLIST,
)
from backend.collectors.registry import (
    collector_registry,
    register_all_collectors,
)

__all__ = [
    "BaseCollector",
    "CollectorResult",
    "LinuxDistro",
    "SecurityError",
    "is_command_allowed",
    "COMMAND_ALLOWLIST",
    "collector_registry",
    "register_all_collectors",
]
