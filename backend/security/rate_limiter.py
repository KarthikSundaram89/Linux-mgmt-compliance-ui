"""
Rate Limiting
=============

Token bucket rate limiter for API endpoint protection.
Prevents brute-force attacks and abuse.
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


@dataclass
class TokenBucket:
    """Token bucket for a single client."""
    tokens: float
    last_refill: float
    max_tokens: int
    refill_rate: float  # tokens per second


class RateLimiter:
    """
    In-memory token bucket rate limiter.

    Configurable per-endpoint rate limits.
    For production scale, replace with Redis-backed limiter.
    """

    def __init__(
        self,
        default_rate: int = 60,
        default_period: int = 60,
        login_rate: int = 5,
        login_period: int = 60,
    ):
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = asyncio.Lock()
        self._default_rate = default_rate
        self._default_period = default_period
        self._login_rate = login_rate
        self._login_period = login_period

    def _get_rate_for_path(self, path: str) -> Tuple[int, int]:
        """Get rate limit for a specific path."""
        if "/auth/login" in path:
            return self._login_rate, self._login_period
        if "/auth/refresh" in path:
            return 10, 60
        if "/bulk/" in path:
            return 10, 60
        if "/reports/generate" in path:
            return 5, 60
        return self._default_rate, self._default_period

    async def is_allowed(
        self, client_id: str, path: str
    ) -> Tuple[bool, Dict[str, str]]:
        """
        Check if a request is allowed under rate limits.

        Returns:
            Tuple of (allowed, headers_dict).
        """
        rate, period = self._get_rate_for_path(path)
        refill_rate = rate / period
        now = time.time()

        async with self._lock:
            bucket = self._buckets.get(client_id)

            if bucket is None:
                bucket = TokenBucket(
                    tokens=rate,
                    last_refill=now,
                    max_tokens=rate,
                    refill_rate=refill_rate,
                )
                self._buckets[client_id] = bucket

            # Refill tokens
            elapsed = now - bucket.last_refill
            bucket.tokens = min(
                bucket.max_tokens,
                bucket.tokens + elapsed * bucket.refill_rate,
            )
            bucket.last_refill = now

            headers = {
                "X-RateLimit-Limit": str(rate),
                "X-RateLimit-Remaining": str(int(bucket.tokens)),
                "X-RateLimit-Reset": str(int(now + period)),
            }

            if bucket.tokens >= 1:
                bucket.tokens -= 1
                return True, headers
            else:
                retry_after = int((1 - bucket.tokens) / bucket.refill_rate)
                headers["Retry-After"] = str(retry_after)
                return False, headers

    async def cleanup_expired(self) -> None:
        """Remove stale bucket entries (older than 5 minutes)."""
        now = time.time()
        async with self._lock:
            expired = [
                k for k, v in self._buckets.items()
                if now - v.last_refill > 300
            ]
            for key in expired:
                del self._buckets[key]


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that enforces rate limiting.

    Identifies clients by IP address.
    Returns 429 Too Many Requests when limit is exceeded.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip rate limiting for health checks
        if request.url.path.startswith("/api/v1/health"):
            return await call_next(request)

        # Client identification
        client_ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        client_id = f"{client_ip}:{request.url.path}"

        allowed, headers = await rate_limiter.is_allowed(
            client_id, request.url.path
        )

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please retry later.",
                    "retry_after": headers.get("Retry-After", "60"),
                },
                headers=headers,
            )

        response = await call_next(request)

        # Add rate limit headers to response
        for key, value in headers.items():
            response.headers[key] = value

        return response
