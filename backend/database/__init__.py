"""
Database Module
===============

Database engine, session management, and utilities.
Abstracts database access to allow PostgreSQL migration later.
"""

from backend.database.session import (
    get_session,
    engine,
    async_session_factory,
    init_db,
)

__all__ = ["get_session", "engine", "async_session_factory", "init_db"]
