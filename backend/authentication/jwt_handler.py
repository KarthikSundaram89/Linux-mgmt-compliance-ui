"""
JWT Token Handler
=================

Creates and validates JSON Web Tokens for session management.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from pydantic import BaseModel

from backend.settings.config import get_settings


class TokenPayload(BaseModel):
    """JWT token payload schema."""
    
    sub: str  # User ID
    username: str
    role: str
    exp: datetime
    iat: datetime
    token_type: str = "access"


class TokenResponse(BaseModel):
    """Token response returned to the client."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class JWTHandler:
    """
    Handles JWT creation and validation.
    
    Generates access tokens and refresh tokens with
    configurable expiration times.
    """
    
    def __init__(self):
        settings = get_settings()
        self._secret_key = settings.secret_key
        self._algorithm = settings.jwt_algorithm
        self._access_expire_minutes = settings.jwt_expiration_minutes
        self._refresh_expire_days = settings.jwt_refresh_expiration_days
    
    def create_access_token(
        self,
        user_id: str,
        username: str,
        role: str,
    ) -> str:
        """
        Create a signed JWT access token.
        
        Args:
            user_id: The user's unique identifier.
            username: The user's login name.
            role: The user's role name.
        
        Returns:
            str: Encoded JWT access token.
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self._access_expire_minutes)
        
        payload = {
            "sub": user_id,
            "username": username,
            "role": role,
            "exp": expire,
            "iat": now,
            "token_type": "access",
        }
        
        return jwt.encode(
            payload, self._secret_key, algorithm=self._algorithm
        )
    
    def create_refresh_token(
        self,
        user_id: str,
        username: str,
        role: str,
    ) -> str:
        """
        Create a signed JWT refresh token.
        
        Args:
            user_id: The user's unique identifier.
            username: The user's login name.
            role: The user's role name.
        
        Returns:
            str: Encoded JWT refresh token.
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self._refresh_expire_days)
        
        payload = {
            "sub": user_id,
            "username": username,
            "role": role,
            "exp": expire,
            "iat": now,
            "token_type": "refresh",
        }
        
        return jwt.encode(
            payload, self._secret_key, algorithm=self._algorithm
        )
    
    def create_token_response(
        self,
        user_id: str,
        username: str,
        role: str,
    ) -> TokenResponse:
        """
        Create a complete token response with access and refresh tokens.
        
        Args:
            user_id: User identifier.
            username: User login name.
            role: User role name.
        
        Returns:
            TokenResponse: Access token, refresh token, and metadata.
        """
        access_token = self.create_access_token(user_id, username, role)
        refresh_token = self.create_refresh_token(user_id, username, role)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self._access_expire_minutes * 60,
        )
    
    def decode_token(self, token: str) -> Optional[TokenPayload]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: The encoded JWT string.
        
        Returns:
            TokenPayload if valid, None if invalid/expired.
        """
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
            )
            return TokenPayload(**payload)
        except JWTError:
            return None
    
    def verify_token(self, token: str) -> bool:
        """
        Verify a token is valid and not expired.
        
        Args:
            token: The encoded JWT string.
        
        Returns:
            bool: True if the token is valid.
        """
        return self.decode_token(token) is not None
