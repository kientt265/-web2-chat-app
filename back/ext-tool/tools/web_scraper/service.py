"""
Web Scraper Service
Business logic for web scraping and content extraction
"""

import httpx
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl
from bs4 import BeautifulSoup

from core.logging import get_logger

logger = get_logger(__name__)


class ScrapeRequest(BaseModel):
    """Web scraping request model"""

    url: HttpUrl
    extract_text: bool = True
    extract_links: bool = False
    extract_images: bool = False
    max_length: Optional[int] = 10000


class ScrapeResult(BaseModel):
    """Web scraping result model"""

    url: str
    title: Optional[str] = None
    text_content: Optional[str] = None
    links: List[str] = []
    images: List[str] = []
    metadata: Dict[str, Any] = {}
    success: bool = True
    error: Optional[str] = None


class WebScraperService:
    """Service for web scraping operations"""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    async def scrape_webpage(self, request: ScrapeRequest) -> ScrapeResult:
        """Scrape content from a webpage"""
        logger.info(f"🕷️ Scraping webpage: {request.url}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(str(request.url))
                response.raise_for_status()

                # Parse HTML content
                soup = BeautifulSoup(response.content, "html.parser")

                # Extract title
                title = self._extract_title(soup)

                # Extract text content
                text_content = None
                if request.extract_text:
                    text_content = self._extract_text(soup, request.max_length)

                # Extract links
                links = []
                if request.extract_links:
                    links = self._extract_links(soup, request.url)

                # Extract images
                images = []
                if request.extract_images:
                    images = self._extract_images(soup, request.url)

                # Extract metadata
                metadata = self._extract_metadata(soup, response)

                logger.info(f"✅ Successfully scraped {request.url}")

                return ScrapeResult(
                    url=str(request.url),
                    title=title,
                    text_content=text_content,
                    links=links[:50],  # Limit to 50 links
                    images=images[:20],  # Limit to 20 images
                    metadata=metadata,
                    success=True,
                )

        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error scraping {request.url}: {e}")
            return ScrapeResult(
                url=str(request.url), success=False, error=f"HTTP error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"❌ Error scraping {request.url}: {e}")
            return ScrapeResult(url=str(request.url), success=False, error=str(e))

    async def extract_text_only(
        self, url: HttpUrl, max_length: Optional[int] = 5000
    ) -> Dict[str, Any]:
        """Quick text extraction from URL"""
        request = ScrapeRequest(
            url=url,
            extract_text=True,
            extract_links=False,
            extract_images=False,
            max_length=max_length,
        )

        result = await self.scrape_webpage(request)

        if result.success:
            return {
                "url": result.url,
                "title": result.title,
                "text": result.text_content,
                "length": len(result.text_content) if result.text_content else 0,
            }
        else:
            raise Exception(result.error)

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract title from HTML"""
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text().strip()
        return None

    def _extract_text(self, soup: BeautifulSoup, max_length: Optional[int]) -> str:
        """Extract clean text content from HTML"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text_content = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text_content = " ".join(chunk for chunk in chunks if chunk)

        # Apply length limit
        if max_length and len(text_content) > max_length:
            text_content = text_content[:max_length] + "..."

        return text_content

    def _extract_links(self, soup: BeautifulSoup, base_url: HttpUrl) -> List[str]:
        """Extract links from HTML"""
        links = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.startswith("http"):
                links.append(href)
            elif href.startswith("/"):
                # Convert relative URLs to absolute
                base = f"{base_url.scheme}://{base_url.host}"
                links.append(base + href)
        return links

    def _extract_images(self, soup: BeautifulSoup, base_url: HttpUrl) -> List[str]:
        """Extract image URLs from HTML"""
        images = []
        for img in soup.find_all("img", src=True):
            src = img["src"]
            if src.startswith("http"):
                images.append(src)
            elif src.startswith("/"):
                # Convert relative URLs to absolute
                base = f"{base_url.scheme}://{base_url.host}"
                images.append(base + src)
        return images

    def _extract_metadata(
        self, soup: BeautifulSoup, response: httpx.Response
    ) -> Dict[str, Any]:
        """Extract metadata from HTML and response"""
        metadata = {
            "content_type": response.headers.get("content-type"),
            "status_code": response.status_code,
            "content_length": len(response.content),
        }

        # Look for meta tags
        meta_description = soup.find("meta", attrs={"name": "description"})
        if meta_description:
            metadata["description"] = meta_description.get("content", "").strip()

        meta_keywords = soup.find("meta", attrs={"name": "keywords"})
        if meta_keywords:
            metadata["keywords"] = meta_keywords.get("content", "").strip()

        return metadata
