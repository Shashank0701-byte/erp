"""
Kafka Consumer for Sales Service
Listens for events from other services (e.g., Low Stock events from Inventory)
"""

import asyncio
import json
import logging
from typing import Callable, Dict, Any, Optional
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from app.config import settings
from app.schemas.kafka_events import LowStockEvent, EventType

logger = logging.getLogger(__name__)


class KafkaConsumerService:
    """
    Async Kafka consumer service
    
    Features:
    - Async message consumption
    - Automatic deserialization
    - Event routing to handlers
    - Error handling and retry
    - Graceful shutdown
    """
    
    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        topics: list[str],
        auto_offset_reset: str = "earliest"
    ):
        """
        Initialize Kafka consumer
        
        Args:
            bootstrap_servers: Kafka broker addresses
            group_id: Consumer group ID
            topics: List of topics to subscribe to
            auto_offset_reset: Where to start reading (earliest/latest)
        """
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topics = topics
        self.auto_offset_reset = auto_offset_reset
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.running = False
        self.handlers: Dict[str, Callable] = {}
        
        logger.info(
            f"Kafka consumer initialized: group={group_id}, "
            f"topics={topics}, servers={bootstrap_servers}"
        )
    
    def register_handler(self, event_type: str, handler: Callable):
        """
        Register a handler function for a specific event type
        
        Args:
            event_type: Event type to handle (e.g., "inventory.low_stock")
            handler: Async function to handle the event
        """
        self.handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")
    
    async def start(self):
        """Start the Kafka consumer"""
        try:
            self.consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset=self.auto_offset_reset,
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda m: m.decode('utf-8') if m else None
            )
            
            await self.consumer.start()
            self.running = True
            
            logger.info(f"Kafka consumer started successfully. Subscribed to: {self.topics}")
            
        except KafkaError as e:
            logger.error(f"Failed to start Kafka consumer: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the Kafka consumer"""
        self.running = False
        
        if self.consumer:
            try:
                await self.consumer.stop()
                logger.info("Kafka consumer stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping Kafka consumer: {str(e)}")
    
    async def consume(self):
        """
        Main consumption loop
        
        Continuously consumes messages and routes them to appropriate handlers
        """
        if not self.consumer:
            raise RuntimeError("Consumer not started. Call start() first.")
        
        logger.info("Starting message consumption loop...")
        
        try:
            async for message in self.consumer:
                if not self.running:
                    break
                
                try:
                    await self._process_message(message)
                except Exception as e:
                    logger.error(
                        f"Error processing message from {message.topic}: {str(e)}",
                        exc_info=True
                    )
                    # Continue processing other messages
                    continue
                    
        except Exception as e:
            logger.error(f"Error in consumption loop: {str(e)}", exc_info=True)
            raise
    
    async def _process_message(self, message):
        """
        Process a single Kafka message
        
        Args:
            message: Kafka message object
        """
        try:
            # Extract message data
            topic = message.topic
            partition = message.partition
            offset = message.offset
            key = message.key
            value = message.value
            
            logger.debug(
                f"Received message: topic={topic}, partition={partition}, "
                f"offset={offset}, key={key}"
            )
            
            # Extract event type from metadata
            event_type = value.get("metadata", {}).get("event_type")
            
            if not event_type:
                logger.warning(f"Message missing event_type: {value}")
                return
            
            # Route to appropriate handler
            handler = self.handlers.get(event_type)
            
            if handler:
                logger.info(f"Routing event {event_type} to handler")
                await handler(value)
            else:
                logger.warning(f"No handler registered for event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            raise


class LowStockConsumer:
    """
    Specialized consumer for Low Stock events from Inventory service
    """
    
    def __init__(self):
        """Initialize low stock consumer"""
        self.consumer_service = KafkaConsumerService(
            bootstrap_servers=getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            group_id=getattr(settings, 'KAFKA_CONSUMER_GROUP', 'sales-service-group'),
            topics=['inventory-events'],  # Subscribe to inventory events topic
            auto_offset_reset='earliest'
        )
        
        # Register handler for low stock events
        self.consumer_service.register_handler(
            EventType.LOW_STOCK.value,
            self.handle_low_stock_event
        )
        
        logger.info("Low Stock consumer initialized")
    
    async def start(self):
        """Start consuming low stock events"""
        await self.consumer_service.start()
        await self.consumer_service.consume()
    
    async def stop(self):
        """Stop consuming"""
        await self.consumer_service.stop()
    
    async def handle_low_stock_event(self, event_data: Dict[str, Any]):
        """
        Handle low stock event from Inventory service
        
        Args:
            event_data: Raw event data from Kafka
        """
        try:
            # Parse event using Pydantic schema
            event = LowStockEvent(**event_data)
            
            logger.info(
                f"Processing low stock event: "
                f"product={event.payload.product_name} ({event.payload.product_sku}), "
                f"current_stock={event.payload.current_stock}, "
                f"reorder_level={event.payload.reorder_level}"
            )
            
            # Business logic for handling low stock
            await self._process_low_stock(event)
            
            logger.info(f"Successfully processed low stock event: {event.metadata.event_id}")
            
        except Exception as e:
            logger.error(f"Error handling low stock event: {str(e)}", exc_info=True)
            raise
    
    async def _process_low_stock(self, event: LowStockEvent):
        """
        Process low stock event - implement business logic
        
        Args:
            event: Parsed low stock event
        """
        # Example business logic:
        
        # 1. Check if product has pending sales orders
        pending_orders = await self._check_pending_orders(event.payload.product_id)
        
        if pending_orders:
            logger.warning(
                f"Product {event.payload.product_sku} has {len(pending_orders)} "
                f"pending orders but low stock!"
            )
        
        # 2. Calculate recommended action
        if event.payload.days_of_stock_remaining and event.payload.days_of_stock_remaining < 3:
            priority = "URGENT"
        elif event.payload.current_stock == 0:
            priority = "CRITICAL"
        else:
            priority = "NORMAL"
        
        # 3. Create alert/notification
        await self._create_stock_alert(event, priority)
        
        # 4. Update sales forecasts
        await self._update_sales_forecast(event.payload.product_id, event.payload.current_stock)
        
        # 5. Notify sales team
        await self._notify_sales_team(event, priority)
        
        logger.info(
            f"Low stock processing complete for {event.payload.product_sku}. "
            f"Priority: {priority}"
        )
    
    async def _check_pending_orders(self, product_id: str) -> list:
        """
        Check for pending sales orders for this product
        
        Args:
            product_id: Product ID
            
        Returns:
            List of pending orders
        """
        # Mock implementation - in production, query database
        logger.debug(f"Checking pending orders for product: {product_id}")
        
        # Simulate database query
        pending_orders = []
        
        return pending_orders
    
    async def _create_stock_alert(self, event: LowStockEvent, priority: str):
        """
        Create stock alert in the system
        
        Args:
            event: Low stock event
            priority: Alert priority
        """
        logger.info(
            f"Creating stock alert: product={event.payload.product_sku}, "
            f"priority={priority}"
        )
        
        # Mock implementation - in production, save to database
        alert = {
            "product_id": event.payload.product_id,
            "product_sku": event.payload.product_sku,
            "product_name": event.payload.product_name,
            "current_stock": event.payload.current_stock,
            "reorder_level": event.payload.reorder_level,
            "priority": priority,
            "tenant_id": event.metadata.tenant_id,
            "created_at": event.metadata.timestamp
        }
        
        # In production: await db.save(alert)
        logger.debug(f"Stock alert created: {alert}")
    
    async def _update_sales_forecast(self, product_id: str, current_stock: int):
        """
        Update sales forecasts based on current stock levels
        
        Args:
            product_id: Product ID
            current_stock: Current stock quantity
        """
        logger.info(f"Updating sales forecast for product: {product_id}")
        
        # Mock implementation - in production, update ML model or forecast data
        # This could trigger:
        # - Recalculation of demand forecasts
        # - Adjustment of sales targets
        # - Update of product availability status
        
        logger.debug(f"Sales forecast updated for product: {product_id}")
    
    async def _notify_sales_team(self, event: LowStockEvent, priority: str):
        """
        Notify sales team about low stock situation
        
        Args:
            event: Low stock event
            priority: Notification priority
        """
        logger.info(f"Notifying sales team about low stock: {event.payload.product_sku}")
        
        # Mock implementation - in production, send notifications via:
        # - Email
        # - Slack/Teams
        # - In-app notifications
        # - SMS for critical items
        
        notification = {
            "type": "low_stock_alert",
            "priority": priority,
            "product": event.payload.product_name,
            "sku": event.payload.product_sku,
            "current_stock": event.payload.current_stock,
            "message": (
                f"Low stock alert: {event.payload.product_name} "
                f"({event.payload.product_sku}) has only {event.payload.current_stock} "
                f"units remaining (reorder level: {event.payload.reorder_level})"
            )
        }
        
        # In production: await notification_service.send(notification)
        logger.debug(f"Notification sent: {notification}")


# Global consumer instance
low_stock_consumer: Optional[LowStockConsumer] = None


async def start_kafka_consumers():
    """Start all Kafka consumers"""
    global low_stock_consumer
    
    try:
        logger.info("Starting Kafka consumers...")
        
        # Initialize and start low stock consumer
        low_stock_consumer = LowStockConsumer()
        
        # Start consumer in background task
        asyncio.create_task(low_stock_consumer.start())
        
        logger.info("Kafka consumers started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start Kafka consumers: {str(e)}")
        raise


async def stop_kafka_consumers():
    """Stop all Kafka consumers"""
    global low_stock_consumer
    
    try:
        logger.info("Stopping Kafka consumers...")
        
        if low_stock_consumer:
            await low_stock_consumer.stop()
        
        logger.info("Kafka consumers stopped successfully")
        
    except Exception as e:
        logger.error(f"Error stopping Kafka consumers: {str(e)}")
