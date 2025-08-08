"""
Kafka consumer service for CDC events
"""
import json
import asyncio
from typing import Optional, Callable
from confluent_kafka import Consumer, KafkaError

from core.logging import get_logger
from config.settings import settings

logger = get_logger(__name__)


class KafkaService:
    """Kafka consumer service for CDC events"""
    
    def __init__(self):
        self.consumer: Optional[Consumer] = None
        self.is_running = False
        self.message_handler: Optional[Callable] = None
        
    async def initialize(self, message_handler: Callable) -> bool:
        """Initialize Kafka consumer"""
        try:
            consumer_config = {
                'bootstrap.servers': settings.kafka_bootstrap_servers,
                'group.id': settings.kafka_group_id,
                'auto.offset.reset': settings.kafka_auto_offset_reset,
                'enable.auto.commit': True,
                'session.timeout.ms': 6000,
                'heartbeat.interval.ms': 1000
            }
            
            self.consumer = Consumer(consumer_config)
            self.consumer.subscribe(settings.cdc_topics)
            self.message_handler = message_handler
            
            logger.info(f"✅ Kafka consumer initialized for topics: {settings.cdc_topics}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Kafka consumer initialization failed: {e}")
            return False
    
    async def start_consuming(self):
        """Start consuming CDC events"""
        if not self.consumer or not self.message_handler:
            raise RuntimeError("Kafka consumer not properly initialized")
        
        self.is_running = True
        logger.info("🔄 Starting Kafka CDC consumer...")
        
        while self.is_running:
            try:
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    await asyncio.sleep(0.1)
                    continue
                    
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error(f"❌ Consumer error: {msg.error()}")
                        continue
                
                # Process message
                try:
                    cdc_data = json.loads(msg.value().decode('utf-8'))
                    topic = msg.topic()
                    
                    await self.message_handler(topic, cdc_data)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse CDC message: {e}")
                    
            except Exception as e:
                logger.error(f"❌ Error in consumer loop: {e}")
                await asyncio.sleep(5)
    
    async def stop_consuming(self):
        """Stop consuming messages"""
        self.is_running = False
        if self.consumer:
            self.consumer.close()
            logger.info("✅ Kafka consumer stopped")


# Global service instance
kafka_service = KafkaService()
