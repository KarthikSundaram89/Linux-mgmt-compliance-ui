"""
Logging Module
==============

Structured logging framework with separate log files,
automatic rotation, and compression of old logs.
"""

from backend.logging.setup import setup_logging

__all__ = ["setup_logging"]
