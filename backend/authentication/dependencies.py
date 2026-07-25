"""
Authentication Dependencies
============================

FastAPI dependencies for authentication and authorization.
Used in route handlers to enforce access control.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.authentication.jwt_handler import JWTHandler, TokenPayload
from backend.database.session import get_session
from backend.models.user import User
from backend.repositories.user_repository import UserRepository

logger = logging.getLogger("security")

# HTTP Bearer token extraction
security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    FastAPI dependency to get the authenticated user.
    
    Extracts and validates the JWT from the Authorization header,
    then loads the corresponding user from the database.
    
    Args:
        credentials: Bearer token from request header.
        session: Database session.
    
    Returns:
        User: The authenticated user.
    
    Raises:
        HTTPException: 401 if not authenticated.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    jwt_handler = JWTHandler()
    payload = jwt_handler.decode_token(credentials.credentials)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(payload.sub)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked",
        )
    
    return user


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Dependency that ensures the user is active."""
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return user


def require_role(*allowed_roles: str):
    """
    Factory for role-based access control dependency.
    
    Usage:
        @router.get("/admin", dependencies=[Depends(require_role("admin"))])
        async def admin_endpoint(): ...
    
    Args:
        allowed_roles: Role names that are allowed access.
    
    Returns:
        FastAPI dependency function.
    """
    async def role_checker(
        user: User = Depends(get_current_user),
    ) -> User:
        if not user.role or user.role.name not in allowed_roles:
            logger.warning(
                "Access denied: insufficient role",
                extra={
                    "username": user.username,
                    "user_role": user.role.name if user.role else None,
                    "required_roles": list(allowed_roles),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user
    
    return role_checker


def require_permission(resource: str, action: str):
    """
    Factory for permission-based access control dependency.
    
    Usage:
        @router.post("/servers", dependencies=[Depends(require_permission("servers", "write"))])
    
    Args:
        resource: Resource name (servers, profiles, etc.).
        action: Action name (read, write, delete, execute).
    
    Returns:
        FastAPI dependency function.
    """
    async def permission_checker(
        user: User = Depends(get_current_user),
    ) -> User:
        if not user.role or not user.role.role_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No permissions assigned",
            )
        
        # Check if user's role has the required permission
        has_permission = any(
            rp.permission.resource == resource
            and rp.permission.action == action
            for rp in user.role.role_permissions
        )
        
        if not has_permission:
            logger.warning(
                "Access denied: missing permission",
                extra={
                    "username": user.username,
                    "resource": resource,
                    "action": action,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {resource}.{action}",
            )
        
        return user
    
    return permission_checker
