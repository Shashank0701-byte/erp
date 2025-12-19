"""
Product Service Layer
Handles business logic for product CRUD operations
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import List, Optional
import logging

from app.models.product import Product, ProductStatus
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductStockAdjustment,
    ProductListFilter
)

logger = logging.getLogger(__name__)


class ProductService:
    """Service layer for Product operations"""
    
    @staticmethod
    async def create_product(
        db: AsyncSession,
        product_data: ProductCreate,
        tenant_id: str
    ) -> Product:
        """
        Create a new product
        
        Args:
            db: Database session
            product_data: Product creation data
            tenant_id: Tenant ID
            
        Returns:
            Created product
            
        Raises:
            ValueError: If SKU already exists for tenant
        """
        # Check if SKU already exists for this tenant
        existing = await ProductService.get_by_sku(db, product_data.sku, tenant_id)
        if existing:
            raise ValueError(f"Product with SKU '{product_data.sku}' already exists")
        
        # Create product
        product = Product(
            tenant_id=tenant_id,
            sku=product_data.sku,
            name=product_data.name,
            description=product_data.description,
            category=product_data.category,
            unit_of_measure=product_data.unit_of_measure,
            unit_price=product_data.unit_price,
            cost_price=product_data.cost_price,
            quantity_on_hand=product_data.quantity_on_hand,
            reorder_level=product_data.reorder_level,
            reorder_quantity=product_data.reorder_quantity,
            location=product_data.location,
            barcode=product_data.barcode,
            image_url=product_data.image_url,
            is_active=product_data.is_active,
            status=product_data.status,
            created_by=product_data.created_by
        )
        
        db.add(product)
        await db.commit()
        await db.refresh(product)
        
        logger.info(f"Product created: {product.id} (SKU: {product.sku}) for tenant {tenant_id}")
        
        return product
    
    @staticmethod
    async def get_product(
        db: AsyncSession,
        product_id: str,
        tenant_id: str
    ) -> Optional[Product]:
        """
        Get a product by ID
        
        Args:
            db: Database session
            product_id: Product ID
            tenant_id: Tenant ID
            
        Returns:
            Product if found, None otherwise
        """
        query = select(Product).where(
            and_(
                Product.id == product_id,
                Product.tenant_id == tenant_id
            )
        )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_sku(
        db: AsyncSession,
        sku: str,
        tenant_id: str
    ) -> Optional[Product]:
        """
        Get a product by SKU
        
        Args:
            db: Database session
            sku: Product SKU
            tenant_id: Tenant ID
            
        Returns:
            Product if found, None otherwise
        """
        query = select(Product).where(
            and_(
                Product.sku == sku,
                Product.tenant_id == tenant_id
            )
        )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_products(
        db: AsyncSession,
        tenant_id: str,
        filters: ProductListFilter
    ) -> tuple[List[Product], int]:
        """
        List products with filtering and pagination
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            filters: Filter parameters
            
        Returns:
            Tuple of (products list, total count)
        """
        # Base query
        query = select(Product).where(Product.tenant_id == tenant_id)
        
        # Apply filters
        if filters.category:
            query = query.where(Product.category == filters.category)
        
        if filters.status:
            query = query.where(Product.status == filters.status)
        
        if filters.is_active is not None:
            query = query.where(Product.is_active == filters.is_active)
        
        if filters.needs_reorder:
            query = query.where(Product.quantity_on_hand <= Product.reorder_level)
        
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    Product.name.ilike(search_term),
                    Product.sku.ilike(search_term),
                    Product.description.ilike(search_term)
                )
            )
        
        if filters.min_price is not None:
            query = query.where(Product.unit_price >= filters.min_price)
        
        if filters.max_price is not None:
            query = query.where(Product.unit_price <= filters.max_price)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total_count = total_result.scalar()
        
        # Apply pagination and ordering
        query = query.order_by(Product.name).offset(filters.skip).limit(filters.limit)
        
        # Execute query
        result = await db.execute(query)
        products = result.scalars().all()
        
        logger.info(f"Listed {len(products)} products (total: {total_count}) for tenant {tenant_id}")
        
        return products, total_count
    
    @staticmethod
    async def update_product(
        db: AsyncSession,
        product_id: str,
        product_data: ProductUpdate,
        tenant_id: str
    ) -> Optional[Product]:
        """
        Update a product
        
        Args:
            db: Database session
            product_id: Product ID
            product_data: Update data
            tenant_id: Tenant ID
            
        Returns:
            Updated product if found, None otherwise
            
        Raises:
            ValueError: If SKU already exists for another product
        """
        # Get existing product
        product = await ProductService.get_product(db, product_id, tenant_id)
        if not product:
            return None
        
        # Check SKU uniqueness if being updated
        if product_data.sku and product_data.sku != product.sku:
            existing = await ProductService.get_by_sku(db, product_data.sku, tenant_id)
            if existing and existing.id != product_id:
                raise ValueError(f"Product with SKU '{product_data.sku}' already exists")
        
        # Update fields
        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        
        await db.commit()
        await db.refresh(product)
        
        logger.info(f"Product updated: {product.id} for tenant {tenant_id}")
        
        return product
    
    @staticmethod
    async def delete_product(
        db: AsyncSession,
        product_id: str,
        tenant_id: str,
        soft_delete: bool = True
    ) -> bool:
        """
        Delete a product (soft or hard delete)
        
        Args:
            db: Database session
            product_id: Product ID
            tenant_id: Tenant ID
            soft_delete: If True, set status to discontinued; if False, delete from DB
            
        Returns:
            True if deleted, False if not found
        """
        product = await ProductService.get_product(db, product_id, tenant_id)
        if not product:
            return False
        
        if soft_delete:
            # Soft delete - set status to discontinued
            product.status = ProductStatus.DISCONTINUED
            product.is_active = False
            await db.commit()
            logger.info(f"Product soft deleted: {product.id} for tenant {tenant_id}")
        else:
            # Hard delete - remove from database
            await db.delete(product)
            await db.commit()
            logger.info(f"Product hard deleted: {product_id} for tenant {tenant_id}")
        
        return True
    
    @staticmethod
    async def adjust_stock(
        db: AsyncSession,
        product_id: str,
        adjustment: ProductStockAdjustment,
        tenant_id: str
    ) -> Optional[Product]:
        """
        Adjust product stock quantity
        
        Args:
            db: Database session
            product_id: Product ID
            adjustment: Stock adjustment data
            tenant_id: Tenant ID
            
        Returns:
            Updated product if found, None otherwise
            
        Raises:
            ValueError: If adjustment would result in negative stock
        """
        product = await ProductService.get_product(db, product_id, tenant_id)
        if not product:
            return None
        
        new_quantity = product.quantity_on_hand + adjustment.quantity_change
        
        if new_quantity < 0:
            raise ValueError(
                f"Stock adjustment would result in negative quantity. "
                f"Current: {product.quantity_on_hand}, Change: {adjustment.quantity_change}"
            )
        
        product.quantity_on_hand = new_quantity
        product.updated_by = adjustment.adjusted_by
        
        await db.commit()
        await db.refresh(product)
        
        logger.info(
            f"Stock adjusted for product {product.id}: "
            f"{adjustment.quantity_change:+d} (Reason: {adjustment.reason})"
        )
        
        return product
    
    @staticmethod
    async def get_low_stock_products(
        db: AsyncSession,
        tenant_id: str
    ) -> List[Product]:
        """
        Get products that need reordering
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            
        Returns:
            List of products below reorder level
        """
        query = select(Product).where(
            and_(
                Product.tenant_id == tenant_id,
                Product.quantity_on_hand <= Product.reorder_level,
                Product.is_active == True,
                Product.status == ProductStatus.ACTIVE
            )
        ).order_by(Product.quantity_on_hand)
        
        result = await db.execute(query)
        products = result.scalars().all()
        
        logger.info(f"Found {len(products)} low stock products for tenant {tenant_id}")
        
        return products
    
    @staticmethod
    async def get_product_statistics(
        db: AsyncSession,
        tenant_id: str
    ) -> dict:
        """
        Get product statistics for tenant
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            
        Returns:
            Dictionary with statistics
        """
        # Total products
        total_query = select(func.count()).select_from(Product).where(
            Product.tenant_id == tenant_id
        )
        total_result = await db.execute(total_query)
        total_products = total_result.scalar()
        
        # Active products
        active_query = select(func.count()).select_from(Product).where(
            and_(
                Product.tenant_id == tenant_id,
                Product.is_active == True
            )
        )
        active_result = await db.execute(active_query)
        active_products = active_result.scalar()
        
        # Low stock products
        low_stock_query = select(func.count()).select_from(Product).where(
            and_(
                Product.tenant_id == tenant_id,
                Product.quantity_on_hand <= Product.reorder_level
            )
        )
        low_stock_result = await db.execute(low_stock_query)
        low_stock_products = low_stock_result.scalar()
        
        # Total stock value
        value_query = select(
            func.sum(Product.quantity_on_hand * Product.cost_price)
        ).where(Product.tenant_id == tenant_id)
        value_result = await db.execute(value_query)
        total_stock_value = value_result.scalar() or 0.0
        
        return {
            "total_products": total_products,
            "active_products": active_products,
            "inactive_products": total_products - active_products,
            "low_stock_products": low_stock_products,
            "total_stock_value": round(total_stock_value, 2)
        }
    
    @staticmethod
    def to_response(product: Product) -> ProductResponse:
        """
        Convert Product model to ProductResponse schema
        
        Args:
            product: Product model instance
            
        Returns:
            ProductResponse schema
        """
        return ProductResponse(
            id=product.id,
            tenant_id=product.tenant_id,
            sku=product.sku,
            name=product.name,
            description=product.description,
            category=product.category,
            unit_of_measure=product.unit_of_measure,
            unit_price=product.unit_price,
            cost_price=product.cost_price,
            quantity_on_hand=product.quantity_on_hand,
            reorder_level=product.reorder_level,
            reorder_quantity=product.reorder_quantity,
            location=product.location,
            barcode=product.barcode,
            image_url=product.image_url,
            is_active=product.is_active,
            status=product.status,
            created_by=product.created_by,
            updated_by=product.updated_by,
            created_at=product.created_at,
            updated_at=product.updated_at,
            needs_reorder=product.needs_reorder,
            stock_value=product.stock_value,
            potential_revenue=product.potential_revenue,
            profit_margin=product.profit_margin
        )
