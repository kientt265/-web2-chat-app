"""
Main CDC event processor
"""
from typing import Dict, Any

from core.logging import get_logger
from processors.message_processor import MessageProcessor

logger = get_logger(__name__)


class CDCProcessor:
    """Routes CDC events to appropriate processors"""
    
    @staticmethod
    async def process_cdc_event(topic: str, cdc_data: Dict[str, Any]) -> bool:
        """Route CDC events to appropriate processors"""
        try:
            if topic == 'chat.cdc.messages':
                return await MessageProcessor.process_cdc_event(cdc_data)
            elif topic == 'chat.cdc.conversations':
                logger.info(f"📝 Conversation CDC event: {cdc_data.get('payload', {}).get('op', 'unknown')}")
                return True
            elif topic == 'chat.cdc.conversation_members':
                logger.info(f"👥 Conversation member CDC event: {cdc_data.get('payload', {}).get('op', 'unknown')}")
                return True
            elif topic == 'chat.cdc.message_deliveries':
                logger.info(f"📬 Message delivery CDC event: {cdc_data.get('payload', {}).get('op', 'unknown')}")
                return True
            else:
                logger.warning(f"Unknown CDC topic: {topic}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error processing CDC event from {topic}: {e}")
            return False
