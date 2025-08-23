"""
Message Agent Service - Hybrid Main Application

This service provides message retrieval capabilities with graceful fallback
when ChromaDB dependencies are not available.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import uvicorn

# Core imports
from api.health import router as health_router
from api.messages import router as messages_router
from api.agent import router as agent_router

# Global service instances
chromadb_service = None
service_mode = "chromadb"  # "chromadb" or "mock"
start_time = datetime.now()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Try to import ChromaDB services, but don't fail if they're not available
try:
    from services.chromadb_service import ChromaDBService
    CHROMADB_AVAILABLE = True
    logger.info("ChromaDB dependencies are available")
except ImportError as e:
    logger.warning(f"ChromaDB dependencies not available: {e}")
    CHROMADB_AVAILABLE = False
    ChromaDBService = None


async def initialize_services():
    """Initialize services with graceful fallback."""
    global chromadb_service, service_mode
    
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
        
        logger.info("ChromaDB services initialized successfully")
        service_mode = "chromadb"
        
    except Exception as e:
        logger.warning(f"Failed to initialize ChromaDB services: {e}")
        logger.info("Falling back to mock mode")
        service_mode = "mock"
        chromadb_service = None


async def cleanup_services():
    """Cleanup services on shutdown."""
    if chromadb_service and hasattr(chromadb_service, 'close'):
        try:
            await chromadb_service.close()
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

# Include routers
app.include_router(health_router)
app.include_router(messages_router)
app.include_router(agent_router)


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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3008,
        reload=True,
        log_level="info"
    )
