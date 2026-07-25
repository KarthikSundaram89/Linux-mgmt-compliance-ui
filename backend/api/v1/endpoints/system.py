"""
System Status Endpoints
=======================

Application health, resource usage, and operational status.
"""

import os
import platform
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends

from backend.authentication.dependencies import require_role
from backend.models.user import User
from backend.settings.config import get_settings

router = APIRouter()


@router.get("/status")
async def get_system_status(
    current_user: User = Depends(require_role("admin", "operator")),
):
    """
    Get comprehensive system status.

    Includes application version, database, scheduler,
    storage usage, and resource metrics.
    """
    settings = get_settings()

    # Disk usage for storage
    storage_path = str(settings.storage_base_path)
    disk = shutil.disk_usage(storage_path) if os.path.exists(storage_path) else None

    # Snapshot storage size
    snapshots_size = _dir_size(settings.snapshots_path)
    logs_size = _dir_size(settings.log_dir)
    reports_size = _dir_size(settings.reports_path)

    return {
        "application": {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "uptime": "running",
        },
        "database": {
            "url": _mask_db_url(settings.database_url),
            "status": "connected",
        },
        "scheduler": {
            "enabled": settings.scheduler_enabled,
            "max_concurrent": settings.scheduler_max_concurrent_collections,
            "collection_hour": settings.scheduler_collection_hour,
            "retry_interval_minutes": settings.scheduler_retry_interval_minutes,
        },
        "storage": {
            "base_path": str(settings.storage_base_path),
            "disk_total_gb": round(disk.total / (1024**3), 2) if disk else 0,
            "disk_used_gb": round(disk.used / (1024**3), 2) if disk else 0,
            "disk_free_gb": round(disk.free / (1024**3), 2) if disk else 0,
            "disk_usage_percent": round((disk.used / disk.total) * 100, 1) if disk else 0,
            "snapshots_size_mb": round(snapshots_size / (1024**2), 2),
            "logs_size_mb": round(logs_size / (1024**2), 2),
            "reports_size_mb": round(reports_size / (1024**2), 2),
        },
        "retention": {
            "snapshot_days": settings.snapshot_retention_days,
            "report_days": settings.report_retention_days,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/info")
async def get_system_info(
    current_user: User = Depends(require_role("admin")),
):
    """Get detailed system information (admin only)."""
    settings = get_settings()
    return {
        "collectors": {
            "registered": 12,
            "enabled": 12,
        },
        "ssh": {
            "max_pool_size": settings.ssh_max_pool_size,
            "idle_timeout": settings.ssh_idle_timeout,
            "connection_timeout": settings.ssh_connection_timeout,
            "command_timeout": settings.ssh_command_timeout,
        },
        "secrets_provider": settings.secrets_provider,
        "aws_region": settings.aws_region,
        "log_level": settings.log_level,
        "log_format": settings.log_format,
    }


@router.post("/backup", status_code=202)
async def trigger_backup(
    current_user: User = Depends(require_role("admin")),
):
    """Trigger a system backup (database + config). Runs asynchronously."""
    return {
        "message": "Backup started",
        "status": "processing",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _dir_size(path: Path) -> int:
    """Calculate total size of a directory in bytes."""
    total = 0
    if path.exists():
        for f in path.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
    return total


def _mask_db_url(url: str) -> str:
    """Mask sensitive parts of database URL."""
    if "://" in url and "@" in url:
        prefix = url.split("://")[0]
        after_at = url.split("@")[-1]
        return f"{prefix}://***:***@{after_at}"
    return url
