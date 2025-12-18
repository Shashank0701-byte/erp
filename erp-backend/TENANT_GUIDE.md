# Tenant ID Extraction and Multi-Tenancy Implementation Guide

## Overview

This ERP system implements comprehensive multi-tenancy support with automatic tenant ID extraction and context injection. Every request carries the correct tenant context, ensuring complete data isolation between tenants.

## Features

✅ **Multiple Extraction Strategies** - Header, subdomain, URL path, JWT token  
✅ **Automatic Validation** - Verify tenant exists and is active  
✅ **Dependency Injection** - Easy access to tenant context in routes  
✅ **Middleware Support** - Automatic tenant context attachment  
✅ **Database Isolation** - Ensure queries are scoped to tenant  
✅ **Flexible Configuration** - Support various deployment models  
✅ **Security** - Prevent cross-tenant data access  

## Tenant Extraction Strategies

The system supports four strategies for extracting tenant ID from requests, tried in priority order:

### 1. Custom Header (Highest Priority)

**Recommended for API clients and mobile apps**

```http
GET /api/users HTTP/1.1
Host: api.erp.com
X-Tenant-ID: tenant-1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Pros:**
- Simple and explicit
- Works with any domain
- Easy to implement in clients

**Cons:**
- Requires client to send header
- Can be forgotten by developers

### 2. Subdomain

**Recommended for web applications**

```http
GET /api/users HTTP/1.1
Host: tenant1.erp.com
```

Extracts `tenant1` from `tenant1.erp.com`

**Pros:**
- Automatic extraction
- User-friendly URLs
- Natural tenant separation

**Cons:**
- Requires DNS configuration
- SSL certificate management

### 3. URL Path

**Alternative for shared domains**

```http
GET /api/tenant-1/users HTTP/1.1
Host: api.erp.com
```

Extracts `tenant-1` from path

**Pros:**
- Works on shared domains
- Explicit in URL
- No DNS needed

**Cons:**
- Longer URLs
- Can be confusing

### 4. JWT Token Payload

**Automatic from authentication**

```json
{
  "sub": "user-123",
  "email": "user@example.com",
  "role": "admin",
  "tenant_id": "tenant-1"
}
```

**Pros:**
- Automatic from auth
- Secure
- No extra headers needed

**Cons:**
- Requires authentication
- Token must include tenant_id

## Tenant Context Schema

```python
class TenantContext(BaseModel):
    tenant_id: str              # Unique tenant identifier
    tenant_name: str            # Human-readable tenant name
    domain: str                 # Tenant's domain
    is_active: bool             # Whether tenant is active
    settings: Optional[dict]    # Tenant-specific settings
```

## Usage Examples

### Basic Tenant Dependency

```python
from fastapi import APIRouter, Depends
from app.dependencies.tenant import get_tenant_context
from app.schemas.tenant import TenantContext

router = APIRouter()

@router.get("/users")
async def get_users(tenant: TenantContext = Depends(get_tenant_context)):
    """
    Get users for the current tenant
    Tenant context is automatically extracted and validated
    """
    print(f"Request from tenant: {tenant.tenant_name}")
    print(f"Tenant ID: {tenant.tenant_id}")
    print(f"Tenant settings: {tenant.settings}")
    
    # Query users scoped to this tenant
    users = db.query(User).filter(User.tenant_id == tenant.tenant_id).all()
    return users
```

### Optional Tenant Context

```python
from app.dependencies.tenant import get_optional_tenant_context

@router.get("/public-data")
async def get_public_data(
    tenant: Optional[TenantContext] = Depends(get_optional_tenant_context)
):
    """
    Route that works with or without tenant context
    """
    if tenant:
        # Return tenant-specific data
        return {"data": "tenant-specific", "tenant": tenant.tenant_name}
    else:
        # Return public data
        return {"data": "public"}
```

### Require Specific Tenant Setting

```python
from app.dependencies.tenant import require_tenant_setting

