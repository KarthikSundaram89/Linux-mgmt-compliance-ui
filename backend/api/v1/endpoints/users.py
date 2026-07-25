"""
User Management Endpoints
=========================

CRUD for application users (admin only).
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.authentication.dependencies import require_role
from backend.authentication.service import AuthenticationService
from backend.database.session import get_session
from backend.models.user import User
from backend.repositories.user_repository import UserRepository

router = APIRouter()


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: str = Field(..., max_length=255)
    full_name: str = Field(..., max_length=200)
    password: str = Field(..., min_length=8)
    role_id: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    role_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_locked: Optional[bool] = None


@router.get("")
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    """List all users (admin only)."""
    repo = UserRepository(session)
    total = await repo.count()
    skip = (page - 1) * page_size
    items = await repo.get_all(skip=skip, limit=page_size)
    total_pages = (total + page_size - 1) // page_size

    return {
        "items": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role.name if u.role else None,
                "is_active": u.is_active,
                "is_locked": u.is_locked,
                "auth_provider": u.auth_provider,
                "last_login_at": u.last_login_at,
                "created_at": u.created_at,
            }
            for u in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }


@router.post("", status_code=201)
async def create_user(
    data: UserCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    """Create a new user (admin only)."""
    repo = UserRepository(session)
    existing = await repo.get_by_username(data.username)
    if existing:
        raise HTTPException(409, f"Username '{data.username}' already exists")

    user = await AuthenticationService.create_user(
        session=session,
        username=data.username,
        email=data.email,
        full_name=data.full_name,
        password=data.password,
        role_id=data.role_id,
    )
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "message": "User created successfully",
    }


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    data: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    """Update a user (admin only)."""
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    update_data = data.model_dump(exclude_unset=True)
    await repo.update(user, update_data)
    return {"message": "User updated", "id": user_id}


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    """Deactivate a user (admin only)."""
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == current_user.id:
        raise HTTPException(400, "Cannot delete your own account")
    await repo.update(user, {"is_active": False})


@router.post("/{user_id}/unlock")
async def unlock_user(
    user_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    """Unlock a locked user account (admin only)."""
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    await repo.update(user, {"is_locked": False, "failed_login_attempts": 0})
    return {"message": "User unlocked", "username": user.username}
