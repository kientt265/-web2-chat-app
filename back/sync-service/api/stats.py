"""
Statistics endpoints
"""
from fastapi import APIRouter, HTTPException

from models.api import StatsResponse
from services.chromadb_service import chromadb_service
from config.settings import settings
from core.logging import get_logger

router = APIRouter(prefix="/stats", tags=["stats"])
logger = get_logger(__name__)


@router.get("", response_model=StatsResponse)
async def get_stats():
    """Get sync service statistics"""
    try:
        # Get ChromaDB stats
        chroma_stats = await chromadb_service.get_stats()
        
        if chroma_stats.get("status") == "error":
            raise HTTPException(status_code=503, detail="ChromaDB not available")
        
        return StatsResponse(
            chromadb_documents=chroma_stats.get("total_documents", 0),
            embedding_model=settings.embedding_model_name,
            kafka_topics=settings.cdc_topics,
            status="operational"
        )
        
    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
