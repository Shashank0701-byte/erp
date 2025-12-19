# Product Model and Service Layer - Implementation Guide

## Overview

This document describes the Product model implementation using SQLAlchemy and the service layer for handling product CRUD operations in the ERP system.

## Features

✅ **SQLAlchemy Model** - Complete product model with relationships  
✅ **Service Layer** - Business logic separation from routes  
✅ **Multi-Tenancy** - Automatic tenant isolation  
✅ **RBAC** - Permission-based access control  
✅ **Stock Management** - Track inventory levels and reorder points  
✅ **Computed Properties** - Automatic calculations (stock value, profit margin)  
✅ **Comprehensive CRUD** - Create, Read, Update, Delete operations  
✅ **Advanced Features** - Stock adjustments, low stock alerts, statistics  

## Database Schema

### Product Model

```python
class Product(Base):
    __tablename__ = "products"
    
    # Primary key
    id = Column(String, primary_key=True)  # Format: PRD-XXXXXXXXXXXX
    
    # Multi-tenancy
    tenant_id = Column(String, nullable=False, index=True)
    
    # Product identification
    sku = Column(String(100), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Categorization
    category = Column(Enum(ProductCategory), nullable=False)
    
    # Measurement
    unit_of_measure = Column(String(50), default="pcs")
    
    # Pricing
    unit_price = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=False)
    
    # Inventory
    quantity_on_hand = Column(Integer, default=0)
    reorder_level = Column(Integer, default=10)
    reorder_quantity = Column(Integer, default=50)
    
    # Location
    location = Column(String(100), nullable=True)
    
    # Additional
    barcode = Column(String(100), unique=True)
    image_url = Column(String(500))
    
    # Status
    is_active = Column(Boolean, default=True)
    status = Column(Enum(ProductStatus), default=ProductStatus.ACTIVE)
    
    # Audit
    created_by = Column(String, nullable=False)
    updated_by = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### Enumerations

```python
class ProductCategory(str, Enum):
    ELECTRONICS = "electronics"
    FURNITURE = "furniture"
    OFFICE_SUPPLIES = "office_supplies"
    HARDWARE = "hardware"
    SOFTWARE = "software"
    RAW_MATERIALS = "raw_materials"
    FINISHED_GOODS = "finished_goods"
    CONSUMABLES = "consumables"
    OTHER = "other"

class ProductStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"
```

### Computed Properties

```python
@property
def needs_reorder(self) -> bool:
    """Check if product needs to be reordered"""
    return self.quantity_on_hand <= self.reorder_level

@property
def stock_value(self) -> float:
    """Calculate total stock value at cost price"""
    return self.quantity_on_hand * self.cost_price

@property
def potential_revenue(self) -> float:
    """Calculate potential revenue at selling price"""
    return self.quantity_on_hand * self.unit_price

@property
def profit_margin(self) -> float:
    """Calculate profit margin percentage"""
    return ((self.unit_price - self.cost_price) / self.unit_price) * 100
