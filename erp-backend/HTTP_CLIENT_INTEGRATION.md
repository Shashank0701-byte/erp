# HTTP Client Integration - Sales Service Communication

## Overview

This document describes the integration of an async HTTP client (httpx) into the Inventory service to fetch real-time data from the Sales service.

## Features

✅ **Async HTTP Client** - Non-blocking HTTP requests using httpx  
✅ **Connection Pooling** - Efficient connection reuse  
✅ **Sales Data Integration** - Real-time sales analytics  
✅ **Demand Forecasting** - AI-powered predictions  
✅ **Smart Reorder Recommendations** - Data-driven inventory decisions  
✅ **Comprehensive Dashboard** - Combined inventory and sales metrics  
✅ **Error Handling** - Graceful degradation on service failures  

## Architecture

```
┌─────────────────┐         HTTP/2          ┌─────────────────┐
│                 │  ◄──────────────────►   │                 │
│  Inventory      │    httpx Client         │  Sales          │
│  Service        │    (Async)              │  Service        │
│  (Port 5000)    │                         │  (Port 5001)    │
│                 │                         │                 │
└─────────────────┘                         └─────────────────┘
        │                                           │
        │                                           │
        ▼                                           ▼
  ┌──────────┐                               ┌──────────┐
  │ Products │                               │  Sales   │
  │ Database │                               │ Database │
  └──────────┘                               └──────────┘
```

## Components

### 1. HTTP Client Utility (`app/utils/http_client.py`)

**HTTPClient Class:**
- Singleton pattern for connection pooling
- Async GET, POST, PUT, DELETE methods
- Automatic retry logic
- Request/response logging
- Timeout configuration

**Features:**
```python
# Configuration
- Timeout: 30s total, 10s connect
- Max connections: 100
- Max keepalive: 20
- HTTP/2 support enabled
- Automatic redirects
```

**Usage:**
```python
from app.utils.http_client import HTTPClient

# GET request
response = await HTTPClient.get(
    url="https://api.example.com/data",
    headers={"Authorization": "Bearer token"},
    params={"limit": 10}
)

# POST request
response = await HTTPClient.post(
    url="https://api.example.com/data",
    json={"key": "value"},
    headers={"Content-Type": "application/json"}
)
```

### 2. Sales Service Client (`app/clients/sales_client.py`)

**SalesServiceClient Methods:**

#### get_product_sales_data()
Fetch sales analytics for a product.

**Request:**
```python
sales_data = await SalesServiceClient.get_product_sales_data(
    product_id="PRD-123",
    tenant_id="tenant-1",
    days=30,
    auth_token="Bearer token"
)
```

**Response:**
```json
{
  "product_id": "PRD-123",
  "total_quantity_sold": 150,
  "total_revenue": 180000.00,
  "average_daily_sales": 5.0,
  "sales_trend": "increasing",
  "last_sale_date": "2024-01-15T10:00:00Z"
}
```

#### get_product_demand_forecast()
Get AI-powered demand forecast.

**Response:**
```json
{
  "product_id": "PRD-123",
  "forecast_days": 30,
  "predicted_demand": 180,
  "confidence_level": 0.85,
  "recommended_stock_level": 200
}
```

#### get_top_selling_products()
Get top selling products.

**Response:**
```json
[
  {
    "product_id": "PRD-123",
    "product_name": "Laptop",
    "quantity_sold": 150,
    "revenue": 180000.00,
    "rank": 1
  }
]
```

#### get_sales_summary()
Get overall sales summary.

**Response:**
```json
{
  "total_orders": 1250,
  "total_revenue": 1500000.00,
  "total_items_sold": 5000,
  "average_order_value": 1200.00
}
```

### 3. Inventory Service (`app/services/inventory_service.py`)

**Enhanced Methods:**

#### get_product_with_sales_data()
Combines product data with sales analytics.

**Response:**
```json
{
  "id": "PRD-123",
  "sku": "LAP-001",
  "name": "Laptop",
  "quantity_on_hand": 50,
  "sales_analytics": {
    "total_quantity_sold": 150,
    "total_revenue": 180000.00,
    "average_daily_sales": 5.0,
    "sales_trend": "increasing",
    "period_days": 30
  }
}
```

#### get_product_with_demand_forecast()
Combines product data with demand forecast.

**Response:**
```json
{
  "id": "PRD-123",
  "current_stock": 50,
  "demand_forecast": {
    "forecast_days": 30,
    "predicted_demand": 180,
    "confidence_level": 0.85,
    "recommended_stock_level": 200,
    "should_reorder": true,
    "recommended_reorder_quantity": 150
  }
}
```

#### get_inventory_dashboard()
Comprehensive dashboard with combined metrics.

**Response:**
```json
{
  "inventory_stats": {
    "total_products": 150,
    "active_products": 140,
    "low_stock_products": 15,
    "total_stock_value": 125000.50
  },
  "sales_summary": {
    "total_revenue": 1500000.00,
    "total_orders": 1250,
    "total_items_sold": 5000
  },
  "top_selling_products": [...],
  "low_stock_alerts": [...]
}
```

#### smart_reorder_recommendation()
AI-powered reorder recommendations.

