"""
Authentication Endpoints
========================

Login, token refresh, and password management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.v1.schemas import (
    LoginRequest,
    PasswordChangeRequest,
    TokenRefreshRequest,
)
from backend.authentication.dependencies import get_current_user
from backend.authentication.service import AuthenticationService
from backend.database.session import get_session
from backend.models.user import User

router = APIRouter()


@router.post("/login")
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Authenticate user with username and password.
    
    Returns access and refresh tokens on success.
    """
    auth_service = AuthenticationService(session)
    token_response = await auth_service.authenticate(
        username=request.username,
        password=request.password,
    )
    
    if not token_response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    return token_response


@router.post("/refresh")
async def refresh_token(
    request: TokenRefreshRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Refresh an expired access token using a valid refresh token.
    """
    auth_service = AuthenticationService(session)
    token_response = await auth_service.refresh_token(
        request.refresh_token
    )
    
    if not token_response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    return token_response


@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Change the current user's password.
    
    Requires the current password for verification.
    """
    auth_service = AuthenticationService(session)
    success = await auth_service.change_password(
        user_id=current_user.id,
        current_password=request.current_password,
        new_password=request.new_password,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    
    return {"message": "Password changed successfully"}


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get the current authenticated user's information."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.name if current_user.role else None,
        "last_login_at": current_user.last_login_at,
    }
