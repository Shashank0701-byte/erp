# Kafka Integration Guide - Event-Driven Architecture

## Overview

This document describes the implementation of async Kafka consumers and producers for event-driven communication between microservices in the ERP system.

## Features

✅ **Async Kafka Consumer** - Non-blocking event consumption using aiokafka  
✅ **Async Kafka Producer** - Non-blocking event publishing  
✅ **Event Schemas** - Pydantic models for type-safe events  
✅ **Low Stock Events** - Inventory → Sales communication  
✅ **Event Routing** - Handler registration for different event types  
✅ **Error Handling** - Graceful degradation and retry logic  
✅ **Multi-Tenancy** - Tenant-aware event processing  
✅ **Priority Levels** - Event prioritization (LOW, MEDIUM, HIGH, CRITICAL)  

## Architecture

```
┌─────────────────────┐                    ┌─────────────────────┐
│                     │                    │                     │
│  Inventory Service  │                    │   Sales Service     │
│                     │                    │                     │
│  ┌───────────────┐  │                    │  ┌───────────────┐  │
│  │   Producer    │  │                    │  │   Consumer    │  │
│  │               │  │                    │  │               │  │
│  │ - Low Stock   │──┼────────────────────┼─►│ - Low Stock   │  │
│  │ - Created     │  │    Kafka Topics    │  │   Handler     │  │
│  │ - Adjusted    │  │                    │  │               │  │
│  └───────────────┘  │                    │  └───────────────┘  │
│                     │                    │                     │
└─────────────────────┘                    └─────────────────────┘
           │                                          │
           │                                          │
           ▼                                          ▼
    ┌──────────────────────────────────────────────────────┐
    │                    Kafka Cluster                      │
    │                                                        │
    │  Topics:                                              │
    │  - inventory-events                                   │
    │  - sales-events                                       │
    │                                                        │
    └──────────────────────────────────────────────────────┘
```

## Event Schemas

### Event Structure

All events follow a consistent structure:

```json
{
  "metadata": {
    "event_id": "evt-123456",
    "event_type": "inventory.low_stock",
    "event_version": "1.0",
    "timestamp": "2024-01-15T10:00:00Z",
    "source_service": "inventory-service",
    "tenant_id": "tenant-1",
    "correlation_id": "corr-789",
    "priority": "high"
  },
  "payload": {
    // Event-specific data
  }
}
```

### Low Stock Event

**Event Type:** `inventory.low_stock`

**Payload:**
```json
{
  "product_id": "PRD-123",
  "product_sku": "LAP-001",
  "product_name": "Laptop Computer",
  "current_stock": 8,
  "reorder_level": 10,
  "reorder_quantity": 50,
  "unit_price": 1200.00,
  "category": "electronics",
  "location": "Warehouse A",
  "days_of_stock_remaining": 3.5
}
```

**Priority Levels:**
- `CRITICAL` - Stock is 0
- `HIGH` - Stock < 3 days remaining or < 50% of reorder level
- `MEDIUM` - Stock <= reorder level
- `LOW` - Normal stock levels

## Kafka Consumer (Sales Service)

### LowStockConsumer Class

Located in `app/consumers/kafka_consumer.py`

**Features:**
- Subscribes to `inventory-events` topic
- Handles `inventory.low_stock` events
- Processes events asynchronously
- Implements business logic for low stock alerts

**Usage:**
```python
from app.consumers import start_kafka_consumers, stop_kafka_consumers

# Start consumer (in application startup)
await start_kafka_consumers()

# Stop consumer (in application shutdown)
await stop_kafka_consumers()
```

### Event Handler

```python
async def handle_low_stock_event(self, event_data: Dict[str, Any]):
    # Parse event
    event = LowStockEvent(**event_data)
    
    # Business logic:
    # 1. Check pending orders
    # 2. Calculate priority
    # 3. Create alerts
    # 4. Update forecasts
    # 5. Notify sales team
```

### Consumer Configuration

```python
consumer = KafkaConsumerService(
    bootstrap_servers="localhost:9092",
    group_id="sales-service-group",
    topics=["inventory-events"],
    auto_offset_reset="earliest"
)
```

## Kafka Producer (Inventory Service)

### InventoryEventProducer Class

Located in `app/producers/kafka_producer.py`

**Features:**
- Publishes to `inventory-events` topic
- Automatic event metadata generation
- Message compression (gzip)
- Retry logic for failed sends
- Acknowledgment from all replicas

**Usage:**
```python
from app.producers import get_inventory_producer

# Get producer instance
producer = await get_inventory_producer()

# Publish low stock event
await producer.publish_low_stock_event(
    product_id="PRD-123",
    product_sku="LAP-001",
    product_name="Laptop Computer",
    current_stock=8,
    reorder_level=10,
    reorder_quantity=50,
    unit_price=1200.00,
    category="electronics",
    tenant_id="tenant-1"
)
```

### Producer Configuration

```python
producer = AIOKafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    compression_type='gzip',
    acks='all',  # Wait for all replicas
    retries=3
)
```

## Integration with Product Service

### Publishing Low Stock Events

In `app/services/product_service.py`, after stock adjustment:

```python
async def adjust_stock(
    db: AsyncSession,
    product_id: str,
    adjustment: ProductStockAdjustment,
    tenant_id: str
) -> Optional[Product]:
    # Adjust stock
    product.quantity_on_hand = new_quantity
    await db.commit()
    
    # Check if low stock
    if product.needs_reorder:
        # Publish low stock event
        producer = await get_inventory_producer()
        await producer.publish_low_stock_event(
            product_id=product.id,
            product_sku=product.sku,
            product_name=product.name,
            current_stock=product.quantity_on_hand,
            reorder_level=product.reorder_level,
            reorder_quantity=product.reorder_quantity,
            unit_price=product.unit_price,
            category=product.category,
            tenant_id=tenant_id
        )
    
    return product
```

