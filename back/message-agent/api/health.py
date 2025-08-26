"""
Health check endpoints
"""

from datetime import datetime
from fastapi import APIRouter

from models.api import HealthResponse, StatsResponse
from config.settings import settings
from core.logging import get_logger

router = APIRouter(tags=["health"])
logger = get_logger(__name__)

# Track service start time
service_start_time = datetime.now()

# Try to import ChromaDB service, but don't fail if not available
try:
    from services.chromadb_service import chromadb_service

    CHROMADB_SERVICE_AVAILABLE = True
except ImportError:
    chromadb_service = None
    CHROMADB_SERVICE_AVAILABLE = False


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        service=settings.app_name,
        version=settings.app_version,
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats() -> StatsResponse:
    """Get service statistics"""
    try:
        if CHROMADB_SERVICE_AVAILABLE and chromadb_service:
            chromadb_stats = await chromadb_service.get_stats()
            status = chromadb_stats.get("status", "unknown")
            docs_count = chromadb_stats.get("total_documents", 0)
        else:
            status = "chromadb_unavailable"
            docs_count = 0

        uptime = (datetime.now() - service_start_time).total_seconds()

        return StatsResponse(
            chromadb_documents=docs_count,
            embedding_model=settings.embedding_model_name,
            status=status,
            uptime_seconds=uptime,
        )

    except Exception as e:
        logger.error(f"❌ Failed to get stats: {e}")
        return StatsResponse(
            chromadb_documents=0,
            embedding_model=settings.embedding_model_name,
            status="error",
        )
