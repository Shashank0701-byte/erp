# Journal Entries API - Implementation Guide

## Overview

This document describes the `/journal-entries` POST endpoint implementation using async SQLAlchemy for database write operations.

## Features

✅ **Async SQLAlchemy** - Non-blocking database operations  
✅ **Multi-Tenancy** - Automatic tenant isolation  
✅ **RBAC** - Permission-based access control  
✅ **Double-Entry Validation** - Debit must equal credit  
✅ **Audit Trail** - Track who created/modified entries  
✅ **Status Management** - Draft, Posted, Approved, Void  
✅ **Error Handling** - Comprehensive error responses  

## Database Schema

### Journal Entry Model

```python
class JournalEntry(Base):
    __tablename__ = "journal_entries"
    
    # Primary key
    id = Column(String, primary_key=True)  # Format: JE-XXXXXXXXXXXX
    
    # Multi-tenancy
    tenant_id = Column(String, nullable=False, index=True)
    
    # Entry details
    date = Column(DateTime(timezone=True), nullable=False)
    description = Column(Text, nullable=False)
    reference = Column(String(100), nullable=True)
    
    # Amounts
    total_debit = Column(Float, nullable=False)
    total_credit = Column(Float, nullable=False)
    
    # Status
    status = Column(String(20), default="draft")  # draft, posted, approved, void
    
    # Audit
    created_by = Column(String, nullable=False)
    approved_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### Indexes

- `idx_tenant_date` - (tenant_id, date) for date range queries
- `idx_tenant_status` - (tenant_id, status) for filtering by status
- `idx_created_by` - (created_by) for audit queries

## API Endpoints

### POST /api/finance/journal-entries

Create a new journal entry.

**Authentication:** Required (JWT)  
**Permission:** `CREATE_FINANCE`  
**Tenant:** Required

#### Request

```http
POST /api/finance/journal-entries HTTP/1.1
Host: api.erp.com
Content-Type: application/json
Authorization: Bearer <token>
X-Tenant-ID: tenant-1

{
  "date": "2024-01-15T10:00:00Z",
  "description": "Monthly rent payment",
  "reference": "INV-2024-001",
  "total_debit": 5000.00,
  "total_credit": 5000.00,
  "created_by": "user-123"
}
```

#### Response (201 Created)

```json
{
  "id": "JE-A1B2C3D4E5F6",
  "date": "2024-01-15T10:00:00Z",
  "description": "Monthly rent payment",
  "reference": "INV-2024-001",
  "total_debit": 5000.00,
  "total_credit": 5000.00,
  "status": "draft",
  "created_by": "user-123",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

#### Validation Rules

1. **Debit = Credit**: Total debit must equal total credit (within 0.01 tolerance)
2. **Required Fields**: date, description, total_debit, total_credit, created_by
3. **Tenant Isolation**: Entry automatically scoped to current tenant
4. **Permission**: User must have `CREATE_FINANCE` permission

#### Error Responses

**400 Bad Request** - Validation Error
```json
{
  "detail": "Total debit must equal total credit"
}
```

**401 Unauthorized** - No Token
```json
{
  "detail": "Not authenticated - no token provided"
}
```

**403 Forbidden** - Insufficient Permission
```json
{
  "detail": "Permission denied. Required permission: create_finance"
}
```

**500 Internal Server Error** - Database Error
```json
{
  "detail": "Failed to create journal entry: <error message>"
}
```

### GET /api/finance/journal-entries

List all journal entries for current tenant.

**Authentication:** Required  
**Permission:** `VIEW_FINANCE`  
**Tenant:** Required

#### Query Parameters

- `skip` (int, default: 0) - Pagination offset
- `limit` (int, default: 100, max: 1000) - Number of records
- `status_filter` (string, optional) - Filter by status (draft, posted, approved, void)

#### Request

```http
GET /api/finance/journal-entries?skip=0&limit=10&status_filter=draft HTTP/1.1
Host: api.erp.com
Authorization: Bearer <token>
X-Tenant-ID: tenant-1
```

#### Response (200 OK)

```json
[
  {
    "id": "JE-A1B2C3D4E5F6",
    "date": "2024-01-15T10:00:00Z",
    "description": "Monthly rent payment",
    "reference": "INV-2024-001",
    "total_debit": 5000.00,
    "total_credit": 5000.00,
    "status": "draft",
    "created_by": "user-123",
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z"
  }
]
```

### GET /api/finance/journal-entries/{entry_id}

Get a specific journal entry.

**Authentication:** Required  
**Permission:** `VIEW_FINANCE`  
**Tenant:** Required

#### Request

```http
GET /api/finance/journal-entries/JE-A1B2C3D4E5F6 HTTP/1.1
Host: api.erp.com
Authorization: Bearer <token>
X-Tenant-ID: tenant-1
```

#### Response (200 OK)

```json
{
  "id": "JE-A1B2C3D4E5F6",
  "date": "2024-01-15T10:00:00Z",
  "description": "Monthly rent payment",
  "reference": "INV-2024-001",
  "total_debit": 5000.00,
  "total_credit": 5000.00,
  "status": "draft",
  "created_by": "user-123",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

#### Error Responses

**404 Not Found**
```json
{
  "detail": "Journal entry JE-A1B2C3D4E5F6 not found"
}
```

### PUT /api/finance/journal-entries/{entry_id}

Update a journal entry (draft only).

**Authentication:** Required  
**Permission:** `EDIT_FINANCE`  
**Tenant:** Required

#### Request

```http
PUT /api/finance/journal-entries/JE-A1B2C3D4E5F6 HTTP/1.1
Host: api.erp.com
Content-Type: application/json
Authorization: Bearer <token>
X-Tenant-ID: tenant-1

{
  "description": "Updated: Monthly rent payment",
  "total_debit": 5500.00,
  "total_credit": 5500.00
}
```

#### Response (200 OK)

```json
{
  "id": "JE-A1B2C3D4E5F6",
  "date": "2024-01-15T10:00:00Z",
  "description": "Updated: Monthly rent payment",
  "reference": "INV-2024-001",
  "total_debit": 5500.00,
  "total_credit": 5500.00,
  "status": "draft",
  "created_by": "user-123",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:05:00Z"
}
```

#### Error Responses

**400 Bad Request** - Cannot Update Posted Entry
```json
{
  "detail": "Cannot update posted entry. Only draft entries can be updated."
}
```

### DELETE /api/finance/journal-entries/{entry_id}

Delete (void) a journal entry.

**Authentication:** Required  
**Permission:** `DELETE_FINANCE`  
**Tenant:** Required

#### Request

```http
DELETE /api/finance/journal-entries/JE-A1B2C3D4E5F6 HTTP/1.1
Host: api.erp.com
Authorization: Bearer <token>
X-Tenant-ID: tenant-1
```

#### Response (204 No Content)

No response body.

## Implementation Details

### Async SQLAlchemy Usage

```python
@router.post("/journal-entries")
async def create_journal_entry(
    entry_data: JournalEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.CREATE_FINANCE)),
    tenant: TenantContext = Depends(get_tenant_context)
):
    # Create model instance
    journal_entry = JournalEntry(
        tenant_id=tenant.tenant_id,
        date=entry_data.date,
        description=entry_data.description,
        total_debit=entry_data.total_debit,
        total_credit=entry_data.total_credit,
        created_by=current_user.user_id
    )
    
    # Add to session
    db.add(journal_entry)
    
    # Commit transaction (async)
    await db.commit()
    
    # Refresh to get generated fields (async)
    await db.refresh(journal_entry)
    
    return journal_entry
