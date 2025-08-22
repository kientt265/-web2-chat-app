"""
Message retrieval endpoints
"""

import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import ORJSONResponse

from models.api import (
    SemanticSearchRequest,
    MessageResult,
)
from services.chromadb_service import chromadb_service
from services.message_service import message_service
from core.logging import get_logger

router = APIRouter(prefix="/messages", tags=["messages"])
logger = get_logger(__name__)


@router.get("/", response_model=None)
async def get_messages(
    conversation_id: Optional[str] = Query(None, description="Filter by conversation ID"),
    sender_id: Optional[str] = Query(None, description="Filter by sender ID"),
    limit: int = Query(10, ge=1, le=100, description="Number of messages to retrieve"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
) -> ORJSONResponse:
    """Retrieve messages with optional filters"""

    try:
        messages = await chromadb_service.get_messages(
            conversation_id=conversation_id,
            sender_id=sender_id,
            limit=limit,
            offset=offset,
        )

        return ORJSONResponse(
            content={
                "messages": messages,
                "total_messages": len(messages),
                "page_info": {
                    "limit": limit,
                    "offset": offset,
                    "has_more": len(messages) == limit,
                },
            },
            status_code=200,
        )

    except Exception as e:
        logger.error(f"❌ Failed to retrieve messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=None)
async def search_messages(request: SemanticSearchRequest) -> ORJSONResponse:
    """Search messages using semantic similarity"""

    try:
        messages = await message_service.search_messages(
            query_texts=request.query,
            conversation_id=request.conversation_id,
            sender_id=request.sender_id,
            limit=request.limit,
        )

        return ORJSONResponse(
            content={
                "messages": messages,
                "total_messages": len(messages),
                "page_info": {
                    "query": request.query,
                    "limit": request.limit,
                    "search_type": "semantic",
                },
            },
            status_code=200,
        )

    except Exception as e:
        logger.error(f"❌ Semantic search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent", response_model=None)
async def get_recent_messages(
    conversation_id: Optional[str] = Query(None, description="Filter by conversation ID"),
    limit: int = Query(10, ge=1, le=100, description="Number of recent messages to retrieve"),
) -> ORJSONResponse:
    """Get most recent messages"""
    start_time = time.time()

    try:
        messages = await chromadb_service.get_recent_messages(
            conversation_id=conversation_id,
            limit=limit,
        )

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        return ORJSONResponse(
            content={
                "messages": messages,
                "total_messages": len(messages),
                "page_info": {
                    "limit": limit,
                    "type": "recent",
                    "conversation_id": conversation_id,
                },
                "processing_time_ms": processing_time,
            },
            status_code=200,
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

    except Exception as e:
        logger.error(f"❌ Failed to retrieve message {message_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))