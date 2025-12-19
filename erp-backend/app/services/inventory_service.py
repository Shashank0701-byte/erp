"""
Inventory Service with Sales Integration
Enhanced product service with real-time sales data
"""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
import logging

from app.services.product_service import ProductService
from app.clients.sales_client import SalesServiceClient
from app.models.product import Product

logger = logging.getLogger(__name__)


class InventoryService:
    """
    Enhanced inventory service with sales data integration
    
    Combines product inventory data with real-time sales analytics
    """
    
    @staticmethod
    async def get_product_with_sales_data(
        db: AsyncSession,
        product_id: str,
        tenant_id: str,
        auth_token: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get product with integrated sales data
        
        Args:
            db: Database session
            product_id: Product ID
            tenant_id: Tenant ID
            auth_token: Optional authentication token
            days: Number of days for sales data
            
        Returns:
            Dictionary with product and sales data combined
        """
        # Get product from database
        product = await ProductService.get_product(db, product_id, tenant_id)
        
        if not product:
            return None
        
        # Fetch sales data from Sales service
        sales_data = await SalesServiceClient.get_product_sales_data(
            product_id=product_id,
            tenant_id=tenant_id,
            days=days,
            auth_token=auth_token
        )
        
        # Combine product and sales data
        product_response = ProductService.to_response(product)
        
        return {
            **product_response.model_dump(),
            "sales_analytics": {
                "total_quantity_sold": sales_data.get("total_quantity_sold", 0),
                "total_revenue": sales_data.get("total_revenue", 0.0),
                "average_daily_sales": sales_data.get("average_daily_sales", 0.0),
                "sales_trend": sales_data.get("sales_trend", "unknown"),
                "last_sale_date": sales_data.get("last_sale_date"),
                "period_days": days
            }
        }
    
    @staticmethod
    async def get_product_with_demand_forecast(
        db: AsyncSession,
        product_id: str,
        tenant_id: str,
        auth_token: Optional[str] = None,
        forecast_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get product with demand forecast
        
        Args:
            db: Database session
            product_id: Product ID
            tenant_id: Tenant ID
            auth_token: Optional authentication token
            forecast_days: Number of days to forecast
            
        Returns:
            Dictionary with product and forecast data
        """
        # Get product from database
        product = await ProductService.get_product(db, product_id, tenant_id)
        
        if not product:
            return None
        
        # Fetch demand forecast from Sales service
        forecast_data = await SalesServiceClient.get_product_demand_forecast(
            product_id=product_id,
            tenant_id=tenant_id,
            forecast_days=forecast_days,
            auth_token=auth_token
        )
        
        # Combine product and forecast data
        product_response = ProductService.to_response(product)
        
        # Calculate reorder recommendation
        predicted_demand = forecast_data.get("predicted_demand", 0)
        current_stock = product.quantity_on_hand
        recommended_stock = forecast_data.get("recommended_stock_level", product.reorder_quantity)
        
        should_reorder = current_stock < recommended_stock
        reorder_quantity = max(0, recommended_stock - current_stock)
        
        return {
            **product_response.model_dump(),
            "demand_forecast": {
                "forecast_days": forecast_days,
                "predicted_demand": predicted_demand,
                "confidence_level": forecast_data.get("confidence_level", 0.0),
                "recommended_stock_level": recommended_stock,
                "current_stock": current_stock,
                "should_reorder": should_reorder,
                "recommended_reorder_quantity": reorder_quantity
            }
        }
    
    @staticmethod
    async def get_inventory_dashboard(
        db: AsyncSession,
        tenant_id: str,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive inventory dashboard with sales integration
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            auth_token: Optional authentication token
            
        Returns:
            Dictionary with dashboard data
        """
        # Get product statistics
        product_stats = await ProductService.get_product_statistics(db, tenant_id)
        
        # Get top selling products from Sales service
        top_selling = await SalesServiceClient.get_top_selling_products(
            tenant_id=tenant_id,
            limit=10,
            days=30,
            auth_token=auth_token
        )
        
        # Get sales summary
        sales_summary = await SalesServiceClient.get_sales_summary(
            tenant_id=tenant_id,
            auth_token=auth_token
        )
        
        # Get low stock products
        low_stock_products = await ProductService.get_low_stock_products(db, tenant_id)
        
        return {
            "inventory_stats": product_stats,
            "sales_summary": {
                "total_revenue": sales_summary.get("total_revenue", 0.0),
                "total_orders": sales_summary.get("total_orders", 0),
                "total_items_sold": sales_summary.get("total_items_sold", 0),
                "average_order_value": sales_summary.get("average_order_value", 0.0)
            },
            "top_selling_products": top_selling,
            "low_stock_alerts": [
                {
                    "product_id": p.id,
                    "sku": p.sku,
                    "name": p.name,
                    "current_stock": p.quantity_on_hand,
                    "reorder_level": p.reorder_level,
                    "reorder_quantity": p.reorder_quantity
                }
                for p in low_stock_products[:10]  # Top 10 low stock items
            ]
        }
    
    @staticmethod
    async def smart_reorder_recommendation(
        db: AsyncSession,
        product_id: str,
        tenant_id: str,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get smart reorder recommendation based on sales data
        
        Args:
            db: Database session
            product_id: Product ID
            tenant_id: Tenant ID
            auth_token: Optional authentication token
            
        Returns:
            Dictionary with reorder recommendation
        """
        # Get product
        product = await ProductService.get_product(db, product_id, tenant_id)
        
        if not product:
            return None
        
        # Get sales data (last 30 days)
        sales_data = await SalesServiceClient.get_product_sales_data(
            product_id=product_id,
            tenant_id=tenant_id,
            days=30,
            auth_token=auth_token
        )
        
        # Get demand forecast (next 30 days)
        forecast_data = await SalesServiceClient.get_product_demand_forecast(
            product_id=product_id,
            tenant_id=tenant_id,
            forecast_days=30,
            auth_token=auth_token
        )
        
        # Calculate smart recommendation
        average_daily_sales = sales_data.get("average_daily_sales", 0.0)
        predicted_demand = forecast_data.get("predicted_demand", 0)
        current_stock = product.quantity_on_hand
        
        # Calculate days of stock remaining
        days_of_stock = (
            current_stock / average_daily_sales 
            if average_daily_sales > 0 
            else float('inf')
        )
        
        # Determine if reorder is needed
        needs_reorder = days_of_stock < 14  # Less than 2 weeks of stock
        
        # Calculate recommended order quantity
        # Target: 30 days of stock based on forecast
        target_stock = predicted_demand
        recommended_order = max(0, target_stock - current_stock)
        
        # Round up to nearest reorder quantity
        if recommended_order > 0:
            reorder_qty = product.reorder_quantity
            recommended_order = ((recommended_order + reorder_qty - 1) // reorder_qty) * reorder_qty
        
        return {
            "product_id": product_id,
            "product_name": product.name,
            "sku": product.sku,
            "current_stock": current_stock,
            "reorder_level": product.reorder_level,
            "standard_reorder_quantity": product.reorder_quantity,
            "sales_analytics": {
                "average_daily_sales": average_daily_sales,
                "total_sold_30_days": sales_data.get("total_quantity_sold", 0),
                "sales_trend": sales_data.get("sales_trend", "unknown")
            },
            "forecast": {
                "predicted_demand_30_days": predicted_demand,
                "confidence_level": forecast_data.get("confidence_level", 0.0)
            },
            "recommendation": {
                "needs_reorder": needs_reorder,
                "days_of_stock_remaining": round(days_of_stock, 1),
                "recommended_order_quantity": recommended_order,
                "target_stock_level": target_stock,
                "urgency": "high" if days_of_stock < 7 else "medium" if days_of_stock < 14 else "low"
            }
        }
