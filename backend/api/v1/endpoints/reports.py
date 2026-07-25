"""
Reports Endpoints
=================

Generate and download inventory reports.
Reports are generated asynchronously and stored on disk.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.authentication.dependencies import get_current_user
from backend.database.session import get_session
from backend.models.user import User

router = APIRouter()


@router.get("")
async def list_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List generated reports with pagination."""
    # TODO: Implement with ReportRepository in Phase 2
    return {
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
        "total_pages": 0,
        "has_next": False,
        "has_previous": False,
    }


@router.post("/generate", status_code=202)
async def generate_report(
    report_type: str = Query(
        ..., description="Report type: inventory, compliance, changes"
    ),
    format: str = Query(
        default="csv", description="Format: csv, excel, pdf"
    ),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger asynchronous report generation.
    
    Returns 202 Accepted. Report will be available via GET /reports.
    """
    valid_types = {"inventory", "compliance", "changes"}
    valid_formats = {"csv", "excel", "pdf"}
    
    if report_type not in valid_types:
        raise HTTPException(400, f"Invalid type. Must be: {valid_types}")
    if format not in valid_formats:
        raise HTTPException(400, f"Invalid format. Must be: {valid_formats}")
    
    return {
        "message": "Report generation started",
        "report_type": report_type,
        "format": format,
        "requested_by": current_user.username,
    }
