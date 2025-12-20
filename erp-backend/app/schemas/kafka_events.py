"""
Kafka Event Schemas
Defines event structures for inter-service communication
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Event types for Kafka messages"""
    LOW_STOCK = "inventory.low_stock"
    PRODUCT_CREATED = "inventory.product_created"
    PRODUCT_UPDATED = "inventory.product_updated"
    STOCK_ADJUSTED = "inventory.stock_adjusted"
    ORDER_CREATED = "sales.order_created"
    ORDER_FULFILLED = "sales.order_fulfilled"


class EventPriority(str, Enum):
    """Event priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventMetadata(BaseModel):
    """Metadata for all events"""
    event_id: str = Field(..., description="Unique event identifier")
    event_type: EventType = Field(..., description="Type of event")
    event_version: str = Field(default="1.0", description="Event schema version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    source_service: str = Field(..., description="Service that produced the event")
    tenant_id: str = Field(..., description="Tenant identifier")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracing")
    priority: EventPriority = Field(default=EventPriority.MEDIUM, description="Event priority")
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "evt-123456",
                "event_type": "inventory.low_stock",
                "event_version": "1.0",
                "timestamp": "2024-01-15T10:00:00Z",
                "source_service": "inventory-service",
                "tenant_id": "tenant-1",
                "priority": "high"
            }
        }


class LowStockEventPayload(BaseModel):
    """Payload for low stock events"""
    product_id: str = Field(..., description="Product ID")
    product_sku: str = Field(..., description="Product SKU")
    product_name: str = Field(..., description="Product name")
    current_stock: int = Field(..., ge=0, description="Current stock quantity")
    reorder_level: int = Field(..., ge=0, description="Reorder level threshold")
    reorder_quantity: int = Field(..., ge=1, description="Recommended reorder quantity")
    unit_price: float = Field(..., ge=0, description="Unit price")
    category: str = Field(..., description="Product category")
    location: Optional[str] = Field(None, description="Storage location")
    days_of_stock_remaining: Optional[float] = Field(None, description="Estimated days until stockout")
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "PRD-123",
                "product_sku": "LAP-001",
                "product_name": "Laptop Computer",
                "current_stock": 8,
                "reorder_level": 10,
                "reorder_quantity": 50,
                "unit_price": 1200.00,
                "category": "electronics",
                "location": "Warehouse A",
                "days_of_stock_remaining": 3.5
            }
        }


class LowStockEvent(BaseModel):
    """Complete low stock event structure"""
    metadata: EventMetadata
    payload: LowStockEventPayload
    
    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "event_id": "evt-123456",
                    "event_type": "inventory.low_stock",
                    "timestamp": "2024-01-15T10:00:00Z",
                    "source_service": "inventory-service",
                    "tenant_id": "tenant-1",
                    "priority": "high"
                },
                "payload": {
                    "product_id": "PRD-123",
                    "product_sku": "LAP-001",
                    "product_name": "Laptop Computer",
                    "current_stock": 8,
                    "reorder_level": 10,
                    "reorder_quantity": 50,
                    "unit_price": 1200.00,
                    "category": "electronics"
                }
            }
        }


class ProductCreatedEventPayload(BaseModel):
    """Payload for product created events"""
    product_id: str
    product_sku: str
    product_name: str
    category: str
    unit_price: float
    cost_price: float
    initial_stock: int
    
    class Config:
        from_attributes = True


class ProductCreatedEvent(BaseModel):
    """Product created event"""
    metadata: EventMetadata
    payload: ProductCreatedEventPayload


class StockAdjustedEventPayload(BaseModel):
    """Payload for stock adjustment events"""
    product_id: str
    product_sku: str
    product_name: str
    previous_stock: int
    new_stock: int
    adjustment_quantity: int
    reason: str
    adjusted_by: str
    
    class Config:
        from_attributes = True


class StockAdjustedEvent(BaseModel):
    """Stock adjusted event"""
    metadata: EventMetadata
    payload: StockAdjustedEventPayload


class OrderCreatedEventPayload(BaseModel):
    """Payload for order created events"""
    order_id: str
    customer_id: str
    total_amount: float
    items_count: int
    status: str
    
    class Config:
        from_attributes = True


class OrderCreatedEvent(BaseModel):
    """Order created event"""
    metadata: EventMetadata
    payload: OrderCreatedEventPayload
