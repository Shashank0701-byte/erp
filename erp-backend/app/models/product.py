from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, Index, Enum as SQLEnum
from sqlalchemy.sql import func
from enum import Enum
from app.database import Base
import uuid


class ProductCategory(str, Enum):
    """Product category enumeration"""
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
    """Product status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"


class Product(Base):
    """
    Product model for inventory management
    
    Attributes:
        id: Unique identifier
        tenant_id: Tenant identifier for multi-tenancy
        sku: Stock Keeping Unit (unique per tenant)
        name: Product name
        description: Detailed product description
        category: Product category
        unit_of_measure: Unit of measurement (pcs, kg, liter, etc.)
        unit_price: Price per unit
        cost_price: Cost per unit
        quantity_on_hand: Current stock quantity
        reorder_level: Minimum quantity before reorder
        reorder_quantity: Quantity to order when below reorder level
        location: Storage location
        barcode: Product barcode (optional)
        image_url: Product image URL (optional)
        is_active: Whether product is active
        status: Product status (active, inactive, discontinued)
        created_by: User ID who created the product
        updated_by: User ID who last updated the product
        created_at: Timestamp when created
        updated_at: Timestamp when last updated
    """
    
    __tablename__ = "products"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: f"PRD-{uuid.uuid4().hex[:12].upper()}")
    
    # Multi-tenancy
    tenant_id = Column(String, nullable=False, index=True)
    
    # Product identification
    sku = Column(String(100), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Categorization
    category = Column(SQLEnum(ProductCategory), nullable=False, default=ProductCategory.OTHER, index=True)
    
    # Measurement
    unit_of_measure = Column(String(50), nullable=False, default="pcs")
    
    # Pricing
    unit_price = Column(Float, nullable=False, default=0.0)
    cost_price = Column(Float, nullable=False, default=0.0)
    
    # Inventory
    quantity_on_hand = Column(Integer, nullable=False, default=0)
    reorder_level = Column(Integer, nullable=False, default=10)
    reorder_quantity = Column(Integer, nullable=False, default=50)
    
    # Location
    location = Column(String(100), nullable=True)
    
    # Additional info
    barcode = Column(String(100), nullable=True, unique=True)
    image_url = Column(String(500), nullable=True)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    status = Column(SQLEnum(ProductStatus), nullable=False, default=ProductStatus.ACTIVE, index=True)
    
    # Audit fields
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_tenant_sku', 'tenant_id', 'sku', unique=True),  # SKU unique per tenant
        Index('idx_tenant_category', 'tenant_id', 'category'),
        Index('idx_tenant_status', 'tenant_id', 'status'),
        Index('idx_tenant_active', 'tenant_id', 'is_active'),
        Index('idx_name_search', 'name'),  # For name searches
    )
    
    def __repr__(self):
        return f"<Product(id={self.id}, sku={self.sku}, name={self.name}, tenant={self.tenant_id})>"
    
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
        if self.unit_price == 0:
            return 0.0
        return ((self.unit_price - self.cost_price) / self.unit_price) * 100
