from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TenantBase(BaseModel):
    """Base tenant schema"""
    name: str = Field(..., min_length=1, max_length=200)
    domain: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True
    settings: Optional[dict] = None


class TenantCreate(TenantBase):
    """Schema for creating a new tenant"""
    admin_email: str
    admin_name: str
    admin_password: str


class TenantUpdate(BaseModel):
    """Schema for updating tenant"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    domain: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None
    settings: Optional[dict] = None


class TenantResponse(TenantBase):
    """Schema for tenant response"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TenantContext(BaseModel):
    """
    Tenant context information extracted from request
    Used for dependency injection
    """
    tenant_id: str
    tenant_name: str
    domain: str
    is_active: bool
    settings: Optional[dict] = None
    
    class Config:
        from_attributes = True
