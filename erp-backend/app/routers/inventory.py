"""
Inventory module router - Products
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

from app.database import get_db
from app.services.product_service import ProductService
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


@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Product",
    description="Create a new product in inventory"
)
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.CREATE_INVENTORY)),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Create a new product
    
    Requires CREATE_INVENTORY permission
    """
    try:
        product = await ProductService.create_product(db, product_data, tenant.tenant_id)
        return ProductService.to_response(product)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create product: {str(e)}"
        )


@router.get(
    "/products",
    response_model=dict,
    summary="List Products",
    description="Get all products with filtering and pagination"
)
async def list_products(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.VIEW_INVENTORY)),
    tenant: TenantContext = Depends(get_tenant_context),
    category: ProductCategory = Query(None, description="Filter by category"),
    status_filter: ProductStatus = Query(None, alias="status", description="Filter by status"),
    is_active: bool = Query(None, description="Filter by active status"),
    needs_reorder: bool = Query(None, description="Filter products needing reorder"),
    search: str = Query(None, description="Search in name, SKU, or description"),
    min_price: float = Query(None, ge=0, description="Minimum price"),
    max_price: float = Query(None, ge=0, description="Maximum price"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results")
):
    """
    List products with filtering and pagination
    
    Requires VIEW_INVENTORY permission
    """
    try:
        filters = ProductListFilter(
            category=category,
            status=status_filter,
            is_active=is_active,
            needs_reorder=needs_reorder,
            search=search,
            min_price=min_price,
            max_price=max_price,
            skip=skip,
            limit=limit
        )
        
        products, total_count = await ProductService.list_products(db, tenant.tenant_id, filters)
        
        return {
            "products": [ProductService.to_response(p) for p in products],
            "total": total_count,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error listing products: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list products: {str(e)}"
        )


@router.get(
    "/products/{product_id}",
    response_model=ProductResponse,
    summary="Get Product",
    description="Get a specific product by ID"
)
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.VIEW_INVENTORY)),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Get a specific product
    
    Requires VIEW_INVENTORY permission
    """
    try:
        product = await ProductService.get_product(db, product_id, tenant.tenant_id)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )
        
        return ProductService.to_response(product)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving product: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve product: {str(e)}"
        )


@router.get(
    "/products/sku/{sku}",
    response_model=ProductResponse,
    summary="Get Product by SKU",
    description="Get a specific product by SKU"
)
async def get_product_by_sku(
    sku: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.VIEW_INVENTORY)),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Get a product by SKU
    
    Requires VIEW_INVENTORY permission
    """
    try:
        product = await ProductService.get_by_sku(db, sku, tenant.tenant_id)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with SKU '{sku}' not found"
            )
        
        return ProductService.to_response(product)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving product by SKU: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve product: {str(e)}"
        )


@router.put(
    "/products/{product_id}",
    response_model=ProductResponse,
    summary="Update Product",
    description="Update an existing product"
)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.EDIT_INVENTORY)),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Update a product
    
    Requires EDIT_INVENTORY permission
    """
    try:
        # Set updated_by if not provided
        if not product_data.updated_by:
            product_data.updated_by = current_user.user_id
        
        product = await ProductService.update_product(db, product_id, product_data, tenant.tenant_id)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )
        
        return ProductService.to_response(product)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update product: {str(e)}"
        )


@router.delete(
    "/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Product",
    description="Delete a product (soft delete by default)"
)
async def delete_product(
    product_id: str,
    hard_delete: bool = Query(False, description="Perform hard delete instead of soft delete"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.DELETE_INVENTORY)),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Delete a product
    
    By default, performs soft delete (sets status to discontinued).
    Use hard_delete=true for permanent deletion.
    
    Requires DELETE_INVENTORY permission
    """
    try:
        deleted = await ProductService.delete_product(
            db, product_id, tenant.tenant_id, soft_delete=not hard_delete
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete product: {str(e)}"
        )


@router.post(
    "/products/{product_id}/adjust-stock",
    response_model=ProductResponse,
    summary="Adjust Product Stock",
    description="Adjust product stock quantity"
)
async def adjust_product_stock(
    product_id: str,
    adjustment: ProductStockAdjustment,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.EDIT_INVENTORY)),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Adjust product stock quantity
    
    Requires EDIT_INVENTORY permission
    """
    try:
        # Set adjusted_by if not provided
        if not adjustment.adjusted_by:
            adjustment.adjusted_by = current_user.user_id
        
        product = await ProductService.adjust_stock(db, product_id, adjustment, tenant.tenant_id)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )
        
        return ProductService.to_response(product)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adjusting stock: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to adjust stock: {str(e)}"
        )


@router.get(
    "/products/low-stock/list",
    response_model=List[ProductResponse],
    summary="Get Low Stock Products",
    description="Get products that need reordering"
)
async def get_low_stock_products(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.VIEW_INVENTORY)),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Get products that need reordering
    
    Requires VIEW_INVENTORY permission
    """
    try:
        products = await ProductService.get_low_stock_products(db, tenant.tenant_id)
        return [ProductService.to_response(p) for p in products]
    except Exception as e:
        logger.error(f"Error getting low stock products: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get low stock products: {str(e)}"
        )


@router.get(
    "/products/statistics/summary",
    response_model=dict,
    summary="Get Product Statistics",
    description="Get product statistics for current tenant"
)
async def get_product_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.VIEW_INVENTORY)),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Get product statistics
    
    Requires VIEW_INVENTORY permission
    """
    try:
        stats = await ProductService.get_product_statistics(db, tenant.tenant_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting product statistics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get product statistics: {str(e)}"
        )
