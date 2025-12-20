"""
Kafka Producer for Inventory Service
Publishes events to Kafka topics for other services to consume
"""

import json
import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from app.config import settings
from app.schemas.kafka_events import (
    EventMetadata,
    EventType,
    EventPriority,
    LowStockEvent,
    LowStockEventPayload,
    ProductCreatedEvent,
    ProductCreatedEventPayload,
    StockAdjustedEvent,
    StockAdjustedEventPayload
)

logger = logging.getLogger(__name__)


class KafkaProducerService:
    """
    Async Kafka producer service
    
    Features:
    - Async message production
    - Automatic serialization
    - Event metadata generation
    - Error handling and retry
    - Graceful shutdown
    """
    
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str = "inventory-events"
    ):
        """
        Initialize Kafka producer
        
        Args:
            bootstrap_servers: Kafka broker addresses
            topic: Default topic to publish to
        """
        self.bootstrap_servers = bootstrap_servers
        self.default_topic = topic
        self.producer: Optional[AIOKafkaProducer] = None
        
        logger.info(f"Kafka producer initialized: topic={topic}, servers={bootstrap_servers}")
    
    async def start(self):
        """Start the Kafka producer"""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                compression_type='gzip',  # Compress messages
                acks='all',  # Wait for all replicas to acknowledge
                retries=3  # Retry failed sends
            )
            
            await self.producer.start()
            logger.info("Kafka producer started successfully")
            
        except KafkaError as e:
            logger.error(f"Failed to start Kafka producer: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the Kafka producer"""
        if self.producer:
            try:
                await self.producer.stop()
                logger.info("Kafka producer stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping Kafka producer: {str(e)}")
    
    async def publish(
        self,
        event_data: Dict[str, Any],
        topic: Optional[str] = None,
        key: Optional[str] = None
    ):
        """
        Publish an event to Kafka
        
        Args:
            event_data: Event data to publish
            topic: Topic to publish to (uses default if not specified)
            key: Message key for partitioning
        """
        if not self.producer:
            raise RuntimeError("Producer not started. Call start() first.")
        
        topic = topic or self.default_topic
        
        try:
            # Send message
            await self.producer.send_and_wait(topic, value=event_data, key=key)
            
            logger.info(
                f"Published event to {topic}: "
                f"type={event_data.get('metadata', {}).get('event_type')}"
            )
            
        except KafkaError as e:
            logger.error(f"Failed to publish event to {topic}: {str(e)}")
            raise
    
    def create_event_metadata(
        self,
        event_type: EventType,
        tenant_id: str,
        priority: EventPriority = EventPriority.MEDIUM,
        correlation_id: Optional[str] = None
    ) -> EventMetadata:
        """
        Create event metadata
        
        Args:
            event_type: Type of event
            tenant_id: Tenant identifier
            priority: Event priority
            correlation_id: Optional correlation ID
            
        Returns:
            EventMetadata object
        """
        return EventMetadata(
            event_id=f"evt-{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            event_version="1.0",
            timestamp=datetime.utcnow(),
            source_service="inventory-service",
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            priority=priority
        )


class InventoryEventProducer:
    """
    Specialized producer for Inventory events
    """
    
    def __init__(self):
        """Initialize inventory event producer"""
        self.producer_service = KafkaProducerService(
            bootstrap_servers=getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            topic='inventory-events'
        )
        
        logger.info("Inventory event producer initialized")
    
    async def start(self):
        """Start the producer"""
        await self.producer_service.start()
    
    async def stop(self):
        """Stop the producer"""
        await self.producer_service.stop()
    
    async def publish_low_stock_event(
        self,
        product_id: str,
        product_sku: str,
        product_name: str,
        current_stock: int,
        reorder_level: int,
        reorder_quantity: int,
        unit_price: float,
        category: str,
        tenant_id: str,
        location: Optional[str] = None,
        days_of_stock_remaining: Optional[float] = None
    ):
        """
        Publish a low stock event
        
        Args:
            product_id: Product ID
            product_sku: Product SKU
            product_name: Product name
            current_stock: Current stock quantity
            reorder_level: Reorder level threshold
            reorder_quantity: Recommended reorder quantity
            unit_price: Unit price
            category: Product category
            tenant_id: Tenant ID
            location: Storage location
            days_of_stock_remaining: Estimated days until stockout
        """
        try:
            # Determine priority based on stock level
            if current_stock == 0:
                priority = EventPriority.CRITICAL
            elif days_of_stock_remaining and days_of_stock_remaining < 3:
                priority = EventPriority.HIGH
            elif current_stock <= reorder_level / 2:
                priority = EventPriority.HIGH
            else:
                priority = EventPriority.MEDIUM
            
            # Create event metadata
            metadata = self.producer_service.create_event_metadata(
                event_type=EventType.LOW_STOCK,
                tenant_id=tenant_id,
                priority=priority
            )
            
            # Create event payload
            payload = LowStockEventPayload(
                product_id=product_id,
                product_sku=product_sku,
                product_name=product_name,
                current_stock=current_stock,
                reorder_level=reorder_level,
                reorder_quantity=reorder_quantity,
                unit_price=unit_price,
                category=category,
                location=location,
                days_of_stock_remaining=days_of_stock_remaining
            )
            
            # Create complete event
            event = LowStockEvent(metadata=metadata, payload=payload)
            
            # Publish to Kafka
            await self.producer_service.publish(
                event_data=event.model_dump(mode='json'),
                key=product_id  # Use product_id as key for partitioning
            )
            
            logger.info(
                f"Published low stock event: product={product_sku}, "
                f"stock={current_stock}, priority={priority.value}"
            )
            
        except Exception as e:
            logger.error(f"Failed to publish low stock event: {str(e)}", exc_info=True)
            raise
    
    async def publish_product_created_event(
        self,
        product_id: str,
        product_sku: str,
        product_name: str,
        category: str,
        unit_price: float,
        cost_price: float,
        initial_stock: int,
        tenant_id: str
    ):
        """
        Publish a product created event
        
        Args:
            product_id: Product ID
            product_sku: Product SKU
            product_name: Product name
            category: Product category
            unit_price: Unit price
            cost_price: Cost price
            initial_stock: Initial stock quantity
            tenant_id: Tenant ID
        """
        try:
            metadata = self.producer_service.create_event_metadata(
                event_type=EventType.PRODUCT_CREATED,
                tenant_id=tenant_id,
                priority=EventPriority.LOW
            )
            
            payload = ProductCreatedEventPayload(
                product_id=product_id,
                product_sku=product_sku,
                product_name=product_name,
                category=category,
                unit_price=unit_price,
                cost_price=cost_price,
                initial_stock=initial_stock
            )
            
            event = ProductCreatedEvent(metadata=metadata, payload=payload)
            
            await self.producer_service.publish(
                event_data=event.model_dump(mode='json'),
                key=product_id
            )
            
            logger.info(f"Published product created event: {product_sku}")
            
        except Exception as e:
            logger.error(f"Failed to publish product created event: {str(e)}", exc_info=True)
            raise
    
    async def publish_stock_adjusted_event(
        self,
        product_id: str,
        product_sku: str,
        product_name: str,
        previous_stock: int,
        new_stock: int,
        adjustment_quantity: int,
        reason: str,
        adjusted_by: str,
        tenant_id: str
    ):
        """
        Publish a stock adjusted event
        
        Args:
            product_id: Product ID
            product_sku: Product SKU
            product_name: Product name
            previous_stock: Previous stock quantity
            new_stock: New stock quantity
            adjustment_quantity: Adjustment amount
            reason: Reason for adjustment
            adjusted_by: User who made the adjustment
            tenant_id: Tenant ID
        """
        try:
            metadata = self.producer_service.create_event_metadata(
                event_type=EventType.STOCK_ADJUSTED,
                tenant_id=tenant_id,
                priority=EventPriority.LOW
            )
            
            payload = StockAdjustedEventPayload(
                product_id=product_id,
                product_sku=product_sku,
                product_name=product_name,
                previous_stock=previous_stock,
                new_stock=new_stock,
                adjustment_quantity=adjustment_quantity,
                reason=reason,
                adjusted_by=adjusted_by
            )
            
            event = StockAdjustedEvent(metadata=metadata, payload=payload)
            
            await self.producer_service.publish(
                event_data=event.model_dump(mode='json'),
                key=product_id
            )
            
            logger.info(
                f"Published stock adjusted event: {product_sku}, "
                f"adjustment={adjustment_quantity:+d}"
            )
            
        except Exception as e:
            logger.error(f"Failed to publish stock adjusted event: {str(e)}", exc_info=True)
            raise


# Global producer instance
inventory_event_producer: Optional[InventoryEventProducer] = None


async def start_kafka_producer():
    """Start Kafka producer"""
    global inventory_event_producer
    
    try:
        logger.info("Starting Kafka producer...")
        
        inventory_event_producer = InventoryEventProducer()
        await inventory_event_producer.start()
        
        logger.info("Kafka producer started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start Kafka producer: {str(e)}")
        raise


async def stop_kafka_producer():
    """Stop Kafka producer"""
    global inventory_event_producer
    
    try:
        logger.info("Stopping Kafka producer...")
        
        if inventory_event_producer:
            await inventory_event_producer.stop()
        
        logger.info("Kafka producer stopped successfully")
        
    except Exception as e:
        logger.error(f"Error stopping Kafka producer: {str(e)}")


async def get_inventory_producer() -> InventoryEventProducer:
    """Get the global inventory event producer instance"""
    if not inventory_event_producer:
        raise RuntimeError("Kafka producer not initialized. Call start_kafka_producer() first.")
    return inventory_event_producer
