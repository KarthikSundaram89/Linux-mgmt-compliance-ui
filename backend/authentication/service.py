"""
Authentication Service
======================

Handles user login, token refresh, and password management.
Supports pluggable authentication providers.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from backend.authentication.jwt_handler import JWTHandler, TokenResponse
from backend.models.user import User
from backend.repositories.user_repository import UserRepository

logger = logging.getLogger("security")

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthenticationService:
    """
    Service layer for authentication operations.
    
    Handles:
    - Local username/password authentication
    - Password hashing and verification
    - Token creation and refresh
    - Account lockout after failed attempts
    - Login audit logging
    """
    
    MAX_FAILED_ATTEMPTS = 5
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self._user_repo = UserRepository(session)
        self._jwt = JWTHandler()
    
    async def authenticate(
        self,
        username: str,
        password: str,
    ) -> Optional[TokenResponse]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: Login username.
            password: Plain-text password.
        
        Returns:
            TokenResponse if authentication succeeds, None otherwise.
        """
        user = await self._user_repo.get_by_username(username)
        
        if not user:
            logger.warning(
                "Authentication failed: user not found",
                extra={"username": username},
            )
            return None
        
        # Check if account is locked
        if user.is_locked:
            logger.warning(
                "Authentication failed: account locked",
                extra={"username": username},
            )
            return None
        
        # Check if account is active
        if not user.is_active:
            logger.warning(
                "Authentication failed: account inactive",
                extra={"username": username},
            )
            return None
        
        # Verify password
        if not self._verify_password(password, user.hashed_password):
            await self._handle_failed_login(user)
            return None
        
        # Success - reset failed attempts and update login time
        user.failed_login_attempts = 0
        user.last_login_at = datetime.now(timezone.utc)
        await self._session.flush()
        
        # Get role name
        role_name = user.role.name if user.role else "viewer"
        
        logger.info(
            "Authentication successful",
            extra={"username": username, "role": role_name},
        )
        
        return self._jwt.create_token_response(
            user_id=user.id,
            username=user.username,
            role=role_name,
        )
    
    async def refresh_token(
        self, refresh_token: str
    ) -> Optional[TokenResponse]:
        """
        Create new tokens from a valid refresh token.
        
        Args:
            refresh_token: The JWT refresh token.
        
        Returns:
            New TokenResponse if refresh token is valid, None otherwise.
        """
        payload = self._jwt.decode_token(refresh_token)
        
        if not payload or payload.token_type != "refresh":
            return None
        
        # Verify user still exists and is active
        user = await self._user_repo.get_by_id(payload.sub)
        if not user or not user.is_active or user.is_locked:
            return None
        
        role_name = user.role.name if user.role else "viewer"
        
        return self._jwt.create_token_response(
            user_id=user.id,
            username=user.username,
            role=role_name,
        )
    
    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> bool:
        """
        Change a user's password.
        
        Args:
            user_id: The user's ID.
            current_password: Current password for verification.
            new_password: New password to set.
        
        Returns:
            bool: True if password was changed successfully.
        """
        user = await self._user_repo.get_by_id(user_id)
        
        if not user:
            return False
        
        if not self._verify_password(
            current_password, user.hashed_password
        ):
            return False
        
        user.hashed_password = self._hash_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        await self._session.flush()
        
        logger.info(
            "Password changed",
            extra={"user_id": user_id},
        )
        return True
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash a plain-text password using bcrypt."""
        return pwd_context.hash(password)
    
    @staticmethod
    def _verify_password(
        plain_password: str, hashed_password: Optional[str]
    ) -> bool:
        """Verify a plain-text password against a hash."""
        if not hashed_password:
            return False
        return pwd_context.verify(plain_password, hashed_password)
    
    async def _handle_failed_login(self, user: User) -> None:
        """Increment failed login counter and lock if threshold reached."""
        user.failed_login_attempts += 1
        
        if user.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
            user.is_locked = True
            logger.warning(
                "Account locked due to too many failed attempts",
                extra={
                    "username": user.username,
                    "attempts": user.failed_login_attempts,
                },
            )
        
        await self._session.flush()
    
    @classmethod
    async def create_user(
        cls,
        session: AsyncSession,
        username: str,
        email: str,
        full_name: str,
        password: str,
        role_id: Optional[str] = None,
    ) -> User:
        """
        Create a new user account.
        
        Args:
            session: Database session.
            username: Unique username.
            email: User email.
            full_name: Display name.
            password: Plain-text password (will be hashed).
            role_id: Optional role to assign.
        
        Returns:
            User: Created user instance.
        """
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=pwd_context.hash(password),
            role_id=role_id,
            auth_provider="local",
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)
        return user