**Response:**
```json
{
  "product_id": "PRD-123",
  "current_stock": 50,
  "sales_analytics": {
    "average_daily_sales": 5.0,
    "total_sold_30_days": 150,
    "sales_trend": "increasing"
  },
  "forecast": {
    "predicted_demand_30_days": 180,
    "confidence_level": 0.85
  },
  "recommendation": {
    "needs_reorder": true,
    "days_of_stock_remaining": 10.0,
    "recommended_order_quantity": 200,
    "urgency": "medium"
  }
}
```

## API Endpoints

### GET /api/inventory/products/{product_id}/with-sales-data

Get product with integrated sales analytics.

**Query Parameters:**
- `days` (int, default: 30) - Number of days for sales data

**Example:**
```bash
curl -X GET "http://localhost:5000/api/inventory/products/PRD-123/with-sales-data?days=30" \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: tenant-1"
```

### GET /api/inventory/products/{product_id}/demand-forecast

Get product with demand forecast.

**Query Parameters:**
- `forecast_days` (int, default: 30) - Number of days to forecast

### GET /api/inventory/dashboard

Get comprehensive inventory dashboard.

**Features:**
- Inventory statistics
- Sales summary
- Top selling products
- Low stock alerts

### GET /api/inventory/products/{product_id}/reorder-recommendation

Get smart reorder recommendation.

**Features:**
- Historical sales analysis
- Demand forecasting
- Stock level calculation
- Urgency assessment

## Configuration

### Environment Variables

```bash
# Microservices URLs
SALES_SERVICE_URL=http://localhost:5001
FINANCE_SERVICE_URL=http://localhost:5002
HR_SERVICE_URL=http://localhost:5003

# HTTP Client Configuration
HTTP_CLIENT_TIMEOUT=30
HTTP_CLIENT_MAX_CONNECTIONS=100
HTTP_CLIENT_MAX_KEEPALIVE=20
```

### Application Config (`app/config.py`)

```python
class Settings(BaseSettings):
    # Microservices URLs
    SALES_SERVICE_URL: str = "http://localhost:5001"
    
    # HTTP Client
    HTTP_CLIENT_TIMEOUT: int = 30
    HTTP_CLIENT_MAX_CONNECTIONS: int = 100
    HTTP_CLIENT_MAX_KEEPALIVE: int = 20
```

## Error Handling

### Graceful Degradation

When Sales service is unavailable, the system returns default values:

```python
# If Sales service fails
{
  "product_id": "PRD-123",
  "total_quantity_sold": 0,
  "total_revenue": 0.0,
  "average_daily_sales": 0.0,
  "sales_trend": "unknown",
  "error": "Connection refused"
}
```

### Retry Logic

```python
# Automatic retries on transient failures
- Connection timeout: Retry 3 times
- 5xx errors: Retry 2 times
- Network errors: Retry 3 times
```

## Performance

### Connection Pooling

```python
# Reuse connections for better performance
- Pool size: 100 connections
- Keepalive: 20 connections
- HTTP/2 multiplexing enabled
```

### Async Operations

```python
# Non-blocking I/O
async def get_dashboard():
    # Parallel requests
    inventory_stats, sales_summary, top_selling = await asyncio.gather(
        get_inventory_stats(),
        get_sales_summary(),
        get_top_selling()
    )
```

## Security

### Authentication

```python
# Forward JWT token to Sales service
headers = {
    "Authorization": f"Bearer {auth_token}",
    "X-Tenant-ID": tenant_id
}
```

### Tenant Isolation

```python
# All requests include tenant context
- Header: X-Tenant-ID
- Ensures data isolation
- Prevents cross-tenant access
```

## Testing

### Mock Sales Service

```python
# For testing without Sales service
@pytest.fixture
def mock_sales_client(monkeypatch):
    async def mock_get_sales_data(*args, **kwargs):
        return {
            "total_quantity_sold": 100,
            "total_revenue": 120000.00
        }
    
    monkeypatch.setattr(
        SalesServiceClient,
        "get_product_sales_data",
        mock_get_sales_data
    )
```

### Integration Tests

```python
async def test_product_with_sales_data():
    # Test with real Sales service
    response = await client.get(
        "/api/inventory/products/PRD-123/with-sales-data",
        headers={"X-Tenant-ID": "tenant-1"}
    )
    
    assert response.status_code == 200
    assert "sales_analytics" in response.json()
```

## Monitoring

### Logging

```python
# HTTP client logs all requests
logger.debug(f"GET request to {url}")
logger.debug(f"GET {url} - Status: {response.status_code}")
logger.error(f"GET request failed: {url} - {str(e)}")
```

### Metrics

Track:
- Request count
- Response times
- Error rates
- Connection pool usage

## Best Practices

1. **Always pass auth token** - For secure service-to-service communication
2. **Handle errors gracefully** - Return default values on failure
3. **Use connection pooling** - Reuse HTTP connections
4. **Set appropriate timeouts** - Prevent hanging requests
5. **Log all requests** - For debugging and monitoring
6. **Cache responses** - For frequently accessed data
7. **Use async/await** - For non-blocking operations
8. **Validate responses** - Check status codes and data structure

## Next Steps

1. ✅ Add response caching with Redis
2. ✅ Implement circuit breaker pattern
3. ✅ Add request rate limiting
4. ✅ Implement service discovery
5. ✅ Add distributed tracing
6. ✅ Implement health checks
7. ✅ Add metrics collection
