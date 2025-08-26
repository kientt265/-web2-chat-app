from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import HttpUrl

from .service import TavilyService

from core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

tavily_service = TavilyService()

@router.post("/search")
async def search(query: str, max_results: Optional[int] = 10):
    try:
        results = tavily_service.search(query, max_results)
        return results
    except Exception as e:
        logger.error(f"Error occurred while searching: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

