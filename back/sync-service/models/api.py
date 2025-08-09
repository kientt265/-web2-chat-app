"""
API response models
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel


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
    kafka_topics: List[str]
    status: str
    uptime_seconds: Optional[float] = None


class SearchResult(BaseModel):
    """Individual search result"""
    message_id: str
    conversation_id: str
    sender_id: str
    content: str
    similarity_score: float


class SearchResponse(BaseModel):
    """Search response"""
    query: str
    results: List[SearchResult]
    total_results: int
    processing_time_ms: float
