"""
External Tools Service - Main Application
HTTP API service for AI agent tools and utilities
"""

import sys
import os
from contextlib import asynccontextmanager
from datetime import datetime

# Add current directory to Python path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.middleware.cors import CORSMiddleware

from core.logging import setup_logging, get_logger
from config.settings import settings
from fastapi import FastAPI

# Import tool routers
from tools.search_messages.api import router as search_messages_router
from tools.web_scraper.api import router as scraper_router
from tools.calculator.api import router as calc_router

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

    # Initialize tool services
    success = True

    logger.info("Initializing tool services...")
    # Add any global initialization here

    if success:
        logger.info("✅ All tool services initialized successfully")
    else:
        logger.error("❌ Failed to initialize tool services")
        raise RuntimeError("Tool service initialization failed")

    yield

    # Shutdown
    logger.info("🛑 Shutting down tool services...")
    logger.info("👋 Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="HTTP API service for AI agent tools and utilities",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include tool routers
app.include_router(
    search_messages_router, prefix="/tools/search-messages", tags=["Search Messages"]
)
app.include_router(scraper_router, prefix="/tools/scraper", tags=["Web Scraper"])
app.include_router(calc_router, prefix="/tools/calculator", tags=["Calculator"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "uptime_seconds": (datetime.now() - start_time).total_seconds(),
        "available_tools": [
            "/tools/search-messages",
            "/tools/scraper",
            "/tools/files",
            "/tools/calculator",
        ],
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": settings.app_name,
    }


@app.get("/tools")
async def list_tools():
    """List all available tools"""
    return {
        "tools": [
            {
                "name": "search-messages",
                "path": "/tools/search-messages",
                "description": "Semantic search tools for chat messages",
            },
            {
                "name": "scraper",
                "path": "/tools/scraper",
                "description": "Web scraping and content extraction",
            },
            {
                "name": "calculator",
                "path": "/tools/calculator",
                "description": "Mathematical calculations and utilities",
            },
        ]
    }


if __name__ == "__main__":
    import uvicorn

    logger.info(f"🔧 Starting {settings.app_name} on {settings.host}:{settings.port}")
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=settings.debug,
    )
