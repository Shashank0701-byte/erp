# JWT Dependency Injection Implementation Guide

## Overview

This document explains the comprehensive JWT (JSON Web Token) dependency injection implementation in FastAPI for secure authentication and authorization.

## Features

✅ **Multiple Token Sources** - Extract tokens from Authorization header, cookies, or query parameters  
✅ **Comprehensive Validation** - Token type, expiration, signature, and payload validation  
✅ **Detailed Logging** - Track authentication attempts and failures  
✅ **Security Best Practices** - Proper error handling and secure defaults  
✅ **RBAC Integration** - Role and permission-based access control  
✅ **Flexible Configuration** - Support for both Bearer tokens and HTTP-only cookies  

## Token Extraction

The `extract_token_from_request()` function extracts JWT tokens from multiple sources with the following priority:

### Priority 1: Authorization Header (Recommended)
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Priority 2: HTTP-Only Cookie
```http
Cookie: auth-token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Priority 3: Query Parameter (Not Recommended for Production)
```http
GET /api/resource?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Token Creation

### Access Token

```python
from app.dependencies import create_access_token

# Create access token
token_data = {
    "sub": "user-123",  # User ID
    "email": "user@example.com",
    "role": "admin"
}

access_token = create_access_token(token_data)
```

**Token Payload:**
```json
{
  "sub": "user-123",
  "email": "user@example.com",
  "role": "admin",
  "exp": 1703001234,
  "iat": 1703000234,
  "type": "access"
}
```

### Refresh Token

```python
from app.dependencies import create_refresh_token

refresh_token = create_refresh_token(token_data)
```

**Token Payload:**
```json
{
  "sub": "user-123",
  "email": "user@example.com",
  "role": "admin",
  "exp": 1705592234,
  "iat": 1703000234,
  "type": "refresh"
}
```

## Token Validation

The `verify_token()` function performs comprehensive validation:

### Validation Steps

1. **Decode JWT** - Verify signature using secret key
2. **Check Token Type** - Ensure it's an access token (not refresh)
3. **Validate Required Fields** - Verify sub, email, and role are present
4. **Validate Role** - Ensure role is a valid UserRole enum value
5. **Check Expiration** - Verify token hasn't expired
6. **Return TokenData** - Create validated TokenData object

### Error Handling

| Error | Status Code | Description |
|-------|-------------|-------------|
| Invalid token type | 401 | Token type doesn't match expected (access/refresh) |
| Missing fields | 401 | Required fields (sub, email, role) are missing |
| Invalid role | 401 | Role is not a valid UserRole enum value |
| Token expired | 401 | Token expiration time has passed |
| Invalid signature | 401 | Token signature verification failed |
| Malformed token | 401 | Token format is invalid |

## Dependency Injection Usage

### Basic Authentication

```python
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.schemas import TokenData

router = APIRouter()

@router.get("/profile")
async def get_profile(current_user: TokenData = Depends(get_current_user)):
    """
    Protected endpoint - requires valid JWT token
    """
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "role": current_user.role
    }
```

### Permission-Based Access

```python
from app.dependencies import require_permission
from app.schemas import Permission

@router.post("/finance/entry")
async def create_journal_entry(
    entry_data: dict,
    current_user: TokenData = Depends(require_permission(Permission.CREATE_FINANCE))
):
    """
    Requires CREATE_FINANCE permission
    """
    return {"message": "Entry created", "created_by": current_user.user_id}
```

### Role-Based Access

```python
from app.dependencies import require_role
from app.schemas import UserRole

@router.get("/admin/dashboard")
async def admin_dashboard(
    current_user: TokenData = Depends(require_role([UserRole.ADMIN]))
):
    """
    Only accessible by ADMIN role
    """
    return {"message": "Admin dashboard"}
```

### Multiple Permissions (ANY)

```python
from app.dependencies import require_any_permission

@router.put("/finance/entry/{id}")
async def update_entry(
    id: str,
    current_user: TokenData = Depends(
        require_any_permission([Permission.EDIT_FINANCE, Permission.APPROVE_FINANCE])
    )
):
    """
    Requires EITHER edit OR approve permission
    """
    return {"message": "Entry updated"}
```

### Multiple Permissions (ALL)

