"""
API V1 Router
=============

Central router that aggregates all v1 endpoint routers.
Each resource has its own router module for separation of concerns.
"""

from fastapi import APIRouter

from backend.api.v1.endpoints import (
    auth,
    servers,
    credential_profiles,
    collections,
    changes,
    scheduler,
    reports,
    notifications,
    settings,
    audit_logs,
    dashboard,
    health,
    search,
    bulk,
    snapshots,
    system,
    users,
)

api_router = APIRouter()

# Health check (no auth required)
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"],
)

# Authentication
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

# Dashboard
api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"],
)

# Servers
api_router.include_router(
    servers.router,
    prefix="/servers",
    tags=["Servers"],
)

# Credential Profiles
api_router.include_router(
    credential_profiles.router,
    prefix="/credential-profiles",
    tags=["Credential Profiles"],
)

# Collections
api_router.include_router(
    collections.router,
    prefix="/collections",
    tags=["Collections"],
)

# Changes
api_router.include_router(
    changes.router,
    prefix="/changes",
    tags=["Change History"],
)

# Scheduler
api_router.include_router(
    scheduler.router,
    prefix="/scheduler",
    tags=["Scheduler"],
)

# Reports
api_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["Reports"],
)

# Notifications
api_router.include_router(
    notifications.router,
    prefix="/notifications",
    tags=["Notifications"],
)

# Settings
api_router.include_router(
    settings.router,
    prefix="/settings",
    tags=["Settings"],
)

# Audit Logs
api_router.include_router(
    audit_logs.router,
    prefix="/audit-logs",
    tags=["Audit Logs"],
)

# Search
api_router.include_router(
    search.router,
    prefix="/search",
    tags=["Search"],
)

# Bulk Operations
api_router.include_router(
    bulk.router,
    prefix="/bulk",
    tags=["Bulk Operations"],
)

# Snapshots
api_router.include_router(
    snapshots.router,
    prefix="/snapshots",
    tags=["Snapshots"],
)

# System Status
api_router.include_router(
    system.router,
    prefix="/system",
    tags=["System"],
)

# User Management
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
)
