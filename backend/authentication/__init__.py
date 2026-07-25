"""
Authentication Module
=====================

Handles user authentication with pluggable providers.
Initially supports local authentication.
Designed for future Azure AD, LDAP, and AWS SSO integration.
"""

from backend.authentication.service import AuthenticationService
from backend.authentication.jwt_handler import JWTHandler

__all__ = ["AuthenticationService", "JWTHandler"]
