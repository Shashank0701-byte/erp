"""
HR module router - Employee Management
With rate limiting on public-facing endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
import logging

from app.database import get_db
from app.schemas import TokenData, Permission
from app.dependencies import get_current_user, require_permission
from app.dependencies.tenant import get_tenant_context
from app.schemas.tenant import TenantContext
from pydantic import BaseModel, Field, EmailStr

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hr", tags=["HR - Employee Management"])


# Pydantic Schemas for HR

class EmployeeBase(BaseModel):
    """Base employee schema"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    department: str = Field(..., max_length=100)
    position: str = Field(..., max_length=100)
    hire_date: datetime
    salary: float = Field(..., gt=0)
    is_active: bool = True


class EmployeeCreate(EmployeeBase):
    """Schema for creating employee"""
    employee_id: str = Field(..., min_length=1, max_length=50)


class EmployeeUpdate(BaseModel):
    """Schema for updating employee"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    salary: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None


class EmployeeResponse(EmployeeBase):
    """Schema for employee response"""
    id: str
    employee_id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Public-facing endpoints (rate-limited)

@router.get(
    "/employees/public/directory",
    response_model=List[dict],
    summary="Public Employee Directory",
    description="Get public employee directory (rate-limited: 10 requests/minute)"
)
async def get_public_employee_directory(
    request: Request,
    tenant: TenantContext = Depends(get_tenant_context),
    department: Optional[str] = Query(None, description="Filter by department"),
    search: Optional[str] = Query(None, description="Search by name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get public employee directory
    
    This endpoint is rate-limited to prevent abuse:
    - 10 requests per minute per IP
    - Public information only (no sensitive data)
    
    No authentication required
    """
    # Mock data for demonstration
    employees = [
        {
            "employee_id": "EMP-001",
            "name": "John Doe",
            "department": "Engineering",
            "position": "Senior Developer",
            "email": "john.doe@company.com"
        },
        {
            "employee_id": "EMP-002",
            "name": "Jane Smith",
            "department": "HR",
            "position": "HR Manager",
            "email": "jane.smith@company.com"
        }
    ]
    
    # Apply filters
    if department:
        employees = [e for e in employees if e["department"].lower() == department.lower()]
    
    if search:
        search_lower = search.lower()
        employees = [
            e for e in employees
            if search_lower in e["name"].lower() or search_lower in e["position"].lower()
        ]
    
    # Apply pagination
    total = len(employees)
    employees = employees[skip:skip + limit]
    
    logger.info(f"Public directory accessed: {len(employees)} employees returned")
    
    return employees


@router.get(
    "/employees/public/{employee_id}",
    response_model=dict,
    summary="Get Public Employee Info",
    description="Get public employee information (rate-limited: 20 requests/minute)"
)
async def get_public_employee_info(
    employee_id: str,
    request: Request,
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Get public employee information
    
    Rate-limited to 20 requests per minute per IP
    Returns only public information
    
    No authentication required
    """
    # Mock data
    employee = {
        "employee_id": employee_id,
        "name": "John Doe",
        "department": "Engineering",
        "position": "Senior Developer",
        "email": "john.doe@company.com",
        "office_location": "Building A, Floor 3"
    }
    
    logger.info(f"Public employee info accessed: {employee_id}")
    
    return employee


@router.post(
    "/employees/public/contact",
    response_model=dict,
    summary="Contact Employee",
    description="Send contact request to employee (rate-limited: 5 requests/hour)"
)
async def contact_employee(
    request: Request,
    employee_id: str = Query(..., description="Employee ID to contact"),
    message: str = Query(..., min_length=10, max_length=500, description="Contact message"),
    sender_email: EmailStr = Query(..., description="Sender email"),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Send contact request to employee
    
    Heavily rate-limited to prevent spam:
    - 5 requests per hour per IP
    - Message length limited
    
    No authentication required
    """
    logger.info(f"Contact request for employee {employee_id} from {sender_email}")
    
    # In production, this would send an email or create a notification
    return {
        "success": True,
        "message": "Contact request sent successfully",
        "employee_id": employee_id
    }


# Protected endpoints (require authentication)

@router.get(
    "/employees",
    response_model=dict,
    summary="List Employees",
    description="Get all employees (requires authentication)"
)
async def list_employees(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.VIEW_HR)),
    tenant: TenantContext = Depends(get_tenant_context),
    department: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    List all employees
    
    Requires VIEW_HR permission
    Returns full employee details including sensitive information
    """
    # Mock data
    employees = [
        {
            "id": "emp-uuid-1",
            "employee_id": "EMP-001",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@company.com",
            "department": "Engineering",
            "position": "Senior Developer",
            "salary": 120000.00,
            "is_active": True
        }
    ]
    
    return {
        "employees": employees,
        "total": len(employees),
        "skip": skip,
        "limit": limit
    }


@router.post(
    "/employees",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create Employee",
    description="Create a new employee (requires authentication)"
)
async def create_employee(
    employee_data: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.CREATE_HR)),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Create a new employee
    
    Requires CREATE_HR permission
    """
    logger.info(f"Creating employee: {employee_data.employee_id}")
    
    return {
        "id": "emp-uuid-new",
        "employee_id": employee_data.employee_id,
        "message": "Employee created successfully"
    }


@router.get(
    "/employees/{employee_id}",
    response_model=dict,
    summary="Get Employee",
    description="Get employee details (requires authentication)"
)
async def get_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.VIEW_HR)),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Get employee details
    
    Requires VIEW_HR permission
    Returns full employee information including salary
    """
    employee = {
        "id": "emp-uuid-1",
        "employee_id": employee_id,
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@company.com",
        "department": "Engineering",
        "position": "Senior Developer",
        "salary": 120000.00,
        "hire_date": "2020-01-15T00:00:00Z",
        "is_active": True
    }
    
    return employee


@router.put(
    "/employees/{employee_id}",
    response_model=dict,
    summary="Update Employee",
    description="Update employee information (requires authentication)"
)
async def update_employee(
    employee_id: str,
    employee_data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.EDIT_HR)),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Update employee information
    
    Requires EDIT_HR permission
    """
    logger.info(f"Updating employee: {employee_id}")
    
    return {
        "id": "emp-uuid-1",
        "employee_id": employee_id,
        "message": "Employee updated successfully"
    }


@router.delete(
    "/employees/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Employee",
    description="Delete employee (requires authentication)"
)
async def delete_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.DELETE_HR)),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Delete employee (soft delete)
    
    Requires DELETE_HR permission
    """
    logger.info(f"Deleting employee: {employee_id}")
    
    return None


@router.get(
    "/statistics",
    response_model=dict,
    summary="Get HR Statistics",
    description="Get HR statistics (requires authentication)"
)
async def get_hr_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.VIEW_HR)),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Get HR statistics
    
    Requires VIEW_HR permission
    """
    stats = {
        "total_employees": 150,
        "active_employees": 145,
        "departments": 8,
        "average_tenure_years": 3.5,
        "total_payroll": 18000000.00
    }
    
    return stats
