"""
Unit tests for rate limiter.
"""

import pytest

from backend.security.rate_limiter import RateLimiter


@pytest.fixture
def limiter():
    return RateLimiter(
        default_rate=5, default_period=60,
        login_rate=3, login_period=60,
    )


@pytest.mark.asyncio
async def test_allows_requests_within_limit(limiter):
    """Requests within rate limit are allowed."""
    for i in range(5):
        allowed, headers = await limiter.is_allowed(
            "client1", "/api/v1/servers"
        )
        assert allowed is True
    assert int(headers["X-RateLimit-Remaining"]) == 0


@pytest.mark.asyncio
async def test_blocks_requests_over_limit(limiter):
    """Requests exceeding rate limit are blocked."""
    for _ in range(5):
        await limiter.is_allowed("client2", "/api/v1/servers")

    allowed, headers = await limiter.is_allowed(
        "client2", "/api/v1/servers"
    )
    assert allowed is False
    assert "Retry-After" in headers


@pytest.mark.asyncio
async def test_login_has_stricter_limit(limiter):
    """Login endpoint has a stricter rate limit."""
    for _ in range(3):
        allowed, _ = await limiter.is_allowed(
            "client3", "/api/v1/auth/login"
        )
        assert allowed is True

    allowed, _ = await limiter.is_allowed(
        "client3", "/api/v1/auth/login"
    )
    assert allowed is False


@pytest.mark.asyncio
async def test_different_clients_independent(limiter):
    """Rate limits are independent per client."""
    for _ in range(5):
        await limiter.is_allowed("clientA", "/api/v1/servers")

    # clientA is exhausted
    allowed_a, _ = await limiter.is_allowed("clientA", "/api/v1/servers")
    assert allowed_a is False

    # clientB still has tokens
    allowed_b, _ = await limiter.is_allowed("clientB", "/api/v1/servers")
    assert allowed_b is True


@pytest.mark.asyncio
async def test_rate_limit_headers_present(limiter):
    """Rate limit headers are included in responses."""
    _, headers = await limiter.is_allowed("client4", "/api/v1/servers")
    assert "X-RateLimit-Limit" in headers
    assert "X-RateLimit-Remaining" in headers
    assert "X-RateLimit-Reset" in headers
