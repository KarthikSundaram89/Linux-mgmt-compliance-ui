"""
Collectors Module
=================

Linux inventory data collectors.
Each collector is independent and returns structured JSON.

Architecture:
    Collector → Parser → Database Repository

Collectors never directly update the database.
"""

from backend.collectors.base import BaseCollector, CollectorResult

__all__ = ["BaseCollector", "CollectorResult"]
