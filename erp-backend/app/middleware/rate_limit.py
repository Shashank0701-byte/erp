"""
Rate Limiting Middleware
Implements rate limiting for API endpoints using Redis backend
"""

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable, Dict, Optional, List
import time
import logging
import hashlib
from app.config import settings

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Rate limit configuration"""
    
    def __init__(
        self,
        requests: int,
        window: int,
        key_func: Optional[Callable] = None
    ):
        """
        Initialize rate limit config
        
        Args:
            requests: Number of requests allowed
            window: Time window in seconds
            key_func: Optional function to generate rate limit key
        """
        self.requests = requests
        self.window = window
        self.key_func = key_func or self._default_key_func
    
    @staticmethod
    def _default_key_func(request: Request) -> str:
        """Default key function using client IP"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        return f"rate_limit:{client_ip}"


class InMemoryRateLimiter:
    """
    In-memory rate limiter (for development/testing)
    Uses sliding window algorithm
    """
    
    def __init__(self):
        self.storage: Dict[str, List[float]] = {}
    
    def is_allowed(self, key: str, limit: int, window: int) -> tuple[bool, Dict[str, int]]:
        """
        Check if request is allowed
        
        Args:
            key: Rate limit key
            limit: Maximum requests allowed
            window: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, info_dict)
        """
        current_time = time.time()
        
        # Initialize or get existing timestamps
        if key not in self.storage:
            self.storage[key] = []
        
        # Remove old timestamps outside the window
        self.storage[key] = [
            ts for ts in self.storage[key]
            if current_time - ts < window
        ]
        
        # Check if limit exceeded
        request_count = len(self.storage[key])
        is_allowed = request_count < limit
        
        if is_allowed:
            self.storage[key].append(current_time)
        
        # Calculate retry after
        if not is_allowed and self.storage[key]:
            oldest_timestamp = min(self.storage[key])
            retry_after = int(window - (current_time - oldest_timestamp)) + 1
        else:
            retry_after = 0
        
        info = {
            "limit": limit,
            "remaining": max(0, limit - request_count - (1 if is_allowed else 0)),
            "reset": int(current_time + window),
            "retry_after": retry_after
        }
        
        return is_allowed, info
    
    def reset(self, key: str):
        """Reset rate limit for a key"""
        if key in self.storage:
            del self.storage[key]