## Configuration

### Environment Variables

```bash
# Kafka Event Streaming
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_CONSUMER_GROUP=sales-service-group
KAFKA_INVENTORY_TOPIC=inventory-events
KAFKA_SALES_TOPIC=sales-events
KAFKA_AUTO_OFFSET_RESET=earliest
KAFKA_ENABLE_AUTO_COMMIT=True
```

### Application Config

```python
class Settings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_CONSUMER_GROUP: str = "sales-service-group"
    KAFKA_INVENTORY_TOPIC: str = "inventory-events"
    KAFKA_SALES_TOPIC: str = "sales-events"
    KAFKA_AUTO_OFFSET_RESET: str = "earliest"
    KAFKA_ENABLE_AUTO_COMMIT: bool = True
```

## Kafka Setup

### 1. Install Kafka

```bash
# Download Kafka
wget https://downloads.apache.org/kafka/3.6.1/kafka_2.13-3.6.1.tgz

# Extract
tar -xzf kafka_2.13-3.6.1.tgz
cd kafka_2.13-3.6.1
```

### 2. Start Zookeeper

```bash
bin/zookeeper-server-start.sh config/zookeeper.properties
```

### 3. Start Kafka Broker

```bash
bin/kafka-server-start.sh config/server.properties
```

### 4. Create Topics

```bash
# Create inventory-events topic
bin/kafka-topics.sh --create \
  --topic inventory-events \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1

# Create sales-events topic
bin/kafka-topics.sh --create \
  --topic sales-events \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1
```

### 5. Verify Topics

```bash
bin/kafka-topics.sh --list --bootstrap-server localhost:9092
```

## Testing

### Test Producer

```python
import asyncio
from app.producers import start_kafka_producer, get_inventory_producer

async def test_producer():
    # Start producer
    await start_kafka_producer()
    
    # Get producer instance
    producer = await get_inventory_producer()
    
    # Publish test event
    await producer.publish_low_stock_event(
        product_id="TEST-001",
        product_sku="TEST-SKU",
        product_name="Test Product",
        current_stock=5,
        reorder_level=10,
        reorder_quantity=50,
        unit_price=100.00,
        category="test",
        tenant_id="test-tenant"
    )
    
    print("Event published successfully!")

asyncio.run(test_producer())
```

### Test Consumer

```python
import asyncio
from app.consumers import start_kafka_consumers

async def test_consumer():
    # Start consumer
    await start_kafka_consumers()
    
    # Consumer runs in background
    # Check logs for event processing
    await asyncio.sleep(60)  # Run for 1 minute

asyncio.run(test_consumer())
```

### Monitor with Kafka Console Consumer

```bash
bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic inventory-events \
  --from-beginning \
  --formatter kafka.tools.DefaultMessageFormatter \
  --property print.key=true \
  --property print.value=true
```

## Error Handling

### Producer Error Handling

```python
try:
    await producer.publish_low_stock_event(...)
except KafkaError as e:
    logger.error(f"Failed to publish event: {str(e)}")
    # Event is lost - implement dead letter queue
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
```

### Consumer Error Handling

```python
async def handle_low_stock_event(self, event_data):
    try:
        event = LowStockEvent(**event_data)
        await self._process_low_stock(event)
    except ValidationError as e:
        logger.error(f"Invalid event schema: {str(e)}")
        # Skip invalid events
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        # Retry or send to dead letter queue
```

## Monitoring

### Metrics to Track

1. **Producer Metrics:**
   - Events published per second
   - Failed publish attempts
   - Average publish latency

2. **Consumer Metrics:**
   - Events consumed per second
   - Consumer lag
   - Processing errors
   - Average processing time

### Logging

```python
# All Kafka operations are logged
logger.info("Published low stock event: product=LAP-001")
logger.info("Processing low stock event: product=LAP-001")
logger.error("Failed to publish event: Connection refused")
```

## Best Practices

1. **Event Versioning** - Include version in metadata
2. **Idempotency** - Handle duplicate events gracefully
3. **Schema Evolution** - Use backward-compatible changes
4. **Error Handling** - Implement retry and dead letter queues
5. **Monitoring** - Track consumer lag and processing errors
6. **Testing** - Test with real Kafka cluster
7. **Partitioning** - Use product_id as key for ordering
8. **Compression** - Enable gzip compression
9. **Batch Processing** - Process events in batches when possible
10. **Graceful Shutdown** - Commit offsets before stopping

## Security

### Authentication

```python
# SASL/SCRAM authentication
consumer = AIOKafkaConsumer(
    sasl_mechanism='SCRAM-SHA-256',
    sasl_plain_username='user',
    sasl_plain_password='password',
    security_protocol='SASL_SSL'
)
```

### Encryption

```python
# SSL encryption
consumer = AIOKafkaConsumer(
    security_protocol='SSL',
    ssl_cafile='/path/to/ca-cert',
    ssl_certfile='/path/to/client-cert',
    ssl_keyfile='/path/to/client-key'
)
```

## Next Steps

1. ✅ Implement dead letter queue for failed events
2. ✅ Add event replay capability
3. ✅ Implement event sourcing
4. ✅ Add schema registry integration
5. ✅ Implement CQRS pattern
6. ✅ Add distributed tracing
7. ✅ Implement saga pattern for distributed transactions