@router.get("/advanced-feature")
async def advanced_feature(
    tenant: TenantContext = Depends(require_tenant_setting("advanced_features", True))
):
    """
    Only accessible if tenant has advanced_features enabled
    """
    return {"message": "Advanced feature accessed"}
```

### Combined with Authentication

```python
from app.dependencies import get_current_user
from app.dependencies.tenant import get_tenant_context
from app.schemas import TokenData

@router.post("/finance/entry")
async def create_entry(
    entry_data: dict,
    current_user: TokenData = Depends(get_current_user),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Protected route with both authentication and tenant context
    """
    # Verify user belongs to this tenant
    if current_user.tenant_id != tenant.tenant_id:
        raise HTTPException(status_code=403, detail="User not authorized for this tenant")
    
    # Create entry scoped to tenant
    entry = create_journal_entry(
        data=entry_data,
        tenant_id=tenant.tenant_id,
        created_by=current_user.user_id
    )
    return entry
```

## Middleware Integration

### Add Tenant Middleware

```python
from fastapi import FastAPI
from app.middleware.tenant import TenantMiddleware, TenantIsolationMiddleware

app = FastAPI()

# Add tenant middleware
app.add_middleware(TenantMiddleware)

# Add tenant isolation middleware (for database)
app.add_middleware(TenantIsolationMiddleware)
```

### Middleware Behavior

1. **TenantMiddleware**:
   - Extracts tenant ID from request
   - Stores in `request.state.tenant_id`
   - Adds `X-Tenant-ID` header to response
   - Logs tenant information

2. **TenantIsolationMiddleware**:
   - Enforces database-level tenant isolation
   - Sets session variables for queries
   - Prevents cross-tenant data access

## Client Integration

### JavaScript/TypeScript (Axios)

```typescript
import axios from 'axios';

// Create axios instance with tenant header
const api = axios.create({
  baseURL: 'https://api.erp.com',
  headers: {
    'X-Tenant-ID': 'tenant-1'
  }
});

// Make request
const response = await api.get('/api/users');
```

### Python (Requests)

```python
import requests

headers = {
    'X-Tenant-ID': 'tenant-1',
    'Authorization': 'Bearer <token>'
}

response = requests.get(
    'https://api.erp.com/api/users',
    headers=headers
)
```

### cURL

```bash
curl -H "X-Tenant-ID: tenant-1" \
     -H "Authorization: Bearer <token>" \
     https://api.erp.com/api/users
```

## Database Isolation

### SQLAlchemy Filter

```python
from sqlalchemy.orm import Session
from app.dependencies.tenant import get_tenant_context

@router.get("/users")
async def get_users(
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context)
):
    # All queries automatically filtered by tenant_id
    users = db.query(User).filter(
        User.tenant_id == tenant.tenant_id
    ).all()
    return users
```

### Base Model with Tenant ID

```python
from sqlalchemy import Column, String
from app.database import Base

class TenantMixin:
    """Mixin to add tenant_id to all models"""
    tenant_id = Column(String, nullable=False, index=True)

class User(Base, TenantMixin):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True)
    name = Column(String)
    # tenant_id inherited from TenantMixin
```

### Automatic Tenant Scoping

```python
from sqlalchemy import event
from sqlalchemy.orm import Session

@event.listens_for(Session, "after_attach")
def receive_after_attach(session, instance):
    """Automatically set tenant_id on new instances"""
    if hasattr(instance, 'tenant_id') and not instance.tenant_id:
        # Get tenant from request context
        tenant_id = getattr(session.info.get('request_state'), 'tenant_id', None)
        if tenant_id:
            instance.tenant_id = tenant_id
```

## Tenant Validation

### Mock Validation (Development)

```python
# Current implementation uses mock data
mock_tenants = {
    "tenant-1": {
        "id": "tenant-1",
        "name": "Acme Corporation",
        "domain": "acme.erp.com",
        "is_active": True,
        "settings": {"timezone": "UTC", "currency": "USD"}
    }
}
```

### Database Validation (Production)

```python
async def validate_tenant(tenant_id: str) -> TenantContext:
    """Validate tenant against database"""
    # Query database
    tenant = await db.query(Tenant).filter(
        Tenant.id == tenant_id
    ).first()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    if not tenant.is_active:
        raise HTTPException(status_code=403, detail="Tenant is not active")
    
    return TenantContext(
        tenant_id=tenant.id,
        tenant_name=tenant.name,
        domain=tenant.domain,
        is_active=tenant.is_active,
        settings=tenant.settings
    )
```

## Security Considerations

### 1. Prevent Tenant Spoofing

```python
@router.get("/users")
async def get_users(
    current_user: TokenData = Depends(get_current_user),
    tenant: TenantContext = Depends(get_tenant_context)
):
    # Verify user's tenant matches request tenant
    if current_user.tenant_id != tenant.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="User not authorized for this tenant"
        )
    
    # Proceed with request
    return get_tenant_users(tenant.tenant_id)
```

### 2. Tenant Isolation in Queries

```python
# ALWAYS filter by tenant_id
users = db.query(User).filter(
    User.tenant_id == tenant.tenant_id
).all()

# NEVER query without tenant filter
# users = db.query(User).all()  # ❌ DANGEROUS!
```

### 3. Validate Tenant Access

```python
def verify_resource_access(resource_tenant_id: str, tenant: TenantContext):
    """Verify resource belongs to current tenant"""
    if resource_tenant_id != tenant.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Resource does not belong to this tenant"
        )
```

## Error Handling

### No Tenant ID Provided

```json
{
  "detail": "Tenant ID is required. Provide via X-Tenant-ID header, subdomain, or URL path"
}
```

### Tenant Not Found

```json
{
  "detail": "Tenant 'tenant-123' not found"
}
```

### Inactive Tenant

```json
{
  "detail": "Tenant 'tenant-123' is not active"
}
```

### Missing Tenant Setting

```json
{
  "detail": "Tenant setting 'advanced_features' not configured"
}
```

## Testing

### Test with Different Tenants

```python
import pytest
from fastapi.testclient import TestClient

def test_tenant_isolation():
    client = TestClient(app)
    
    # Create data for tenant-1
    response = client.post(
        "/api/users",
        headers={"X-Tenant-ID": "tenant-1"},
        json={"name": "User 1", "email": "user1@tenant1.com"}
    )
    assert response.status_code == 201
    
    # Try to access from tenant-2
    response = client.get(
        "/api/users",
        headers={"X-Tenant-ID": "tenant-2"}
    )
    # Should not see tenant-1's data
    assert len(response.json()) == 0
```

### Mock Tenant Context

```python
from app.schemas.tenant import TenantContext

def get_mock_tenant():
    return TenantContext(
        tenant_id="test-tenant",
        tenant_name="Test Tenant",
        domain="test.erp.com",
        is_active=True,
        settings={}
    )

# Override dependency in tests
app.dependency_overrides[get_tenant_context] = get_mock_tenant
```

## Best Practices

1. **Always Use Tenant Context** - Never query without tenant filter
2. **Validate Tenant Access** - Verify user belongs to tenant
3. **Use Middleware** - Automatic tenant extraction
4. **Index tenant_id** - Optimize database queries
5. **Log Tenant Operations** - Audit trail per tenant
6. **Test Isolation** - Verify data separation
7. **Document Tenant Strategy** - Clear for team
8. **Handle Missing Tenant** - Graceful error messages
9. **Cache Tenant Data** - Reduce database queries
10. **Monitor Per Tenant** - Track usage and performance

## Configuration

### Environment Variables

```bash
# Tenant configuration
TENANT_EXTRACTION_STRATEGY=header  # header, subdomain, path, jwt
TENANT_VALIDATION_CACHE_TTL=300    # Cache tenant validation for 5 minutes
TENANT_ISOLATION_ENABLED=true      # Enable database isolation
```

## Next Steps

1. ✅ Implement database tenant table
2. ✅ Add tenant creation API
3. ✅ Implement tenant caching
4. ✅ Add tenant usage metrics
5. ✅ Implement tenant-specific rate limiting
6. ✅ Add tenant backup/restore
7. ✅ Implement tenant migration tools