```python
from app.dependencies import require_all_permissions

@router.delete("/finance/entry/{id}")
async def delete_entry(
    id: str,
    current_user: TokenData = Depends(
        require_all_permissions([Permission.DELETE_FINANCE, Permission.APPROVE_FINANCE])
    )
):
    """
    Requires BOTH delete AND approve permissions
    """
    return {"message": "Entry deleted"}
```

## Client Integration

### Using Authorization Header (Recommended)

```javascript
// Frontend example
const response = await fetch('/api/profile', {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
});
```

### Using HTTP-Only Cookies

```javascript
// Frontend example
const response = await fetch('/api/profile', {
  credentials: 'include'  // Include cookies
});
```

## Security Features

### 1. Auto-Error Disabled for Swagger UI

```python
security = HTTPBearer(auto_error=False)
```

This allows optional authentication, enabling Swagger UI to work without tokens while still protecting routes that require authentication.

### 2. Comprehensive Logging

```python
logger.info(f"Token verified successfully for user: {email}")
logger.warning(f"No authentication token found in request to {request.url.path}")
logger.error(f"JWT validation error: {str(e)}")
```

All authentication attempts are logged for security auditing.

### 3. Token Type Validation

```python
if payload.get("type") != token_type:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Invalid token type. Expected {token_type} token"
    )
```

Prevents using refresh tokens as access tokens and vice versa.

### 4. Expiration Checking

```python
if exp_datetime < datetime.utcnow():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has expired"
    )
```

Explicit expiration validation with detailed error messages.

### 5. Role Validation

```python
try:
    user_role = UserRole(role)
except ValueError:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid role in token"
    )
```

Ensures role in token is a valid enum value.

## Testing

### Test Protected Endpoint

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import create_access_token

client = TestClient(app)

def test_protected_endpoint_with_valid_token():
    # Create valid token
    token = create_access_token({
        "sub": "user-123",
        "email": "test@example.com",
        "role": "admin"
    })
    
    # Make request with token
    response = client.get(
        "/api/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

def test_protected_endpoint_without_token():
    response = client.get("/api/profile")
    assert response.status_code == 401
    assert "not authenticated" in response.json()["detail"].lower()

def test_protected_endpoint_with_expired_token():
    from datetime import timedelta
    
    # Create expired token
    token = create_access_token(
        {"sub": "user-123", "email": "test@example.com", "role": "admin"},
        expires_delta=timedelta(seconds=-1)  # Already expired
    )
    
    response = client.get(
        "/api/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()
```

## Configuration

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
```

### Customizing Token Expiration

```python
from datetime import timedelta
from app.dependencies import create_access_token

# Custom expiration (2 hours)
token = create_access_token(
    data={"sub": "user-123", "email": "user@example.com", "role": "admin"},
    expires_delta=timedelta(hours=2)
)
```

## Error Responses

### No Token Provided

```json
{
  "detail": "Not authenticated - no token provided"
}
```

### Invalid Token

```json
{
  "detail": "Could not validate credentials"
}
```

### Expired Token

```json
{
  "detail": "Token has expired"
}
```

### Insufficient Permissions

```json
{
  "detail": "Permission denied. Required permission: create_finance"
}
```

### Insufficient Role

```json
{
  "detail": "Access denied. Required roles: ['admin']"
}
```

## Best Practices

1. **Always use HTTPS in production** - Prevent token interception
2. **Use Authorization header for APIs** - More secure than cookies for APIs
3. **Use HTTP-only cookies for web apps** - Prevent XSS attacks
4. **Avoid query parameters** - Tokens in URLs can be logged
5. **Set appropriate expiration times** - Balance security and UX
6. **Rotate secret keys regularly** - Enhance security
7. **Log authentication failures** - Monitor for attacks
8. **Validate all token claims** - Don't trust client data
9. **Use refresh tokens** - Allow long sessions without compromising security
10. **Implement token revocation** - Handle logout and security incidents

## Troubleshooting

### Issue: "Not authenticated - no token provided"
**Solution**: Ensure token is included in Authorization header or cookie

### Issue: "Token has expired"
**Solution**: Implement token refresh mechanism or re-authenticate

### Issue: "Invalid token type"
**Solution**: Ensure you're using access token, not refresh token

### Issue: "Permission denied"
**Solution**: Check user's role has required permission in ROLE_PERMISSIONS mapping

## Next Steps

1. ✅ Implement token refresh endpoint
2. ✅ Add token blacklist for logout
3. ✅ Implement rate limiting for auth endpoints
4. ✅ Add multi-factor authentication
5. ✅ Implement session management
