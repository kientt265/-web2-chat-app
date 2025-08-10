"""
Search Tool API
HTTP endpoints for semantic search capabilities
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel

from core.logging import get_logger
from .service import SearchService

router = APIRouter()
logger = get_logger(__name__)

# Global service instance
search_service = SearchService()


class SearchRequest(BaseModel):
    """Search request model"""

    query: str
    conversation_id: Optional[str] = None
    sender_id: Optional[str] = None
    limit: int = 10


class SearchResult(BaseModel):
    """Search result model"""

    message_id: str
    content: str
    similarity_score: float
    conversation_id: str
    sender_id: str
    metadata: dict = {}


class SearchResponse(BaseModel):
    """Search response model"""

    query: str
    results: List[SearchResult]
    total_results: int
    processing_time_ms: float


@router.post("/messages", response_model=SearchResponse)
async def search_messages(request: SearchRequest):
    """Search messages using semantic similarity"""
    logger.info(f"🔍 Searching messages for: {request.query}")

    try:
        # Use search service
        results = await search_service.search_messages(
            query=request.query,
            conversation_id=request.conversation_id,
            limit=request.limit,
        )

        # Convert service results to API response
        search_results = []
        for result in results:
            search_results.append(
                SearchResult(
                    message_id=result.message_id,
                    content=result.content,
                    similarity_score=result.similarity_score,
                    conversation_id=result.conversation_id,
                    sender_id=result.metadata.get("sender_id", ""),
                    metadata=result.metadata,
                )
            )

        logger.info(f"✅ Found {len(search_results)} results")

        return SearchResponse(
            query=request.query,
            results=search_results,
            total_results=len(search_results),
            processing_time_ms=0.0,  # TODO: Add timing
        )

    except Exception as e:
        logger.error(f"❌ Search request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/messages", response_model=SearchResponse)
async def search_in_conversation(
    conversation_id: str,
    q: str = Query(..., description="Search query"),
    sender_id: Optional[str] = Query(None, description="Filter by sender"),
    limit: int = Query(10, ge=1, le=100, description="Number of results"),
):
    """Search messages within a specific conversation"""
    logger.info(f"🔍 Searching in conversation {conversation_id} for: {q}")

    try:
        # Use search service
        results = await search_service.search_messages(
            query=q, conversation_id=conversation_id, limit=limit
        )

        # Filter by sender if specified
        if sender_id:
            results = [r for r in results if r.metadata.get("sender_id") == sender_id]

        # Convert service results to API response
        search_results = []
        for result in results:
            search_results.append(
                SearchResult(
                    message_id=result.message_id,
                    content=result.content,
                    similarity_score=result.similarity_score,
                    conversation_id=result.conversation_id,
                    sender_id=result.metadata.get("sender_id", ""),
                    metadata=result.metadata,
                )
            )

        logger.info(f"✅ Found {len(search_results)} results in conversation")

        return SearchResponse(
            query=q,
            results=search_results,
            total_results=len(search_results),
            processing_time_ms=0.0,  # TODO: Add timing
        )

    except Exception as e:
        logger.error(f"❌ Conversation search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def search_health():
    """Health check for search tool"""
    try:
        # Test connection to sync service
        sync_healthy = await search_service.check_sync_service_health()

        return {
            "status": "healthy" if sync_healthy else "degraded",
            "sync_service": "connected" if sync_healthy else "disconnected",
            "capabilities": ["semantic_search", "conversation_search"],
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "sync_service": "disconnected"}
