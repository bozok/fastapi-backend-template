"""
Rate limiting configuration and utilities for the FastAPI application.

This module provides:
- IP-based rate limiting using SlowAPI
- Redis backend for distributed rate limiting
- Multiple rate limiting tiers for different endpoint types
- Custom rate limit exceeded handlers
- Rate limiting middleware setup
"""

import logging
from typing import Callable

from fastapi import Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request, handling proxy headers.

    Priority order:
    1. X-Forwarded-For (proxy/load balancer)
    2. X-Real-IP (nginx proxy)
    3. X-Client-IP (some CDNs)
    4. Remote address (direct connection)
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        client_ip = forwarded_for.split(",")[0].strip()
        return client_ip

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    client_ip = request.headers.get("X-Client-IP")
    if client_ip:
        return client_ip.strip()

    # Fallback to direct connection IP
    return get_remote_address(request)


def get_api_key_or_ip(request: Request) -> str:
    """
    Get rate limiting key based on API key or IP address.
    If API key is present, use it for rate limiting, otherwise use IP.
    This allows for user-specific rate limits vs anonymous IP limits.
    """
    # Check for API key in headers
    api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")
    if api_key:
        # Hash the API key for privacy in storage
        import hashlib

        return f"api_key:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"

    # Fallback to IP-based limiting
    return f"ip:{get_client_ip(request)}"


def create_limiter() -> Limiter:
    """
    Create and configure the rate limiter instance.

    Uses Redis if configured, otherwise falls back to in-memory storage.
    """
    storage_uri = None

    # Configure Redis backend if available
    if hasattr(settings, "REDIS_URL") and settings.REDIS_URL:
        storage_uri = settings.REDIS_URL
        logger.info("Rate limiter using Redis backend")
    elif hasattr(settings, "REDIS_HOST") and settings.REDIS_HOST:
        redis_port = getattr(settings, "REDIS_PORT", 6379)
        redis_db = getattr(settings, "REDIS_DB", 0)
        redis_password = getattr(settings, "REDIS_PASSWORD", None)

        if redis_password:
            storage_uri = f"redis://:{redis_password}@{settings.REDIS_HOST}:{redis_port}/{redis_db}"
        else:
            storage_uri = f"redis://{settings.REDIS_HOST}:{redis_port}/{redis_db}"
        logger.info("Rate limiter using Redis backend")
    else:
        logger.warning(
            "Rate limiter using in-memory storage (not recommended for production)"
        )

    return Limiter(
        key_func=get_api_key_or_ip,
        storage_uri=storage_uri,
        enabled=getattr(settings, "ENABLE_RATE_LIMITING", True),
        default_limits=[],  # We'll define limits per endpoint
    )


def custom_rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors.

    Returns a professional JSON response with rate limit information.
    """
    response = JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": f"Rate limit exceeded: {exc.detail}",
            "type": "rate_limit_exceeded",
            "retry_after": getattr(exc, "retry_after", None),
            "limit": str(exc.limit),
            "window": str(exc.limit.get_window_stats()[0])
            if hasattr(exc.limit, "get_window_stats")
            else None,
        },
    )

    # Add rate limit headers
    if hasattr(exc, "retry_after") and exc.retry_after:
        response.headers["Retry-After"] = str(exc.retry_after)

    response.headers["X-RateLimit-Limit"] = str(exc.limit)

    # Log the rate limit violation for monitoring
    client_ip = get_client_ip(request)
    logger.warning(
        f"Rate limit exceeded for {client_ip} on {request.url.path}",
        extra={
            "client_ip": client_ip,
            "path": request.url.path,
            "method": request.method,
            "limit": str(exc.limit),
            "user_agent": request.headers.get("User-Agent", "Unknown"),
        },
    )

    return response


# Rate limiting tiers for different types of endpoints
class RateLimitTiers:
    """
    Predefined rate limiting tiers for different endpoint categories.
    """

    # Public endpoints - more restrictive
    PUBLIC_READ = "10/minute"  # General public read operations
    PUBLIC_SEARCH = "10/minute"  # Search operations (potentially expensive)

    # Authenticated users - more generous
    AUTHENTICATED_READ = "100/minute"  # Authenticated read operations
    AUTHENTICATED_WRITE = "50/minute"  # Write operations

    # Admin/internal - very generous
    ADMIN_OPERATIONS = "500/minute"  # Admin operations

    # Burst protection - very short windows for abuse prevention
    BURST_PROTECTION = "10/second"  # Burst protection

    # Heavy operations - specific limits
    BULK_OPERATIONS = "5/minute"  # Bulk data operations
    EXPORT_OPERATIONS = "3/minute"  # Data export operations


# Create the global limiter instance
limiter = create_limiter()


def rate_limit_by_tier(tier: str) -> Callable:
    """
    Decorator factory for applying rate limits by tier.

    Args:
        tier: Rate limit string (e.g., "10/minute")

    Returns:
        Decorator function
    """
    return limiter.limit(tier)


def get_rate_limit_status(request: Request) -> dict:
    """
    Get current rate limit status for the requesting client.

    Returns information about remaining requests and reset time.
    """
    try:
        key = get_api_key_or_ip(request)
        # This would require access to the limiter's storage
        # Implementation depends on the storage backend used
        return {
            "key": key,
            "client_ip": get_client_ip(request),
            "message": "Rate limit status check - implementation depends on storage backend",
        }
    except Exception as e:
        logger.error(f"Error getting rate limit status: {e}")
        return {"error": "Unable to retrieve rate limit status"}
