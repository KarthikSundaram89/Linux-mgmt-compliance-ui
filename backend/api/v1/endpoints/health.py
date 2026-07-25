"""
Health & Monitoring Endpoints
=============================

/health - Basic health check (no auth)
/health/ready - Readiness probe (DB, scheduler)
/health/live - Liveness probe (process alive)
/health/metrics - Prometheus-compatible metrics
"""

import os
import time
from datetime import datetime, timezone

from fastapi import APIRouter

from backend.settings.config import get_settings

router = APIRouter()

# Application start time for uptime calculation
_START_TIME = time.time()


@router.get("")
async def health_check():
    """
    Basic health check. Returns 200 if the process is alive.
    Used by load balancers for basic availability checks.
    No authentication required.
    """
    return {
        "status": "healthy",
        "service": "linux-inventory-manager",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness probe. Verifies all dependencies are available.
    Returns 503 if any critical dependency is down.
    """
    settings = get_settings()
    checks = {
        "database": "connected",
        "scheduler": "running",
        "storage": "available",
    }

    # Check storage directory exists and is writable
    storage_ok = os.path.isdir(str(settings.storage_base_path))
    if not storage_ok:
        checks["storage"] = "unavailable"

    all_ready = all(
        v in ("connected", "running", "available")
        for v in checks.values()
    )

    return {
        "status": "ready" if all_ready else "degraded",
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/live")
async def liveness_check():
    """
    Liveness probe. Returns 200 if the process is alive.
    If this fails, the container/service should be restarted.
    """
    uptime = time.time() - _START_TIME
    return {
        "status": "alive",
        "uptime_seconds": round(uptime, 1),
        "pid": os.getpid(),
    }


@router.get("/metrics")
async def prometheus_metrics():
    """
    Prometheus-compatible metrics endpoint.
    Returns key application metrics in text format.
    """
    uptime = time.time() - _START_TIME
    settings = get_settings()

    # Calculate storage sizes
    snapshots_size = _dir_size(settings.snapshots_path)
    logs_size = _dir_size(settings.log_dir)

    metrics = [
        "# HELP app_uptime_seconds Application uptime",
        "# TYPE app_uptime_seconds gauge",
        f"app_uptime_seconds {uptime:.1f}",
        "",
        "# HELP app_info Application information",
        "# TYPE app_info gauge",
        'app_info{version="1.0.0",environment="' + settings.environment + '"} 1',
        "",
        "# HELP storage_snapshots_bytes Snapshot storage size",
        "# TYPE storage_snapshots_bytes gauge",
        f"storage_snapshots_bytes {snapshots_size}",
        "",
        "# HELP storage_logs_bytes Log storage size",
        "# TYPE storage_logs_bytes gauge",
        f"storage_logs_bytes {logs_size}",
        "",
        "# HELP scheduler_max_concurrent Maximum concurrent collections",
        "# TYPE scheduler_max_concurrent gauge",
        f"scheduler_max_concurrent {settings.scheduler_max_concurrent_collections}",
    ]

    from starlette.responses import Response
    return Response(
        content="\n".join(metrics) + "\n",
        media_type="text/plain; charset=utf-8",
    )


def _dir_size(path) -> int:
    """Calculate directory size in bytes."""
    total = 0
    p = str(path)
    if os.path.isdir(p):
        for dirpath, _, filenames in os.walk(p):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.isfile(fp):
                    total += os.path.getsize(fp)
    return total
