"""
Scheduler Module
================

APScheduler-based task scheduling for inventory collection.
Supports daily collection, retry logic, and manual triggers.
"""

from backend.scheduler.manager import SchedulerManager

__all__ = ["SchedulerManager"]