class RedisRateLimiter:
    """
    Redis-based rate limiter (for production)
    Uses sliding window algorithm with Redis sorted sets
    """
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def is_allowed(self, key: str, limit: int, window: int) -> tuple[bool, Dict[str, int]]:
        """
        Check if request is allowed using Redis
        
        Args:
            key: Rate limit key
            limit: Maximum requests allowed
            window: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, info_dict)
        """
        current_time = time.time()
        window_start = current_time - window
        
        # Remove old entries
        await self.redis.zremrangebyscore(key, 0, window_start)
        
        # Count requests in current window
        request_count = await self.redis.zcard(key)
        
        is_allowed = request_count < limit
        
        if is_allowed:
            # Add current request
            await self.redis.zadd(key, {str(current_time): current_time})
            await self.redis.expire(key, window)
        
        # Calculate retry after
        if not is_allowed:
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                oldest_timestamp = oldest[0][1]
                retry_after = int(window - (current_time - oldest_timestamp)) + 1
            else:
                retry_after = window
        else:
            retry_after = 0
        
        info = {
            "limit": limit,
            "remaining": max(0, limit - request_count - (1 if is_allowed else 0)),
            "reset": int(current_time + window),
            "retry_after": retry_after
        }
        
        return is_allowed, info
    
    async def reset(self, key: str):
        """Reset rate limit for a key"""
        await self.redis.delete(key)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for FastAPI
    
    Features:
    - Configurable rate limits per endpoint
    - Multiple rate limit tiers
    - IP-based and user-based rate limiting
    - Redis backend support
    - Detailed rate limit headers
    - Exemption for certain paths
    """
    
    def __init__(
        self,
        app: ASGIApp,
        default_limit: int = 100,
        default_window: int = 60,
        exempt_paths: Optional[List[str]] = None,
        use_redis: bool = False,
        redis_client = None
    ):
        """
        Initialize rate limit middleware
        
        Args:
            app: ASGI application
            default_limit: Default requests per window
            default_window: Default time window in seconds
            exempt_paths: List of paths to exempt from rate limiting
            use_redis: Whether to use Redis backend
            redis_client: Redis client instance
        """
        super().__init__(app)
        self.default_limit = default_limit
        self.default_window = default_window
        self.exempt_paths = exempt_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        
        # Initialize rate limiter
        if use_redis and redis_client:
            self.limiter = RedisRateLimiter(redis_client)
            self.use_async = True
            logger.info("Rate limiter initialized with Redis backend")
        else:
            self.limiter = InMemoryRateLimiter()
            self.use_async = False
            logger.info("Rate limiter initialized with in-memory backend")
        
        # Route-specific rate limits
        self.route_limits: Dict[str, RateLimitConfig] = {}
    
    def add_route_limit(
        self,
        path_pattern: str,
        requests: int,
        window: int,
        key_func: Optional[Callable] = None
    ):
        """
        Add route-specific rate limit
        
        Args:
            path_pattern: Path pattern to match
            requests: Number of requests allowed
            window: Time window in seconds
            key_func: Optional custom key function
        """
        self.route_limits[path_pattern] = RateLimitConfig(requests, window, key_func)
    
    def _get_rate_limit_config(self, path: str) -> RateLimitConfig:
        """Get rate limit config for path"""
        # Check for exact match
        if path in self.route_limits:
            return self.route_limits[path]
        
        # Check for pattern match
        for pattern, config in self.route_limits.items():
            if path.startswith(pattern):
                return config
        
        # Return default
        return RateLimitConfig(self.default_limit, self.default_window)
    
    def _generate_key(self, request: Request, config: RateLimitConfig) -> str:
        """Generate rate limit key"""
        base_key = config.key_func(request)
        
        # Add tenant ID if available
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            base_key = f"{base_key}:tenant:{tenant_id}"
        
        # Add path to key
        path = request.url.path
        key_hash = hashlib.md5(path.encode()).hexdigest()[:8]
        
        return f"{base_key}:path:{key_hash}"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response with rate limit headers
        """
        path = request.url.path
        
        # Skip rate limiting for exempt paths
        if any(path.startswith(exempt) for exempt in self.exempt_paths):
            return await call_next(request)
        
        # Get rate limit config
        config = self._get_rate_limit_config(path)
        
        # Generate rate limit key
        key = self._generate_key(request, config)
        
        # Check rate limit
        try:
            if self.use_async:
                is_allowed, info = await self.limiter.is_allowed(
                    key, config.requests, config.window
                )
            else:
                is_allowed, info = self.limiter.is_allowed(
                    key, config.requests, config.window
                )
        except Exception as e:
            logger.error(f"Rate limiter error: {str(e)}")
            # On error, allow request but log
            return await call_next(request)
        
        # Add rate limit headers
        headers = {
            "X-RateLimit-Limit": str(info["limit"]),
            "X-RateLimit-Remaining": str(info["remaining"]),
            "X-RateLimit-Reset": str(info["reset"])
        }
        
        if not is_allowed:
            # Rate limit exceeded
            headers["Retry-After"] = str(info["retry_after"])
            
            logger.warning(
                f"Rate limit exceeded for {key} on {path}. "
                f"Limit: {config.requests}/{config.window}s"
            )
            
            return Response(
                content='{"detail":"Rate limit exceeded. Please try again later."}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers=headers,
                media_type="application/json"
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        for header, value in headers.items():
            response.headers[header] = value
        
        return response


def get_user_key(request: Request) -> str:
    """
    Generate rate limit key based on authenticated user
    
    Args:
        request: FastAPI request
        
    Returns:
        Rate limit key
    """
    # Try to get user ID from request state (set by auth middleware)
    user_id = getattr(request.state, "user_id", None)
    
    if user_id:
        return f"rate_limit:user:{user_id}"
    
    # Fallback to IP-based key
    return RateLimitConfig._default_key_func(request)


def get_tenant_key(request: Request) -> str:
    """
    Generate rate limit key based on tenant
    
    Args:
        request: FastAPI request
        
    Returns:
        Rate limit key
    """
    tenant_id = request.headers.get("X-Tenant-ID")
    
    if tenant_id:
        return f"rate_limit:tenant:{tenant_id}"
    
    # Fallback to IP-based key
    return RateLimitConfig._default_key_func(request)
