"""
Health check endpoints
"""
from datetime import datetime
from fastapi import APIRouter

from models.api import HealthResponse
from config.settings import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        service=settings.app_name,
        version=settings.app_version
    )
