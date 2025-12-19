"""
Sales Service Client
Handles communication with the Sales service
"""

from typing import List, Dict, Any, Optional
import logging
from app.utils.http_client import HTTPClient
from app.config import settings

logger = logging.getLogger(__name__)


class SalesServiceClient:
    """
    Client for communicating with Sales service
    
    Provides methods to fetch sales data, product demand, and analytics
    """
    
    # Sales service base URL (from environment or config)
    BASE_URL = getattr(settings, 'SALES_SERVICE_URL', 'http://localhost:5001')
    
    @staticmethod
    async def get_product_sales_data(
        product_id: str,
        tenant_id: str,
        days: int = 30,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get sales data for a specific product
        
        Args:
            product_id: Product ID
            tenant_id: Tenant ID
            days: Number of days to fetch data for
            auth_token: Optional authentication token
            
        Returns:
            Dictionary with sales data
            
        Example response:
            {
                "product_id": "PRD-123",
                "total_quantity_sold": 150,
                "total_revenue": 180000.00,
                "average_daily_sales": 5.0,
                "sales_trend": "increasing",
                "last_sale_date": "2024-01-15T10:00:00Z"
            }
        """
        url = f"{SalesServiceClient.BASE_URL}/api/sales/products/{product_id}/analytics"
        
        headers = {
            "X-Tenant-ID": tenant_id
        }
        
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        params = {"days": days}
        
        try:
            response = await HTTPClient.get(url, headers=headers, params=params)
            data = response.json()
            
            logger.info(f"Fetched sales data for product {product_id}: {data.get('total_quantity_sold', 0)} units sold")
            
            return data
        except Exception as e:
            logger.error(f"Failed to fetch sales data for product {product_id}: {str(e)}")
            # Return default data on error
            return {
                "product_id": product_id,
                "total_quantity_sold": 0,
                "total_revenue": 0.0,
                "average_daily_sales": 0.0,
                "sales_trend": "unknown",
                "error": str(e)
            }
    
    @staticmethod
    async def get_product_demand_forecast(
        product_id: str,
        tenant_id: str,
        forecast_days: int = 30,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get demand forecast for a product
        
        Args:
            product_id: Product ID
            tenant_id: Tenant ID
            forecast_days: Number of days to forecast
            auth_token: Optional authentication token
            
        Returns:
            Dictionary with demand forecast
            
        Example response:
            {
                "product_id": "PRD-123",
                "forecast_days": 30,
                "predicted_demand": 180,
                "confidence_level": 0.85,
                "recommended_stock_level": 200
            }
        """
        url = f"{SalesServiceClient.BASE_URL}/api/sales/products/{product_id}/forecast"
        
        headers = {
            "X-Tenant-ID": tenant_id
        }
        
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        params = {"forecast_days": forecast_days}
        
        try:
            response = await HTTPClient.get(url, headers=headers, params=params)
            data = response.json()
            
            logger.info(
                f"Fetched demand forecast for product {product_id}: "
                f"{data.get('predicted_demand', 0)} units predicted"
            )
            
            return data
        except Exception as e:
            logger.error(f"Failed to fetch demand forecast for product {product_id}: {str(e)}")
            return {
                "product_id": product_id,
                "forecast_days": forecast_days,
                "predicted_demand": 0,
                "confidence_level": 0.0,
                "error": str(e)
            }
    
    @staticmethod
    async def get_top_selling_products(
        tenant_id: str,
        limit: int = 10,
        days: int = 30,
        auth_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get top selling products
        
        Args:
            tenant_id: Tenant ID
            limit: Number of products to return
            days: Number of days to analyze
            auth_token: Optional authentication token
            
        Returns:
            List of top selling products with sales data
            
        Example response:
            [
                {
                    "product_id": "PRD-123",
                    "product_name": "Laptop",
                    "quantity_sold": 150,
                    "revenue": 180000.00,
                    "rank": 1
                }
            ]
        """
        url = f"{SalesServiceClient.BASE_URL}/api/sales/products/top-selling"
        
        headers = {
            "X-Tenant-ID": tenant_id
        }
        
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        params = {
            "limit": limit,
            "days": days
        }
        
        try:
            response = await HTTPClient.get(url, headers=headers, params=params)
            data = response.json()
            
            logger.info(f"Fetched {len(data)} top selling products for tenant {tenant_id}")
            
            return data
        except Exception as e:
            logger.error(f"Failed to fetch top selling products: {str(e)}")
            return []
    
    @staticmethod
    async def check_product_availability(
        product_id: str,
        quantity: int,
        tenant_id: str,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if product quantity is available for sale
        
        Args:
            product_id: Product ID
            quantity: Requested quantity
            tenant_id: Tenant ID
            auth_token: Optional authentication token
            
        Returns:
            Dictionary with availability status
            
        Example response:
            {
                "product_id": "PRD-123",
                "requested_quantity": 10,
                "available": true,
                "current_stock": 50,
                "reserved_quantity": 5,
                "available_quantity": 45
            }
        """
        url = f"{SalesServiceClient.BASE_URL}/api/sales/products/{product_id}/check-availability"
        
        headers = {
            "X-Tenant-ID": tenant_id,
            "Content-Type": "application/json"
        }
        
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        payload = {
            "quantity": quantity
        }
        
        try:
            response = await HTTPClient.post(url, json=payload, headers=headers)
            data = response.json()
            
            logger.info(
                f"Checked availability for product {product_id}: "
                f"{data.get('available', False)}"
            )
            
            return data
        except Exception as e:
            logger.error(f"Failed to check product availability: {str(e)}")
            return {
                "product_id": product_id,
                "requested_quantity": quantity,
                "available": False,
                "error": str(e)
            }
    
    @staticmethod
    async def get_sales_summary(
        tenant_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get sales summary for tenant
        
        Args:
            tenant_id: Tenant ID
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)
            auth_token: Optional authentication token
            
        Returns:
            Dictionary with sales summary
            
        Example response:
            {
                "total_orders": 1250,
                "total_revenue": 1500000.00,
                "total_items_sold": 5000,
                "average_order_value": 1200.00,
                "period": {
                    "start": "2024-01-01",
                    "end": "2024-01-31"
                }
            }
        """
        url = f"{SalesServiceClient.BASE_URL}/api/sales/summary"
        
        headers = {
            "X-Tenant-ID": tenant_id
        }
        
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        try:
            response = await HTTPClient.get(url, headers=headers, params=params)
            data = response.json()
            
            logger.info(
                f"Fetched sales summary for tenant {tenant_id}: "
                f"{data.get('total_revenue', 0)} revenue"
            )
            
            return data
        except Exception as e:
            logger.error(f"Failed to fetch sales summary: {str(e)}")
            return {
                "total_orders": 0,
                "total_revenue": 0.0,
                "total_items_sold": 0,
                "error": str(e)
            }
