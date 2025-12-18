from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    FINANCE = "finance"
    INVENTORY = "inventory"
    HR = "hr"
    SALES = "sales"
    VIEWER = "viewer"


class Permission(str, Enum):
    # Finance permissions
    VIEW_FINANCE = "view_finance"
    CREATE_FINANCE = "create_finance"
    EDIT_FINANCE = "edit_finance"
    DELETE_FINANCE = "delete_finance"
    APPROVE_FINANCE = "approve_finance"
    
    # Inventory permissions
    VIEW_INVENTORY = "view_inventory"
    CREATE_INVENTORY = "create_inventory"
    EDIT_INVENTORY = "edit_inventory"
    DELETE_INVENTORY = "delete_inventory"
    
    # HR permissions
    VIEW_HR = "view_hr"
    CREATE_HR = "create_hr"
    EDIT_HR = "edit_hr"
    DELETE_HR = "delete_hr"
    
    # Sales permissions
    VIEW_SALES = "view_sales"
    CREATE_SALES = "create_sales"
    EDIT_SALES = "edit_sales"
    DELETE_SALES = "delete_sales"
    
    # Admin permissions
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    VIEW_REPORTS = "view_reports"
    SYSTEM_SETTINGS = "system_settings"


# Base schemas
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        use_enum_values = True


# User schemas
class UserBase(BaseSchema):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    role: UserRole
    department: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v


class UserUpdate(BaseSchema):
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    id: str
    hashed_password: str
    created_at: datetime
    updated_at: datetime


class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime
    permissions: List[Permission]


# Authentication schemas
class LoginRequest(BaseSchema):
    email: EmailStr
    password: str


class LoginResponse(BaseSchema):
    success: bool
    message: str
    token: str
    refresh_token: Optional[str] = None
    user: UserResponse


class TokenData(BaseSchema):
    user_id: str
    email: str
    role: UserRole
    exp: Optional[datetime] = None


class RefreshTokenRequest(BaseSchema):
    refresh_token: str


# Finance schemas
class JournalEntryBase(BaseSchema):
    date: datetime
    description: str = Field(..., min_length=1, max_length=500)
    reference: Optional[str] = None
    total_debit: float = Field(..., ge=0)
    total_credit: float = Field(..., ge=0)
    
    @validator('total_credit')
    def validate_balance(cls, v, values):
        if 'total_debit' in values and abs(v - values['total_debit']) > 0.01:
            raise ValueError('Total debit must equal total credit')
        return v


class JournalEntryCreate(JournalEntryBase):
    created_by: str


class JournalEntryUpdate(BaseSchema):
    date: Optional[datetime] = None
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    reference: Optional[str] = None
    total_debit: Optional[float] = Field(None, ge=0)
    total_credit: Optional[float] = Field(None, ge=0)


class JournalEntryResponse(JournalEntryBase):
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    status: str


# Inventory schemas
class InventoryItemBase(BaseSchema):
    sku: str = Field(..., min_length=1, max_length=50)
    product_name: str = Field(..., min_length=1, max_length=200)
    category: str
    quantity: int = Field(..., ge=0)
    reorder_level: int = Field(..., ge=0)
    unit_price: float = Field(..., ge=0)
    location: str


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemUpdate(BaseSchema):
    sku: Optional[str] = Field(None, min_length=1, max_length=50)
    product_name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=0)
    reorder_level: Optional[int] = Field(None, ge=0)
    unit_price: Optional[float] = Field(None, ge=0)
    location: Optional[str] = None


class InventoryItemResponse(InventoryItemBase):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime


# HR schemas
class EmployeeBase(BaseSchema):
    employee_id: str = Field(..., min_length=1, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    department: str
    position: str
    hire_date: datetime
    salary: float = Field(..., gt=0)


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseSchema):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    salary: Optional[float] = Field(None, gt=0)


class EmployeeResponse(EmployeeBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Sales schemas
class SalesOrderBase(BaseSchema):
    customer_name: str = Field(..., min_length=1, max_length=200)
    customer_email: EmailStr
    order_date: datetime
    total_amount: float = Field(..., gt=0)
    status: str
    payment_method: Optional[str] = None


class SalesOrderCreate(SalesOrderBase):
    created_by: str


class SalesOrderUpdate(BaseSchema):
    customer_name: Optional[str] = Field(None, min_length=1, max_length=200)
    customer_email: Optional[EmailStr] = None
    total_amount: Optional[float] = Field(None, gt=0)
    status: Optional[str] = None
    payment_method: Optional[str] = None


class SalesOrderResponse(SalesOrderBase):
    id: str
    order_number: str
    created_by: str
    created_at: datetime
    updated_at: datetime


# Generic response schemas
class MessageResponse(BaseSchema):
    success: bool
    message: str


class PaginatedResponse(BaseSchema):
    total: int
    page: int
    page_size: int
    total_pages: int
    data: List[dict]


class ErrorResponse(BaseSchema):
    success: bool = False
    message: str
    details: Optional[dict] = None
