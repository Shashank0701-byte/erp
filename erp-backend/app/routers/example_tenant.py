"""
Example router demonstrating tenant context usage
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.dependencies.tenant import (
    get_tenant_context,
    get_optional_tenant_context,
    require_tenant_setting
)
from app.schemas.tenant import TenantContext

router = APIRouter(prefix="/api/example", tags=["Example - Tenant Usage"])


@router.get("/tenant-info")
async def get_tenant_info(tenant: TenantContext = Depends(get_tenant_context)):
    """
    Example: Get current tenant information
    
    Demonstrates basic tenant context extraction
    """
    return {
        "tenant_id": tenant.tenant_id,
        "tenant_name": tenant.tenant_name,
        "domain": tenant.domain,
        "is_active": tenant.is_active,
        "settings": tenant.settings
    }


@router.get("/tenant-users")
async def get_tenant_users(tenant: TenantContext = Depends(get_tenant_context)):
    """
    Example: Get users scoped to current tenant
    
    In production, this would query the database with tenant filter:
    users = db.query(User).filter(User.tenant_id == tenant.tenant_id).all()
    """
    # Mock data for demonstration
    mock_users = {
        "tenant-1": [
            {"id": "u1", "name": "Alice", "email": "alice@acme.com"},
            {"id": "u2", "name": "Bob", "email": "bob@acme.com"}
        ],
        "tenant-2": [
            {"id": "u3", "name": "Charlie", "email": "charlie@techcorp.com"},
            {"id": "u4", "name": "Diana", "email": "diana@techcorp.com"}
        ]
    }
    
    users = mock_users.get(tenant.tenant_id, [])
    
    return {
        "tenant": tenant.tenant_name,
        "users": users,
        "count": len(users)
    }


@router.get("/optional-tenant")
async def optional_tenant_route(
    tenant: TenantContext | None = Depends(get_optional_tenant_context)
):
    """
    Example: Route that works with or without tenant context
    
    Useful for public endpoints that can return tenant-specific or general data
    """
    if tenant:
        return {
            "mode": "tenant-specific",
            "tenant": tenant.tenant_name,
            "message": f"Data for {tenant.tenant_name}"
        }
    else:
        return {
            "mode": "public",
            "message": "Public data - no tenant context"
        }


@router.get("/premium-feature")
async def premium_feature(
    tenant: TenantContext = Depends(require_tenant_setting("premium_enabled", True))
):
    """
    Example: Route requiring specific tenant setting
    
    Only accessible if tenant has premium_enabled=True in settings
    """
    return {
        "message": "Premium feature accessed",
        "tenant": tenant.tenant_name,
        "features": ["Advanced Analytics", "Custom Reports", "API Access"]
    }


@router.post("/tenant-data")
async def create_tenant_data(
    data: dict,
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Example: Create data scoped to tenant
    
    In production:
    new_record = Model(
        **data,
        tenant_id=tenant.tenant_id
    )
    db.add(new_record)
    db.commit()
    """
    return {
        "message": "Data created",
        "tenant_id": tenant.tenant_id,
        "tenant_name": tenant.tenant_name,
        "data": data
    }


@router.get("/tenant-settings/{setting_key}")
async def get_tenant_setting(
    setting_key: str,
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Example: Get specific tenant setting
    """
    settings = tenant.settings or {}
    
    if setting_key not in settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{setting_key}' not found for tenant"
        )
    
    return {
        "tenant": tenant.tenant_name,
        "setting_key": setting_key,
        "setting_value": settings[setting_key]
    }


@router.get("/tenant-stats")
async def get_tenant_stats(tenant: TenantContext = Depends(get_tenant_context)):
    """
    Example: Get statistics for current tenant
    
    Demonstrates how to aggregate tenant-specific data
    """
    # Mock statistics
    mock_stats = {
        "tenant-1": {
            "total_users": 150,
            "active_users": 120,
            "total_orders": 1250,
            "revenue": 125000.50
        },
        "tenant-2": {
            "total_users": 85,
            "active_users": 70,
            "total_orders": 680,
            "revenue": 68500.75
        }
    }
    
    stats = mock_stats.get(tenant.tenant_id, {
        "total_users": 0,
        "active_users": 0,
        "total_orders": 0,
        "revenue": 0.0
    })
    
    return {
        "tenant": tenant.tenant_name,
        "statistics": stats
    }
