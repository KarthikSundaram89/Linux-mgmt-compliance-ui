"""
CSRF Protection
===============

Double-submit cookie pattern for CSRF protection.
State-changing requests must include a matching CSRF token.
"""

import secrets
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
SAFE_METHODS = frozenset(["GET", "HEAD", "OPTIONS"])


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection using double-submit cookie pattern.

    - Safe methods (GET, HEAD, OPTIONS) are exempt.
    - API endpoints using Bearer token auth are exempt
      (tokens are not automatically sent by browsers).
    - For cookie-based sessions, the CSRF token in the
      header must match the CSRF cookie.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Safe methods are always allowed
        if request.method in SAFE_METHODS:
            response = await call_next(request)
            # Set CSRF cookie if not present
            if CSRF_COOKIE_NAME not in request.cookies:
                token = secrets.token_urlsafe(32)
                response.set_cookie(
                    key=CSRF_COOKIE_NAME,
                    value=token,
                    httponly=False,  # Must be readable by JS
                    samesite="strict",
                    secure=request.url.scheme == "https",
                    max_age=3600,
                )
            return response

        # Bearer token requests are exempt (not vulnerable to CSRF)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return await call_next(request)

        # For cookie-based auth, validate CSRF token
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        header_token = request.headers.get(CSRF_HEADER_NAME)

        if not cookie_token or not header_token:
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing"},
            )

        if not secrets.compare_digest(cookie_token, header_token):
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token mismatch"},
            )

        response = await call_next(request)

        # Rotate CSRF token after state-changing request
        new_token = secrets.token_urlsafe(32)
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=new_token,
            httponly=False,
            samesite="strict",
            secure=request.url.scheme == "https",
            max_age=3600,
        )

        return response
