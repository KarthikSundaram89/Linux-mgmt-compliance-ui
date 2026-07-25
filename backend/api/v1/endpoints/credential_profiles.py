"""
Credential Profile Endpoints
=============================

CRUD for SSH credential profiles.
Secrets (ARNs) are stored but never returned in full.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.v1.schemas import (
    CredentialProfileCreate,
    CredentialProfileResponse,
    PaginatedResponse,
)
from backend.authentication.dependencies import get_current_user, require_role
from backend.database.session import get_session
from backend.models.credential_profile import CredentialProfile
from backend.models.user import User
from backend.repositories.credential_profile_repository import CredentialProfileRepository

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_credential_profiles(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List all credential profiles with pagination."""
    repo = CredentialProfileRepository(session)
    filters = {"is_deleted": False}
    total = await repo.count(filters)
    skip = (page - 1) * page_size
    items = await repo.get_all(skip=skip, limit=page_size, filters=filters)
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=[CredentialProfileResponse.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )


@router.get("/{profile_id}", response_model=CredentialProfileResponse)
async def get_credential_profile(
    profile_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a single credential profile by ID."""
    repo = CredentialProfileRepository(session)
    profile = await repo.get_by_id(profile_id)
    
    if not profile or profile.is_deleted:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return CredentialProfileResponse.model_validate(profile)


@router.post("", response_model=CredentialProfileResponse, status_code=201)
async def create_credential_profile(
    data: CredentialProfileCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    """Create a new credential profile (admin only)."""
    repo = CredentialProfileRepository(session)
    
    existing = await repo.get_by_name(data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Profile '{data.name}' already exists",
        )
    
    profile = CredentialProfile(**data.model_dump())
    profile = await repo.create(profile)
    return CredentialProfileResponse.model_validate(profile)


@router.delete("/{profile_id}", status_code=204)
async def delete_credential_profile(
    profile_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    """Soft-delete a credential profile (admin only)."""
    repo = CredentialProfileRepository(session)
    profile = await repo.get_by_id(profile_id)
    
    if not profile or profile.is_deleted:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    await repo.soft_delete(profile)
