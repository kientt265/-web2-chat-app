"""
CDC data models
"""
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class CDCPayload(BaseModel):
    """CDC payload from Debezium"""
    op: str  # c=create, u=update, d=delete
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    source: Dict[str, Any]
    ts_ms: int


class CDCMessage(BaseModel):
    """Complete CDC message"""
    payload: CDCPayload
    

class MessageData(BaseModel):
    """Message data for ChromaDB"""
    message_id: str
    conversation_id: str
    sender_id: str
    content: str
    sent_at: datetime
    operation: str = Field(description="CDC operation: c, u, d")


class SearchQuery(BaseModel):
    """Search query model"""
    query: str = Field(..., min_length=1, max_length=1000)
    conversation_id: Optional[str] = None
    sender_id: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)
