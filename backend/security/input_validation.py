"""
Input Validation & Sanitization
================================

Centralized input validation utilities for API security.
Prevents injection attacks, oversized payloads, and malformed input.
"""

import re
from typing import Optional

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


# ─── Validation Constants ──────────────────────────────────────────────────

# Maximum request body size (10 MB)
MAX_REQUEST_BODY_BYTES = 10 * 1024 * 1024

# Maximum JSON depth
MAX_JSON_DEPTH = 10

# Patterns that indicate injection attempts
INJECTION_PATTERNS = [
    re.compile(r"<script", re.IGNORECASE),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),  # onclick=, onerror=, etc.
    re.compile(r"&#x?[0-9a-f]+;", re.IGNORECASE),  # HTML entities
]

# Valid hostname pattern
HOSTNAME_PATTERN = re.compile(
    r"^[a-zA-Z0-9]([a-zA-Z0-9\-\.]{0,253}[a-zA-Z0-9])?$"
)

# Valid IP address pattern (IPv4)
IPV4_PATTERN = re.compile(
    r"^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$"
)

# Valid username pattern
USERNAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_\-\.]{2,99}$")

# Valid UUID pattern
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

# Allowed sort fields (prevent SQL injection via ORDER BY)
ALLOWED_SORT_FIELDS = frozenset([
    "hostname", "ip_address", "os_family", "os_version",
    "environment", "created_at", "updated_at",
    "last_collection_at", "last_collection_status",
    "username", "email", "full_name",
    "timestamp", "action", "severity",
    "detected_at", "category", "change_type",
    "name", "status", "started_at", "completed_at",
])


# ─── Validation Functions ──────────────────────────────────────────────────

def validate_hostname(value: str) -> str:
    """Validate a hostname string."""
    if not value or len(value) > 255:
        raise ValueError("Invalid hostname length")
    if not HOSTNAME_PATTERN.match(value):
        raise ValueError(f"Invalid hostname format: {value[:50]}")
    return value


def validate_ip_address(value: str) -> str:
    """Validate an IPv4 address."""
    if not IPV4_PATTERN.match(value):
        raise ValueError(f"Invalid IP address: {value[:50]}")
    return value


def validate_username(value: str) -> str:
    """Validate a username string."""
    if not USERNAME_PATTERN.match(value):
        raise ValueError(
            "Username must start with a letter and contain "
            "only alphanumeric, underscore, hyphen, dot (3-100 chars)"
        )
    return value


def validate_uuid(value: str) -> str:
    """Validate a UUID string."""
    if not UUID_PATTERN.match(value):
        raise ValueError(f"Invalid UUID format: {value[:50]}")
    return value


def validate_sort_field(value: str) -> str:
    """Validate a sort field against the allowlist."""
    if value not in ALLOWED_SORT_FIELDS:
        raise ValueError(
            f"Invalid sort field: {value}. "
            f"Allowed: {sorted(ALLOWED_SORT_FIELDS)}"
        )
    return value


def sanitize_string(value: str, max_length: int = 500) -> str:
    """
    Sanitize a string input.

    - Strips leading/trailing whitespace
    - Truncates to max_length
    - Checks for injection patterns
    """
    if not value:
        return value

    value = value.strip()[:max_length]

    for pattern in INJECTION_PATTERNS:
        if pattern.search(value):
            raise ValueError(
                "Input contains potentially unsafe content"
            )

    return value


def validate_pagination(
    page: int, page_size: int, max_page_size: int = 100
) -> tuple:
    """Validate pagination parameters."""
    if page < 1:
        raise ValueError("Page must be >= 1")
    if page_size < 1 or page_size > max_page_size:
        raise ValueError(
            f"Page size must be 1-{max_page_size}"
        )
    return page, page_size


# ─── Request Size Middleware ───────────────────────────────────────────────

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Rejects requests exceeding the maximum body size.

    Prevents denial-of-service via oversized payloads.
    """

    def __init__(self, app, max_size: int = MAX_REQUEST_BODY_BYTES):
        super().__init__(app)
        self._max_size = max_size

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Check Content-Length header
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self._max_size:
            return Response(
                content='{"detail": "Request body too large"}',
                status_code=413,
                media_type="application/json",
            )

        return await call_next(request)
