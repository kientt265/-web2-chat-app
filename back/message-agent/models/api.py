"""
API models for message agent
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class MessageRetrievalRequest(BaseModel):
    """Request model for message retrieval"""
    
    conversation_id: Optional[str] = None
    sender_id: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search"""
    
    query: str = Field(..., min_length=1, max_length=1000)
    conversation_id: Optional[str] = None
    sender_id: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)


class MessageResult(BaseModel):
    """Individual message result"""
    
    message_id: str
    conversation_id: str
    sender_id: str
    content: str
    sent_at: datetime
    similarity_score: Optional[float] = None


class MessageResponse(BaseModel):
    """Response model for message retrieval"""
    
    messages: List[MessageResult]
    total_messages: int
    page_info: dict
    processing_time_ms: float


class HealthResponse(BaseModel):
    """Health check response"""
    
    status: str
    timestamp: datetime
    service: str
    version: str


class StatsResponse(BaseModel):
    """Service statistics response"""
    
    chromadb_documents: int
    embedding_model: str
    status: str
    uptime_seconds: Optional[float] = None
