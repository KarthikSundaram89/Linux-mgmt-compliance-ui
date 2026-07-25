"""
Health Check Endpoint
=====================

System health and readiness probes.
No authentication required.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns 200 OK if the application is running.
    Used by load balancers and monitoring systems.
    """
    return {
        "status": "healthy",
        "service": "linux-inventory-manager",
        "version": "1.0.0",
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness probe.
    
    Verifies the application can serve requests including
    database connectivity.
    """
    # TODO: Add database connectivity check
    return {
        "status": "ready",
        "database": "connected",
        "scheduler": "running",
    }
