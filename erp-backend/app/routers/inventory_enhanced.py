"""
Inventory module router - Products with Sales Integration
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

from app.database import get_db
from app.services.product_service import ProductService
from app.services.inventory_service import InventoryService
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductStockAdjustment,
    ProductListFilter,
    ProductCategory,
    ProductStatus
)
from app.schemas import TokenData, Permission
from app.dependencies import get_current_user, require_permission
from app.dependencies.tenant import get_tenant_context
from app.schemas.tenant import TenantContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/inventory", tags=["Inventory - Products"])


# ... (existing endpoints remain the same) ...


# New endpoints with Sales integration

@router.get(
    "/products/{product_id}/with-sales-data",
    response_model=dict,
    summary="Get Product with Sales Data",
    description="Get product with integrated real-time sales analytics"
)
async def get_product_with_sales_data(
    product_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.VIEW_INVENTORY)),
    tenant: TenantContext = Depends(get_tenant_context),
    days: int = Query(30, ge=1, le=365, description="Number of days for sales data")
):
    """
    Get product with integrated sales analytics
    
    Fetches product data from inventory and combines it with real-time
    sales data from the Sales service.
    
    Requires VIEW_INVENTORY permission
    """
    try:
        # Extract auth token from request
        auth_token = request.headers.get("Authorization", "").replace("Bearer ", "")
        
        product_data = await InventoryService.get_product_with_sales_data(
            db=db,
            product_id=product_id,
            tenant_id=tenant.tenant_id,
            auth_token=auth_token if auth_token else None,
            days=days
        )
        
        if not product_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )
        
        return product_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product with sales data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get product with sales data: {str(e)}"
        )


@router.get(
    "/products/{product_id}/demand-forecast",
    response_model=dict,
    summary="Get Product Demand Forecast",
    description="Get product with demand forecast from Sales service"
)
async def get_product_demand_forecast(
    product_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.VIEW_INVENTORY)),
    tenant: TenantContext = Depends(get_tenant_context),
    forecast_days: int = Query(30, ge=1, le=365, description="Number of days to forecast")
):
    """
    Get product with demand forecast
    
    Combines inventory data with AI-powered demand forecasting
    from the Sales service.
    
    Requires VIEW_INVENTORY permission
    """
    try:
        auth_token = request.headers.get("Authorization", "").replace("Bearer ", "")
        
        forecast_data = await InventoryService.get_product_with_demand_forecast(
            db=db,
            product_id=product_id,
            tenant_id=tenant.tenant_id,
            auth_token=auth_token if auth_token else None,
            forecast_days=forecast_days
        )
        
        if not forecast_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )
        
        return forecast_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting demand forecast: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get demand forecast: {str(e)}"
        )


@router.get(
    "/dashboard",
    response_model=dict,
    summary="Get Inventory Dashboard",
    description="Get comprehensive inventory dashboard with sales integration"
)
async def get_inventory_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.VIEW_INVENTORY)),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Get comprehensive inventory dashboard
    
    Combines inventory statistics with real-time sales data,
    top-selling products, and low stock alerts.
    
    Requires VIEW_INVENTORY permission
    """
    try:
        auth_token = request.headers.get("Authorization", "").replace("Bearer ", "")
        
        dashboard_data = await InventoryService.get_inventory_dashboard(
            db=db,
            tenant_id=tenant.tenant_id,
            auth_token=auth_token if auth_token else None
        )
        
        return dashboard_data
    except Exception as e:
        logger.error(f"Error getting inventory dashboard: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get inventory dashboard: {str(e)}"
        )


@router.get(
    "/products/{product_id}/reorder-recommendation",
    response_model=dict,
    summary="Get Smart Reorder Recommendation",
    description="Get AI-powered reorder recommendation based on sales data"
)
async def get_reorder_recommendation(
    product_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.VIEW_INVENTORY)),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Get smart reorder recommendation
    
    Analyzes historical sales data and demand forecast to provide
    intelligent reorder recommendations.
    
    Requires VIEW_INVENTORY permission
    """
    try:
        auth_token = request.headers.get("Authorization", "").replace("Bearer ", "")
        
        recommendation = await InventoryService.smart_reorder_recommendation(
            db=db,
            product_id=product_id,
            tenant_id=tenant.tenant_id,
            auth_token=auth_token if auth_token else None
        )
        
        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )
        
        return recommendation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting reorder recommendation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get reorder recommendation: {str(e)}"
        )
