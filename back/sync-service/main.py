"""
Chat Sync Service - Main Application
Structured FastAPI application for CDC processing and vector search
"""
import sys
import os
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime

# Add current directory to Python path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.logging import setup_logging, get_logger
from config.settings import settings
from services.chromadb_service import chromadb_service
from services.embedding_service import embedding_service
from services.kafka_service import kafka_service
from processors.cdc_processor import CDCProcessor
from api import health, search, stats

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Global state
start_time = datetime.now()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    
    # Initialize services
    success = True
    
    logger.info("Initializing embedding service...")
    success &= await embedding_service.initialize()
    
    logger.info("Initializing ChromaDB service...")
    success &= await chromadb_service.initialize()
    
    logger.info("Initializing Kafka service...")
    success &= await kafka_service.initialize(CDCProcessor.process_cdc_event)
    
    if success:
        # Start CDC consumer in background
        asyncio.create_task(kafka_service.start_consuming())
        logger.info("✅ All services initialized successfully")
    else:
        logger.error("❌ Failed to initialize services")
        raise RuntimeError("Service initialization failed")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down services...")
    await kafka_service.stop_consuming()
    logger.info("👋 Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="CDC consumer service for syncing chat data to ChromaDB",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(search.router)
app.include_router(stats.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "uptime_seconds": (datetime.now() - start_time).total_seconds()
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"🔧 Starting {settings.app_name} on {settings.host}:{settings.port}")
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=settings.debug
    )
