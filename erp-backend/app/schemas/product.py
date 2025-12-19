from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum


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


class ProductBase(BaseModel):
    """Base product schema"""
    sku: str = Field(..., min_length=1, max_length=100, description="Stock Keeping Unit")
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    category: ProductCategory = Field(default=ProductCategory.OTHER, description="Product category")
    unit_of_measure: str = Field(default="pcs", max_length=50, description="Unit of measurement")
    unit_price: float = Field(..., ge=0, description="Selling price per unit")
    cost_price: float = Field(..., ge=0, description="Cost price per unit")
    quantity_on_hand: int = Field(default=0, ge=0, description="Current stock quantity")
    reorder_level: int = Field(default=10, ge=0, description="Minimum quantity before reorder")
    reorder_quantity: int = Field(default=50, ge=1, description="Quantity to order when restocking")
    location: Optional[str] = Field(None, max_length=100, description="Storage location")
    barcode: Optional[str] = Field(None, max_length=100, description="Product barcode")
    image_url: Optional[str] = Field(None, max_length=500, description="Product image URL")
    is_active: bool = Field(default=True, description="Whether product is active")
    status: ProductStatus = Field(default=ProductStatus.ACTIVE, description="Product status")
    
    @validator('unit_price')
    def validate_unit_price(cls, v, values):
        """Validate unit price is greater than or equal to cost price"""
        cost_price = values.get('cost_price', 0)
        if v < cost_price:
            raise ValueError('Unit price should be greater than or equal to cost price')
        return v
    
    class Config:
        from_attributes = True
        use_enum_values = True


class ProductCreate(ProductBase):
    """Schema for creating a new product"""
    created_by: str = Field(..., description="User ID creating the product")


class ProductUpdate(BaseModel):
    """Schema for updating a product"""
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[ProductCategory] = None
    unit_of_measure: Optional[str] = Field(None, max_length=50)
    unit_price: Optional[float] = Field(None, ge=0)
    cost_price: Optional[float] = Field(None, ge=0)
    quantity_on_hand: Optional[int] = Field(None, ge=0)
    reorder_level: Optional[int] = Field(None, ge=0)
    reorder_quantity: Optional[int] = Field(None, ge=1)
    location: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    image_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    status: Optional[ProductStatus] = None
    updated_by: Optional[str] = Field(None, description="User ID updating the product")
    
    class Config:
        from_attributes = True
        use_enum_values = True


class ProductResponse(ProductBase):
    """Schema for product response"""
    id: str
    tenant_id: str
    created_by: str
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    needs_reorder: bool = Field(description="Whether product needs reordering")
    stock_value: float = Field(description="Total stock value at cost price")
    potential_revenue: float = Field(description="Potential revenue at selling price")
    profit_margin: float = Field(description="Profit margin percentage")
    
    class Config:
        from_attributes = True
        use_enum_values = True


class ProductStockAdjustment(BaseModel):
    """Schema for adjusting product stock"""
    quantity_change: int = Field(..., description="Quantity to add (positive) or remove (negative)")
    reason: str = Field(..., min_length=1, max_length=200, description="Reason for adjustment")
    adjusted_by: str = Field(..., description="User ID making the adjustment")


class ProductListFilter(BaseModel):
    """Schema for filtering product list"""
    category: Optional[ProductCategory] = None
    status: Optional[ProductStatus] = None
    is_active: Optional[bool] = None
    needs_reorder: Optional[bool] = None
    search: Optional[str] = Field(None, description="Search in name, SKU, or description")
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    skip: int = Field(default=0, ge=0, description="Pagination offset")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum results")
    
    class Config:
        use_enum_values = True
