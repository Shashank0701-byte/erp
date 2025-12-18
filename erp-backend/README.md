# ERP Backend API

FastAPI-based backend for Enterprise Resource Planning (ERP) system with comprehensive RBAC (Role-Based Access Control).

## Features

- ✅ **FastAPI Framework** - Modern, fast, async Python web framework
- ✅ **Pydantic Validation** - Comprehensive request/response validation
- ✅ **JWT Authentication** - Secure token-based authentication
- ✅ **RBAC System** - Role-based access control with fine-grained permissions
- ✅ **Multiple Modules** - Finance, Inventory, HR, Sales, and more
- ✅ **Auto-generated API Docs** - Interactive Swagger UI and ReDoc
- ✅ **Type Safety** - Full type hints and validation

## Project Structure

```
erp-backend/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration settings
│   ├── schemas.py           # Pydantic models for validation
│   ├── dependencies.py      # Auth and RBAC dependencies
│   ├── utils.py             # Utility functions
│   └── routers/             # API route handlers (to be created)
│       ├── auth.py
│       ├── users.py
│       ├── finance.py
│       ├── inventory.py
│       ├── hr.py
│       └── sales.py
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis (optional, for caching)

### Setup

1. **Clone the repository**
```bash
cd erp-backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run the application**
```bash
python -m app.main
# Or use uvicorn directly:
uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
```

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:5000/api/docs
- **ReDoc**: http://localhost:5000/api/redoc
- **OpenAPI JSON**: http://localhost:5000/api/openapi.json

## Pydantic Schemas

### User Schemas

- `UserCreate` - Create new user with validation
- `UserUpdate` - Update user information
- `UserResponse` - User data response
- `LoginRequest` - Login credentials
- `LoginResponse` - Login response with JWT

### Finance Schemas

- `JournalEntryCreate` - Create journal entry
- `JournalEntryUpdate` - Update journal entry
- `JournalEntryResponse` - Journal entry data

### Inventory Schemas

- `InventoryItemCreate` - Create inventory item
- `InventoryItemUpdate` - Update inventory item
- `InventoryItemResponse` - Inventory item data

### HR Schemas

- `EmployeeCreate` - Create employee record
- `EmployeeUpdate` - Update employee information
- `EmployeeResponse` - Employee data

### Sales Schemas

- `SalesOrderCreate` - Create sales order
- `SalesOrderUpdate` - Update sales order
- `SalesOrderResponse` - Sales order data

## Authentication & Authorization

### JWT Token Flow

1. User logs in with credentials
2. Server validates and returns JWT access token
3. Client includes token in Authorization header: `Bearer <token>`
4. Server validates token on protected endpoints

### RBAC Roles

- **ADMIN** - Full system access
- **MANAGER** - Multi-module access with reporting
- **FINANCE** - Finance module access
- **INVENTORY** - Inventory module access
- **HR** - HR module access
- **SALES** - Sales module access
- **VIEWER** - Read-only access

### Using Dependencies

```python
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user, require_permission, require_role
from app.schemas import Permission, UserRole, TokenData

router = APIRouter()

# Require authentication
@router.get("/protected")
async def protected_route(current_user: TokenData = Depends(get_current_user)):
    return {"user": current_user.email}

# Require specific permission
@router.post("/finance/entry")
async def create_entry(
    current_user: TokenData = Depends(require_permission(Permission.CREATE_FINANCE))
):
    return {"message": "Entry created"}

# Require specific role
@router.get("/admin/dashboard")
async def admin_dashboard(
    current_user: TokenData = Depends(require_role([UserRole.ADMIN]))
):
    return {"message": "Admin dashboard"}
```

## Validation Examples

### Password Validation

```python
from app.schemas import UserCreate

# This will raise validation error
user = UserCreate(
    email="user@example.com",
    name="John Doe",
    role="admin",
    password="weak"  # Error: must be 8+ chars with uppercase, lowercase, digit
)

# Valid
user = UserCreate(
    email="user@example.com",
    name="John Doe",
    role="admin",
    password="SecurePass123"  # ✓
)
```

### Journal Entry Validation

```python
from app.schemas import JournalEntryCreate

# This will raise validation error
entry = JournalEntryCreate(
    date=datetime.now(),
    description="Test entry",
    total_debit=100.00,
    total_credit=99.00,  # Error: must equal debit
    created_by="user-123"
)

# Valid
entry = JournalEntryCreate(
    date=datetime.now(),
    description="Test entry",
    total_debit=100.00,
    total_credit=100.00,  # ✓
    created_by="user-123"
)
```

## Environment Variables

Key environment variables (see `.env.example`):

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/erp_db

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

## Development

### Running in Development Mode

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black app/
isort app/
```

### Type Checking

```bash
mypy app/
```

## Production Deployment

### Using Docker

```bash
docker build -t erp-backend .
docker run -p 5000:5000 erp-backend
```

### Using Gunicorn

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000
```

## API Endpoints (Planned)

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/verify` - Verify token
- `POST /api/auth/refresh` - Refresh token

### Users
- `GET /api/users` - List users
- `POST /api/users` - Create user
- `GET /api/users/{id}` - Get user
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user

### Finance
- `GET /api/finance/journal-entries` - List entries
- `POST /api/finance/journal-entries` - Create entry
- `GET /api/finance/journal-entries/{id}` - Get entry
- `PUT /api/finance/journal-entries/{id}` - Update entry
- `DELETE /api/finance/journal-entries/{id}` - Delete entry

### Inventory
- `GET /api/inventory/items` - List items
- `POST /api/inventory/items` - Create item
- `GET /api/inventory/items/{id}` - Get item
- `PUT /api/inventory/items/{id}` - Update item
- `DELETE /api/inventory/items/{id}` - Delete item

### HR
- `GET /api/hr/employees` - List employees
- `POST /api/hr/employees` - Create employee
- `GET /api/hr/employees/{id}` - Get employee
- `PUT /api/hr/employees/{id}` - Update employee
- `DELETE /api/hr/employees/{id}` - Delete employee

### Sales
- `GET /api/sales/orders` - List orders
- `POST /api/sales/orders` - Create order
- `GET /api/sales/orders/{id}` - Get order
- `PUT /api/sales/orders/{id}` - Update order
- `DELETE /api/sales/orders/{id}` - Delete order

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.
