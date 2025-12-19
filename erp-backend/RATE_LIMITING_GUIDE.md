# Rate Limiting Implementation Guide

## Overview

This document describes the implementation of rate limiting on all public-facing HR endpoints using FastAPI middleware.

## Features

✅ **Flexible Rate Limiting** - Configurable limits per endpoint  
✅ **Multiple Backends** - In-memory (development) and Redis (production)  
✅ **Sliding Window Algorithm** - Accurate request counting  
✅ **IP-Based Limiting** - Default rate limiting by client IP  
✅ **User-Based Limiting** - Optional rate limiting by authenticated user  
✅ **Tenant-Based Limiting** - Optional rate limiting by tenant  
✅ **Rate Limit Headers** - Standard X-RateLimit-* headers  
✅ **Graceful Degradation** - Continues on rate limiter errors  
✅ **Path Exemptions** - Exclude specific paths from rate limiting  

## Architecture

```
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│  Rate Limit Middleware      │
│  - Extract client identifier│
│  - Check rate limit         │
│  - Update counter           │
│  - Add headers              │
└──────┬──────────────────────┘
       │
       ├─── Allowed ───────────► Continue to endpoint
       │
       └─── Exceeded ─────────► 429 Too Many Requests
```

## Rate Limiting Middleware

### RateLimitMiddleware Class

**Features:**
- Configurable default limits
- Route-specific limits
- Multiple key generation strategies
- Redis or in-memory backend
- Automatic header injection

**Configuration:**
```python
rate_limiter = RateLimitMiddleware(
    app=app.router,
    default_limit=100,  # 100 requests
    default_window=60,  # per 60 seconds
    exempt_paths=["/health", "/docs"],
    use_redis=False  # Use in-memory for development
)
```

### Rate Limit Algorithms

#### In-Memory (Development)
```python
class InMemoryRateLimiter:
    - Uses Python dictionary
    - Sliding window algorithm
    - Automatic cleanup of old timestamps
    - Thread-safe operations
```

#### Redis (Production)
```python
class RedisRateLimiter:
    - Uses Redis sorted sets
    - Distributed rate limiting
    - Automatic expiration
    - High performance
```

## HR Endpoint Rate Limits

### Public Endpoints (No Authentication Required)

#### 1. Employee Directory
```
GET /api/hr/employees/public/directory
Rate Limit: 10 requests per minute
```

**Purpose:** Prevent scraping of employee directory  
**Key:** Client IP address  
**Window:** 60 seconds  

**Response Headers:**
```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1703001234
```

#### 2. Employee Info
```
GET /api/hr/employees/public/{employee_id}
Rate Limit: 20 requests per minute
```

**Purpose:** Prevent excessive lookups  
**Key:** Client IP address  
**Window:** 60 seconds  

#### 3. Contact Employee
```
POST /api/hr/employees/public/contact
Rate Limit: 5 requests per hour
```

**Purpose:** Prevent spam/abuse  
**Key:** Client IP address  
**Window:** 3600 seconds (1 hour)  

**Heavily rate-limited due to:**
- Potential for spam
- Email sending costs
- Employee privacy

### Protected Endpoints (Authentication Required)

Protected endpoints use the default rate limit:
- **100 requests per minute** per user
- Based on authenticated user ID
- Higher limits for trusted users

## Configuration

### Environment Variables

```bash
# Rate Limiting Configuration
RATE_LIMIT_ENABLED=True
RATE_LIMIT_DEFAULT_REQUESTS=100
RATE_LIMIT_DEFAULT_WINDOW=60
RATE_LIMIT_USE_REDIS=False

# HR Public Endpoint Rate Limits
RATE_LIMIT_HR_PUBLIC_DIRECTORY=10
RATE_LIMIT_HR_PUBLIC_INFO=20
RATE_LIMIT_HR_PUBLIC_CONTACT=5
```

### Application Config

```python
class Settings(BaseSettings):
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT_REQUESTS: int = 100
    RATE_LIMIT_DEFAULT_WINDOW: int = 60
    RATE_LIMIT_USE_REDIS: bool = False
    
    # HR Specific
    RATE_LIMIT_HR_PUBLIC_DIRECTORY: int = 10
    RATE_LIMIT_HR_PUBLIC_INFO: int = 20
    RATE_LIMIT_HR_PUBLIC_CONTACT: int = 5
```

## Usage Examples

### Adding Route-Specific Limits

```python
# In main.py
rate_limiter.add_route_limit(
    path_pattern="/api/hr/employees/public/directory",
    requests=10,  # 10 requests
    window=60,  # per minute
    key_func=None  # Use default IP-based key
)

rate_limiter.add_route_limit(
    path_pattern="/api/hr/employees/public/contact",
    requests=5,  # 5 requests
    window=3600,  # per hour
    key_func=None
)
```

### Custom Key Functions

```python
# User-based rate limiting
def get_user_key(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"rate_limit:user:{user_id}"
    return f"rate_limit:ip:{request.client.host}"

# Tenant-based rate limiting
def get_tenant_key(request: Request) -> str:
    tenant_id = request.headers.get("X-Tenant-ID")
    if tenant_id:
        return f"rate_limit:tenant:{tenant_id}"
    return f"rate_limit:ip:{request.client.host}"

# Apply custom key function
rate_limiter.add_route_limit(
    "/api/hr/employees",
    requests=50,
    window=60,
    key_func=get_user_key  # Use user-based key
)
```

