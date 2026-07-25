"""
Scheduler Endpoints
===================

Control the collection scheduler (status, pause, resume, trigger).
"""

from fastapi import APIRouter, Depends, Request

from backend.authentication.dependencies import require_role
from backend.models.user import User

router = APIRouter()


@router.get("/status")
async def get_scheduler_status(
    request: Request,
    current_user: User = Depends(require_role("admin", "operator")),
):
    """Get current scheduler status and job info."""
    scheduler = request.app.state.scheduler
    status = await scheduler.get_status()
    return status


@router.post("/pause")
async def pause_scheduler(
    request: Request,
    current_user: User = Depends(require_role("admin")),
):
    """Pause all scheduled jobs."""
    scheduler = request.app.state.scheduler
    await scheduler.pause()
    return {"message": "Scheduler paused"}


@router.post("/resume")
async def resume_scheduler(
    request: Request,
    current_user: User = Depends(require_role("admin")),
):
    """Resume all scheduled jobs."""
    scheduler = request.app.state.scheduler
    await scheduler.resume()
    return {"message": "Scheduler resumed"}
