"""
Message CDC processor
"""
from typing import Dict, Any
from datetime import datetime

from core.logging import get_logger
from models.cdc import MessageData
from services.chromadb_service import chromadb_service
from services.embedding_service import embedding_service

logger = get_logger(__name__)


class MessageProcessor:
    """Processes CDC events for messages table"""
    
    @staticmethod
    async def process_cdc_event(cdc_data: Dict[str, Any]) -> bool:
        """Process CDC event for messages"""
        try:
            payload = cdc_data.get('payload', {})
            operation = payload.get('op')  # c=create, u=update, d=delete
            
            if operation in ['c', 'u']:  # Create or Update
                return await MessageProcessor._handle_upsert(payload, operation)
            elif operation == 'd':  # Delete
                return await MessageProcessor._handle_delete(payload)
            else:
                logger.warning(f"Unknown operation: {operation}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error processing message CDC: {e}")
            return False
    
    @staticmethod
    async def _handle_upsert(payload: Dict[str, Any], operation: str) -> bool:
        """Handle create/update operations"""
        after = payload.get('after', {})
        
        message_id = after.get('message_id')
        content = after.get('content')
        conversation_id = after.get('conversation_id')
        sender_id = after.get('sender_id')
        sent_at_str = after.get('sent_at')
        
        if not all([message_id, content, conversation_id, sender_id, sent_at_str]):
            logger.warning(f"Missing required fields in CDC payload")
            return False
        
        try:
            # Parse timestamp - handle microsecond timestamp from PostgreSQL
            if isinstance(sent_at_str, int):
                # Convert microseconds to datetime
                sent_at = datetime.fromtimestamp(sent_at_str / 1_000_000)
            else:
                # Handle ISO format string
                sent_at = datetime.fromisoformat(sent_at_str.replace('Z', '+00:00'))
            
            # Create message data
            message_data = MessageData(
                message_id=message_id,
                conversation_id=conversation_id,
                sender_id=sender_id,
                content=content,
                sent_at=sent_at,
                operation=operation
            )
            
            # Generate embedding
            embedding = embedding_service.encode(content)
            
            # Store in ChromaDB
            success = await chromadb_service.upsert_message(message_data, embedding)
            
            if success:
                logger.info(f"✅ Processed message {operation}: {message_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error handling upsert: {e}")
            return False
    
    @staticmethod
    async def _handle_delete(payload: Dict[str, Any]) -> bool:
        """Handle delete operations"""
        before = payload.get('before', {})
        message_id = before.get('message_id')
        
        if not message_id:
            logger.warning("Missing message_id in delete payload")
            return False
        
        try:
            success = await chromadb_service.delete_message(message_id)
            
            if success:
                logger.info(f"✅ Deleted message: {message_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error handling delete: {e}")
            return False