## Response Headers

### Standard Rate Limit Headers

```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1703001234
```

**Header Descriptions:**
- `X-RateLimit-Limit` - Maximum requests allowed in window
- `X-RateLimit-Remaining` - Requests remaining in current window
- `X-RateLimit-Reset` - Unix timestamp when limit resets

### Rate Limit Exceeded Response

**Status Code:** `429 Too Many Requests`

**Headers:**
```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1703001234
Retry-After: 45
```

**Body:**
```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

## Testing

### Test Rate Limiting

```python
import pytest
from fastapi.testclient import TestClient

def test_rate_limit_public_directory():
    client = TestClient(app)
    
    # Make 10 requests (should succeed)
    for i in range(10):
        response = client.get(
            "/api/hr/employees/public/directory",
            headers={"X-Tenant-ID": "tenant-1"}
        )
        assert response.status_code == 200
        assert "X-RateLimit-Remaining" in response.headers
    
    # 11th request should be rate limited
    response = client.get(
        "/api/hr/employees/public/directory",
        headers={"X-Tenant-ID": "tenant-1"}
    )
    assert response.status_code == 429
    assert "Retry-After" in response.headers
```

### Test with Different IPs

```python
def test_rate_limit_per_ip():
    client = TestClient(app)
    
    # IP 1 - 10 requests
    for i in range(10):
        response = client.get(
            "/api/hr/employees/public/directory",
            headers={"X-Forwarded-For": "192.168.1.1"}
        )
        assert response.status_code == 200
    
    # IP 1 - 11th request (rate limited)
    response = client.get(
        "/api/hr/employees/public/directory",
        headers={"X-Forwarded-For": "192.168.1.1"}
    )
    assert response.status_code == 429
    
    # IP 2 - Should still work
    response = client.get(
        "/api/hr/employees/public/directory",
        headers={"X-Forwarded-For": "192.168.1.2"}
    )
    assert response.status_code == 200
```

## Production Deployment

### Using Redis Backend

```python
import redis.asyncio as redis

# Create Redis client
redis_client = redis.from_url(
    "redis://localhost:6379/0",
    encoding="utf-8",
    decode_responses=True
)

# Configure rate limiter with Redis
rate_limiter = RateLimitMiddleware(
    app=app.router,
    default_limit=100,
    default_window=60,
    use_redis=True,
    redis_client=redis_client
)
```

### Distributed Rate Limiting

With Redis backend, rate limiting works across multiple application instances:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   App 1     │     │   App 2     │     │   App 3     │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    Redis    │
                    │ (Shared)    │
                    └─────────────┘
```

## Monitoring

### Log Rate Limit Events

```python
# Middleware logs all rate limit events
logger.warning(
    f"Rate limit exceeded for {key} on {path}. "
    f"Limit: {requests}/{window}s"
)
```

### Metrics to Track

1. **Rate limit hits** - Number of 429 responses
2. **Top limited IPs** - IPs hitting limits most often
3. **Endpoint usage** - Requests per endpoint
4. **Window utilization** - Average requests per window

### Example Monitoring Query

```python
# Count rate limit hits per hour
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as rate_limit_hits
FROM logs
WHERE status_code = 429
GROUP BY hour
ORDER BY hour DESC;
```

## Best Practices

1. **Set Appropriate Limits** - Balance security and usability
2. **Use Redis in Production** - For distributed systems
3. **Monitor Rate Limits** - Track abuse patterns
4. **Exempt Health Checks** - Don't rate limit monitoring
5. **Clear Error Messages** - Help users understand limits
6. **Include Retry-After** - Tell users when to retry
7. **Log Violations** - Track potential abuse
8. **Adjust Based on Usage** - Monitor and tune limits
9. **Different Limits for Different Endpoints** - Sensitive endpoints get stricter limits
10. **Consider User Tiers** - Premium users get higher limits

## Security Considerations

### IP Spoofing Prevention

```python
# Use X-Forwarded-For with caution
forwarded = request.headers.get("X-Forwarded-For")
if forwarded:
    # Take first IP (client IP)
    client_ip = forwarded.split(",")[0].strip()
else:
    client_ip = request.client.host
```

### Rate Limit Bypass Prevention

- Don't expose rate limit implementation details
- Use cryptographic hashing for keys
- Implement IP allowlisting for trusted sources
- Monitor for distributed attacks

### DDoS Protection

Rate limiting is one layer of DDoS protection:
- Use CDN (Cloudflare, AWS CloudFront)
- Implement connection limits
- Use WAF (Web Application Firewall)
- Monitor traffic patterns

## Troubleshooting

### Issue: Rate limits too strict
**Solution:** Increase limits or window size

### Issue: Legitimate users getting blocked
**Solution:** Implement user-based rate limiting with higher limits for authenticated users

### Issue: Rate limiting not working
**Solution:** Check middleware order - rate limiting should be early in the chain

### Issue: Redis connection errors
**Solution:** Implement fallback to in-memory rate limiting

## Next Steps

1. ✅ Implement user-tier based rate limiting
2. ✅ Add rate limit dashboard
3. ✅ Implement rate limit bypass for admins
4. ✅ Add rate limit analytics
5. ✅ Implement dynamic rate limit adjustment
6. ✅ Add IP allowlist/blocklist
7. ✅ Implement CAPTCHA for repeated violations
