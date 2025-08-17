"""
Message Agent Service - Hybrid Main Application

This service provides message retrieval capabilities with graceful fallback
when ChromaDB dependencies are not available.
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Core imports
from config.settings import settings
from models.api import MessageResponse, MessageResult, HealthResponse
from api.health import router as health_router

# Global service instances
chromadb_service = None
embedding_service = None
service_mode = "mock"  # "chromadb" or "mock"
start_time = datetime.now()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Try to import ChromaDB services, but don't fail if they're not available
try:
    from services.chromadb_service import ChromaDBService
    from services.embedding_service import EmbeddingService
    CHROMADB_AVAILABLE = True
    logger.info("ChromaDB dependencies are available")
except ImportError as e:
    logger.warning(f"ChromaDB dependencies not available: {e}")
    CHROMADB_AVAILABLE = False
    ChromaDBService = None
    EmbeddingService = None


async def initialize_services():
    """Initialize services with graceful fallback."""
    global chromadb_service, embedding_service, service_mode
    
    if not CHROMADB_AVAILABLE:
        logger.info("ChromaDB dependencies not installed, using mock mode")
        service_mode = "mock"
        return
    
    try:
        logger.info("Attempting to initialize ChromaDB services...")
        
        # Try to initialize ChromaDB service
        chromadb_service = ChromaDBService()
        success = await chromadb_service.initialize()
        
        if not success:
            raise Exception("ChromaDB initialization failed")
            
        # Try to initialize embedding service
        embedding_service = EmbeddingService()
        await embedding_service.initialize()
        
        logger.info("ChromaDB services initialized successfully")
        service_mode = "chromadb"
        
    except Exception as e:
        logger.warning(f"Failed to initialize ChromaDB services: {e}")
        logger.info("Falling back to mock mode")
        service_mode = "mock"
        chromadb_service = None
        embedding_service = None


async def cleanup_services():
    """Cleanup services on shutdown."""
    if chromadb_service and hasattr(chromadb_service, 'close'):
        try:
            await chromadb_service.close()
        except:
            pass
    if embedding_service and hasattr(embedding_service, 'cleanup'):
        try:
            await embedding_service.cleanup()
        except:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Message Agent Service")
    await initialize_services()
    logger.info(f"Service started in {service_mode} mode")
    
    yield
    
    logger.info("Shutting down Message Agent Service")
    await cleanup_services()


# Create FastAPI app
app = FastAPI(
    title="Message Agent Service",
    description="Message retrieval service with ChromaDB integration and mock fallback",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include health router
app.include_router(health_router)


@app.get("/", tags=["info"])
async def root():
    """Root endpoint with service information."""
    global start_time
    uptime = (datetime.now() - start_time).total_seconds()
    
    return {
        "message": "Welcome to the Message Agent Service. See /docs for Swagger UI.",
        "version": "1.0.0",
        "service": "message-agent",
        "mode": service_mode,
        "chromadb_available": CHROMADB_AVAILABLE,
        "chromadb_connected": service_mode == "chromadb",
        "uptime_seconds": uptime
    }


async def generate_mock_messages(
    conversation_id: Optional[str] = None,
    sender_id: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
) -> tuple[list[MessageResult], int]:
    """Generate mock messages for fallback mode."""
    
    # Generate mock data
    messages = []
    total_messages = 50  # Mock total
    
    for i in range(offset, min(offset + limit, total_messages)):
        # Apply filters
        if conversation_id:
            mock_conversation_id = conversation_id
        else:
            mock_conversation_id = f"conv-{i % 4}"
        
        if sender_id:
            mock_sender_id = sender_id
        else:
            mock_sender_id = f"user-{i % 2}"
        
        message = MessageResult(
            message_id=f"msg-{i}",
            conversation_id=mock_conversation_id,
            sender_id=mock_sender_id,
            content=f"Mock message content {i}",
            sent_at=datetime.now(),
            similarity_score=None
        )
        messages.append(message)
    
    return messages, total_messages


@app.get("/api/v1/messages/", response_model=MessageResponse)
async def get_messages(
    conversation_id: Optional[str] = Query(None, description="Filter by conversation ID"),
    sender_id: Optional[str] = Query(None, description="Filter by sender ID"),
    limit: int = Query(10, ge=1, le=100, description="Number of messages to retrieve"),
    offset: int = Query(0, ge=0, description="Number of messages to skip")
):
    """
    Retrieve messages with optional filters.
    
    Uses ChromaDB when available, falls back to mock data otherwise.
    """
    start_time_req = asyncio.get_event_loop().time()
    
    try:
        if service_mode == "chromadb" and chromadb_service:
            # Use ChromaDB service
            messages = await chromadb_service.get_messages(
                conversation_id=conversation_id,
                sender_id=sender_id,
                limit=limit,
                offset=offset
            )
            
            total_messages = len(messages)
            has_more = len(messages) == limit
            
        else:
            # Use mock data
            messages, total_messages = await generate_mock_messages(
                conversation_id=conversation_id,
                sender_id=sender_id,
                limit=limit,
                offset=offset
            )
            has_more = (offset + limit) < total_messages
        
        end_time_req = asyncio.get_event_loop().time()
        processing_time = (end_time_req - start_time_req) * 1000
        
        return MessageResponse(
            messages=messages,
            total_messages=total_messages,
            page_info={
                "limit": limit,
                "offset": offset,
                "has_more": has_more,
                "mode": service_mode
            },
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error retrieving messages: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving messages: {str(e)}")


@app.post("/api/v1/search", response_model=MessageResponse)
async def search_messages(
    query: str = Query(..., description="Search query"),
    conversation_id: Optional[str] = Query(None, description="Filter by conversation ID"),
    limit: int = Query(10, ge=1, le=100, description="Number of messages to retrieve"),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity score")
):
    """
    Search messages using semantic similarity.
    
    Uses ChromaDB when available, returns mock results otherwise.
    """
    start_time_req = asyncio.get_event_loop().time()
    
    try:
        if service_mode == "chromadb" and chromadb_service and embedding_service:
            # Generate embedding for the query
            query_embedding = embedding_service.encode(query)
            
            # Use ChromaDB for semantic search
            messages = await chromadb_service.search_similar(
                query_embedding=query_embedding,
                conversation_id=conversation_id,
                limit=limit
            )
            
            # Filter by similarity threshold
            filtered_messages = [msg for msg in messages if msg.similarity_score and msg.similarity_score >= similarity_threshold]
            
            total_messages = len(filtered_messages)
            has_more = False  # Search results don't have pagination
            
        else:
            # Return mock search results
            messages, _ = await generate_mock_messages(
                conversation_id=conversation_id,
                limit=min(limit, 5)
            )
            
            # Add mock similarity scores
            for i, message in enumerate(messages):
                message.similarity_score = max(0.8 - (i * 0.05), 0.6)
            
            # Filter by threshold
            filtered_messages = [msg for msg in messages if msg.similarity_score >= similarity_threshold]
            total_messages = len(filtered_messages)
            has_more = False
        
        end_time_req = asyncio.get_event_loop().time()
        processing_time = (end_time_req - start_time_req) * 1000
        
        return MessageResponse(
            messages=filtered_messages,
            total_messages=total_messages,
            page_info={
                "query": query,
                "limit": limit,
                "similarity_threshold": similarity_threshold,
                "has_more": has_more,
                "mode": service_mode
            },
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error searching messages: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching messages: {str(e)}")


@app.get("/api/v1/messages/recent", response_model=MessageResponse)
async def get_recent_messages(
    conversation_id: Optional[str] = Query(None, description="Filter by conversation ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of recent messages to retrieve")
):
    """
    Get recent messages from ChromaDB or mock data.
    """
    start_time_req = asyncio.get_event_loop().time()
    
    try:
        if service_mode == "chromadb" and chromadb_service:
            # Use ChromaDB service
            messages = await chromadb_service.get_recent_messages(
                conversation_id=conversation_id,
                limit=limit
            )
            total_messages = len(messages)
            
        else:
            # Use mock data sorted by recent
            messages, _ = await generate_mock_messages(
                conversation_id=conversation_id,
                limit=limit
            )
            total_messages = len(messages)
        
        end_time_req = asyncio.get_event_loop().time()
        processing_time = (end_time_req - start_time_req) * 1000
        
        return MessageResponse(
            messages=messages,
            total_messages=total_messages,
            page_info={
                "limit": limit,
                "type": "recent",
                "has_more": False,
                "mode": service_mode
            },
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error retrieving recent messages: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving recent messages: {str(e)}")


@app.get("/api/v1/messages/{message_id}", response_model=MessageResult)
async def get_message_by_id(message_id: str):
    """
    Get a specific message by ID.
    """
    try:
        # For now, return mock response
        message = MessageResult(
            message_id=message_id,
            conversation_id="conv-1",
            sender_id="user-1",
            content=f"Mock message content for {message_id}",
            sent_at=datetime.now(),
            similarity_score=None
        )
        
        return message
        
    except Exception as e:
        logger.error(f"Error retrieving message {message_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Message {message_id} not found")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3008,
        reload=True,
        log_level="info"
    )
