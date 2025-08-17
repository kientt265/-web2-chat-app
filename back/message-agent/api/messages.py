"""
Message retrieval endpoints
"""

import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from models.api import (
    MessageRetrievalRequest,
    SemanticSearchRequest,
    MessageResponse,
    MessageResult,
)
from services.chromadb_service import chromadb_service
from services.embedding_service import embedding_service
from core.logging import get_logger

router = APIRouter(prefix="/messages", tags=["messages"])
logger = get_logger(__name__)


@router.get("/", response_model=MessageResponse)
async def get_messages(
    conversation_id: Optional[str] = Query(None, description="Filter by conversation ID"),
    sender_id: Optional[str] = Query(None, description="Filter by sender ID"),
    limit: int = Query(10, ge=1, le=100, description="Number of messages to retrieve"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
) -> MessageResponse:
    """Retrieve messages with optional filters"""
    start_time = time.time()

    try:
        messages = await chromadb_service.get_messages(
            conversation_id=conversation_id,
            sender_id=sender_id,
            limit=limit,
            offset=offset,
        )

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        return MessageResponse(
            messages=messages,
            total_messages=len(messages),
            page_info={
                "limit": limit,
                "offset": offset,
                "has_more": len(messages) == limit,
            },
            processing_time_ms=processing_time,
        )

    except Exception as e:
        logger.error(f"❌ Failed to retrieve messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=MessageResponse)
async def search_messages(request: SemanticSearchRequest) -> MessageResponse:
    """Search messages using semantic similarity"""
    start_time = time.time()

    try:
        # Generate query embedding
        query_embedding = embedding_service.encode(request.query)

        # Search ChromaDB
        messages = await chromadb_service.search_similar(
            query_embedding=query_embedding,
            conversation_id=request.conversation_id,
            sender_id=request.sender_id,
            limit=request.limit,
        )

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        return MessageResponse(
            messages=messages,
            total_messages=len(messages),
            page_info={
                "query": request.query,
                "limit": request.limit,
                "search_type": "semantic",
            },
            processing_time_ms=processing_time,
        )

    except Exception as e:
        logger.error(f"❌ Semantic search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent", response_model=MessageResponse)
async def get_recent_messages(
    conversation_id: Optional[str] = Query(None, description="Filter by conversation ID"),
    limit: int = Query(10, ge=1, le=100, description="Number of recent messages to retrieve"),
) -> MessageResponse:
    """Get most recent messages"""
    start_time = time.time()

    try:
        messages = await chromadb_service.get_recent_messages(
            conversation_id=conversation_id,
            limit=limit,
        )

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        return MessageResponse(
            messages=messages,
            total_messages=len(messages),
            page_info={
                "limit": limit,
                "type": "recent",
                "conversation_id": conversation_id,
            },
            processing_time_ms=processing_time,
        )

    except Exception as e:
        logger.error(f"❌ Failed to retrieve recent messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{message_id}", response_model=MessageResult)
async def get_message_by_id(message_id: str) -> MessageResult:
    """Get a specific message by ID"""
    try:
        # Search for the specific message
        messages = await chromadb_service.get_messages(limit=1000)
        
        for message in messages:
            if message.message_id == message_id:
                return message
        
        raise HTTPException(status_code=404, detail=f"Message {message_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to retrieve message {message_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation/{conversation_id}", response_model=MessageResponse)
async def get_conversation_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=200, description="Number of messages to retrieve"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
) -> MessageResponse:
    """Get all messages from a specific conversation"""
    start_time = time.time()

    try:
        messages = await chromadb_service.get_messages(
            conversation_id=conversation_id,
            limit=limit,
            offset=offset,
        )

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        return MessageResponse(
            messages=messages,
            total_messages=len(messages),
            page_info={
                "conversation_id": conversation_id,
                "limit": limit,
                "offset": offset,
                "has_more": len(messages) == limit,
            },
            processing_time_ms=processing_time,
        )

    except Exception as e:
        logger.error(f"❌ Failed to retrieve conversation messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))
