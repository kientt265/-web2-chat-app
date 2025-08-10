"""
Web Scraper Tool API
HTTP endpoints for web scraping and content extraction
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import HttpUrl

from core.logging import get_logger
from .service import WebScraperService, ScrapeRequest, ScrapeResult

router = APIRouter()
logger = get_logger(__name__)

# Global service instance
scraper_service = WebScraperService()


@router.post("/scrape", response_model=ScrapeResult)
async def scrape_webpage(request: ScrapeRequest):
    """Scrape content from a webpage"""
    logger.info(f"🕷️ Scraping webpage: {request.url}")

    try:
        result = await scraper_service.scrape_webpage(request)
        return result

    except Exception as e:
        logger.error(f"❌ Error in scrape endpoint: {e}")
        return ScrapeResult(url=str(request.url), success=False, error=str(e))


@router.get("/extract-text")
async def extract_text_from_url(url: HttpUrl, max_length: Optional[int] = 5000):
    """Quick text extraction from URL"""
    try:
        result = await scraper_service.extract_text_only(url, max_length)
        return result
    except Exception as e:
        logger.error(f"❌ Text extraction error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/health")
async def scraper_health():
    """Health check for web scraper tool"""
    return {
        "status": "healthy",
        "capabilities": [
            "web_scraping",
            "text_extraction",
            "link_extraction",
            "image_extraction",
        ],
    }