```

### Tenant Isolation

All queries automatically filter by tenant_id:

```python
query = select(JournalEntry).where(
    and_(
        JournalEntry.id == entry_id,
        JournalEntry.tenant_id == tenant.tenant_id  # Tenant isolation
    )
)
```

### Error Handling

```python
try:
    # Database operations
    await db.commit()
except HTTPException:
    # Re-raise HTTP exceptions
    raise
except Exception as e:
    # Rollback on error
    await db.rollback()
    logger.error(f"Error: {str(e)}", exc_info=True)
    raise HTTPException(status_code=500, detail=str(e))
```

## Database Setup

### PostgreSQL with asyncpg

```bash
# Install dependencies
pip install sqlalchemy[asyncio] asyncpg

# Connection string
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/erp_db
```

### Initialize Database

```python
from app.database import init_db

# Create tables
await init_db()
```

### Migration with Alembic

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Create journal_entries table"

# Apply migration
alembic upgrade head
```

## Testing

### Create Journal Entry

```bash
curl -X POST "http://localhost:5000/api/finance/journal-entries" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: tenant-1" \
  -d '{
    "date": "2024-01-15T10:00:00Z",
    "description": "Test entry",
    "total_debit": 1000.00,
    "total_credit": 1000.00,
    "created_by": "user-123"
  }'
```

### List Entries

```bash
curl -X GET "http://localhost:5000/api/finance/journal-entries?limit=10" \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: tenant-1"
```

## Performance Considerations

1. **Indexes** - Composite indexes on (tenant_id, date) and (tenant_id, status)
2. **Connection Pooling** - Configured pool size and max overflow
3. **Async Operations** - Non-blocking I/O for better concurrency
4. **Pagination** - Limit query results to prevent memory issues
5. **Query Optimization** - Use `select()` with specific columns when needed

## Security

1. **Tenant Isolation** - All queries filtered by tenant_id
2. **Permission Checks** - RBAC enforced on all endpoints
3. **Input Validation** - Pydantic schemas validate all input
4. **SQL Injection Prevention** - SQLAlchemy parameterized queries
5. **Audit Trail** - Track who created/modified entries

## Next Steps

1. ✅ Implement journal entry line items (debits/credits)
2. ✅ Add posting workflow (draft → posted → approved)
3. ✅ Implement reversal entries
4. ✅ Add batch operations
5. ✅ Implement reports (trial balance, general ledger)
6. ✅ Add export functionality (CSV, Excel, PDF)
