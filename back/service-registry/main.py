"""
Service Registry Main Application

This module provides a centralized service registry using Zookeeper for
service discovery and coordination in a distributed microservices architecture.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from core.logging import setup_logging, get_logger
from core.zookeeper_client import ZookeeperClient
from core.service_registry import ServiceRegistry
from api.endpoints import router
from api.dependencies import get_service_registry

# Setup logging
setup_logging(settings.log_level)
logger = get_logger(__name__)

# Global state
start_time = datetime.now()
registry: ServiceRegistry = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    global registry
    
    # Startup
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    
    try:
        # Initialize Zookeeper client
        zk_client = ZookeeperClient(
            hosts=settings.zookeeper_hosts,
            timeout=settings.zookeeper_timeout
        )
        
        # Initialize service registry
        registry = ServiceRegistry(zk_client)
        
        # Store in global dependencies
        import api.dependencies as deps
        deps._service_registry = registry
        deps._zk_client = zk_client
        
        # Start the registry
        await registry.start()
        
        logger.info("✅ Service Registry initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Service Registry: {e}")
        raise RuntimeError("Service Registry initialization failed")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Service Registry...")
    
    if registry:
        await registry.stop()
    
    logger.info("👋 Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Centralized service registry and discovery using Zookeeper",
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

# Include API router
app.include_router(router, prefix="/api/v1", tags=["service-registry"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "uptime_seconds": (datetime.now() - start_time).total_seconds(),
        "zookeeper_hosts": settings.zookeeper_hosts,
        "services_root_path": settings.services_root_path,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    
    # Check Zookeeper connection
    zk_connected = False
    if registry and registry.zk_client:
        zk_connected = registry.zk_client.is_connected()
    
    status = "healthy" if zk_connected else "unhealthy"
    
    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "service": settings.app_name,
        "zookeeper_connected": zk_connected,
        "registered_services": len(registry.services) if registry else 0
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
