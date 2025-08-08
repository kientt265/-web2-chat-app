"""
Search endpoints
"""
import time
from fastapi import APIRouter, HTTPException
from typing import List

from models.cdc import SearchQuery
from models.api import SearchResponse, SearchResult
from services.chromadb_service import chromadb_service
from services.embedding_service import embedding_service
from core.logging import get_logger

router = APIRouter(prefix="/search", tags=["search"])
logger = get_logger(__name__)


@router.post("", response_model=SearchResponse)
async def search_messages(query: SearchQuery) -> SearchResponse:
    """Search messages using semantic similarity"""
    start_time = time.time()
    
    try:
        # Generate query embedding
        query_embedding = embedding_service.encode(query.query)
        
        # Search ChromaDB
        results = await chromadb_service.search_similar(
            query_embedding=query_embedding,
            conversation_id=query.conversation_id,
            sender_id=query.sender_id,
            limit=query.limit
        )
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return SearchResponse(
            query=query.query,
            results=results,
            total_results=len(results),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"❌ Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