```

### Indexes

- `idx_tenant_sku` - (tenant_id, sku) UNIQUE - SKU unique per tenant
- `idx_tenant_category` - (tenant_id, category) - Category filtering
- `idx_tenant_status` - (tenant_id, status) - Status filtering
- `idx_tenant_active` - (tenant_id, is_active) - Active filtering
- `idx_name_search` - (name) - Name searches

## Service Layer

### ProductService Methods

#### 1. create_product()
```python
async def create_product(
    db: AsyncSession,
    product_data: ProductCreate,
    tenant_id: str
) -> Product
```

**Features:**
- Validates SKU uniqueness per tenant
- Auto-generates product ID
- Sets tenant_id automatically
- Returns created product

**Raises:**
- `ValueError` if SKU already exists

#### 2. get_product()
```python
async def get_product(
    db: AsyncSession,
    product_id: str,
    tenant_id: str
) -> Optional[Product]
```

**Features:**
- Retrieves product by ID
- Enforces tenant isolation
- Returns None if not found

#### 3. get_by_sku()
```python
async def get_by_sku(
    db: AsyncSession,
    sku: str,
    tenant_id: str
) -> Optional[Product]
```

**Features:**
- Retrieves product by SKU
- Tenant-scoped lookup
- Returns None if not found

#### 4. list_products()
```python
async def list_products(
    db: AsyncSession,
    tenant_id: str,
    filters: ProductListFilter
) -> tuple[List[Product], int]
```

**Features:**
- Supports multiple filters (category, status, active, price range)
- Full-text search in name, SKU, description
- Pagination (skip, limit)
- Returns products and total count

**Filters:**
- `category` - Filter by product category
- `status` - Filter by status (active, inactive, discontinued)
- `is_active` - Filter by active flag
- `needs_reorder` - Show only products needing reorder
- `search` - Search in name, SKU, description
- `min_price` / `max_price` - Price range
- `skip` / `limit` - Pagination

#### 5. update_product()
```python
async def update_product(
    db: AsyncSession,
    product_id: str,
    product_data: ProductUpdate,
    tenant_id: str
) -> Optional[Product]
```

**Features:**
- Partial updates (only provided fields)
- SKU uniqueness validation
- Returns updated product
- Returns None if not found

**Raises:**
- `ValueError` if new SKU already exists

#### 6. delete_product()
```python
async def delete_product(
    db: AsyncSession,
    product_id: str,
    tenant_id: str,
    soft_delete: bool = True
) -> bool
```

**Features:**
- Soft delete (default) - sets status to discontinued
- Hard delete (optional) - removes from database
- Returns True if deleted, False if not found

#### 7. adjust_stock()
```python
async def adjust_stock(
    db: AsyncSession,
    product_id: str,
    adjustment: ProductStockAdjustment,
    tenant_id: str
) -> Optional[Product]
```

**Features:**
- Add or remove stock quantity
- Validates non-negative stock
- Logs adjustment reason
- Updates updated_by field

**Raises:**
- `ValueError` if adjustment results in negative stock

#### 8. get_low_stock_products()
```python
async def get_low_stock_products(
    db: AsyncSession,
    tenant_id: str
) -> List[Product]
```

**Features:**
- Returns products at or below reorder level
- Only active products
- Sorted by quantity (lowest first)

#### 9. get_product_statistics()
```python
async def get_product_statistics(
    db: AsyncSession,
    tenant_id: str
) -> dict
```

**Returns:**
```json
{
  "total_products": 150,
  "active_products": 140,
  "inactive_products": 10,
  "low_stock_products": 15,
  "total_stock_value": 125000.50
}
```

## API Endpoints

### POST /api/inventory/products

Create a new product.

**Request:**
```json
{
  "sku": "LAP-001",
  "name": "Laptop Computer",
  "description": "High-performance laptop",
  "category": "electronics",
  "unit_of_measure": "pcs",
  "unit_price": 1200.00,
  "cost_price": 800.00,
  "quantity_on_hand": 50,
  "reorder_level": 10,
  "reorder_quantity": 20,
  "location": "Warehouse A",
  "barcode": "123456789",
  "created_by": "user-123"
}
```

**Response (201):**
```json
{
  "id": "PRD-A1B2C3D4E5F6",
  "tenant_id": "tenant-1",
  "sku": "LAP-001",
  "name": "Laptop Computer",
  "category": "electronics",
  "unit_price": 1200.00,
  "cost_price": 800.00,
  "quantity_on_hand": 50,
  "needs_reorder": false,
  "stock_value": 40000.00,
  "potential_revenue": 60000.00,
  "profit_margin": 33.33,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

### GET /api/inventory/products

List products with filtering.

**Query Parameters:**
- `category` - Filter by category
- `status` - Filter by status
- `is_active` - Filter by active status
- `needs_reorder` - Show products needing reorder
- `search` - Search text
- `min_price` / `max_price` - Price range
- `skip` / `limit` - Pagination

**Response (200):**
```json
{
  "products": [...],
  "total": 150,
  "skip": 0,
  "limit": 100
}
```

### GET /api/inventory/products/{product_id}

Get a specific product.

**Response (200):**
```json
{
  "id": "PRD-A1B2C3D4E5F6",
  "sku": "LAP-001",
  "name": "Laptop Computer",
  ...
}
```

### GET /api/inventory/products/sku/{sku}

Get product by SKU.

### PUT /api/inventory/products/{product_id}

Update a product.

**Request:**
```json
{
  "unit_price": 1300.00,
  "quantity_on_hand": 45,
  "updated_by": "user-123"
}
```

### DELETE /api/inventory/products/{product_id}

Delete a product.

**Query Parameters:**
- `hard_delete` (bool) - Perform hard delete (default: false)

### POST /api/inventory/products/{product_id}/adjust-stock

Adjust product stock.

**Request:**
```json
{
  "quantity_change": -5,
  "reason": "Sold 5 units",
  "adjusted_by": "user-123"
}
```

### GET /api/inventory/products/low-stock/list

Get products needing reorder.

**Response (200):**
```json
[
  {
    "id": "PRD-123",
    "sku": "LAP-001",
    "quantity_on_hand": 8,
    "reorder_level": 10,
    "needs_reorder": true
  }
]
```

### GET /api/inventory/products/statistics/summary

Get product statistics.

**Response (200):**
```json
{
  "total_products": 150,
  "active_products": 140,
  "inactive_products": 10,
  "low_stock_products": 15,
  "total_stock_value": 125000.50
}
```

## Usage Examples

### Create Product

```python
from app.services.product_service import ProductService
from app.schemas.product import ProductCreate

product_data = ProductCreate(
    sku="LAP-001",
    name="Laptop Computer",
    category="electronics",
    unit_price=1200.00,
    cost_price=800.00,
    quantity_on_hand=50,
    created_by="user-123"
)

product = await ProductService.create_product(db, product_data, "tenant-1")
```

### List Products with Filters

```python
from app.schemas.product import ProductListFilter

filters = ProductListFilter(
    category="electronics",
    needs_reorder=True,
    search="laptop",
    skip=0,
    limit=10
)

products, total = await ProductService.list_products(db, "tenant-1", filters)
```

### Adjust Stock

```python
from app.schemas.product import ProductStockAdjustment

adjustment = ProductStockAdjustment(
    quantity_change=-5,
    reason="Sold 5 units",
    adjusted_by="user-123"
)

product = await ProductService.adjust_stock(db, "PRD-123", adjustment, "tenant-1")
```

## Security

1. **Tenant Isolation** - All queries filtered by tenant_id
2. **Permission Checks** - RBAC enforced on all endpoints
3. **SKU Uniqueness** - Per-tenant SKU validation
4. **Input Validation** - Pydantic schemas validate all input
5. **Audit Trail** - Track who created/updated products

## Performance Optimization

1. **Indexes** - Composite indexes on frequently queried fields
2. **Pagination** - Limit query results
3. **Async Operations** - Non-blocking database I/O
4. **Computed Properties** - Calculated on-the-fly, not stored
5. **Efficient Queries** - Use select() with specific columns when needed

## Next Steps

1. ✅ Add product images upload
2. ✅ Implement product variants (size, color, etc.)
3. ✅ Add product bundles/kits
4. ✅ Implement stock movement history
5. ✅ Add barcode scanning integration
6. ✅ Implement product import/export (CSV, Excel)
7. ✅ Add product analytics and reports
