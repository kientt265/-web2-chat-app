"""
Webscraper service core logic.
"""

import logging
import httpx
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.core_base import BaseService


logger = logging.getLogger(__name__)


class WebscraperService(BaseService):
    """Core service for webscraper operations."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize webscraper service."""
        super().__init__(config)
        self.timeout = config.get("timeout", 30.0) if config else 30.0

    async def health_check(self) -> bool:
        """Check if webscraper service is healthy."""
        try:
            # Test a simple HTTP request
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("https://httpbin.org/status/200")
                return response.status_code == 200
        except Exception:
            return False

    async def scrape_webpage(
        self,
        url: str,
        extract_links: bool = True,
        extract_images: bool = True,
        extract_text: bool = True,
        max_length: int = 5000,
    ) -> Dict[str, Any]:
        """Scrape content from a webpage.

        Args:
            url: URL of the webpage to scrape
            extract_links: Whether to extract all links from the page
            extract_images: Whether to extract image URLs from the page
            extract_text: Whether to extract text content from the page
            max_length: Maximum length of extracted text content

        Returns:
            Scraped webpage content
        """
        try:
            self.logger.info(f"🕷️ Scraping webpage: {url}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()

                # Parse HTML content
                soup = BeautifulSoup(response.content, "html.parser")

                # Extract title
                title = self._extract_title(soup)

                # Extract text content
                text_content = None
                if extract_text:
                    text_content = self._extract_text(soup, max_length)

                # Extract links
                links = []
                if extract_links:
                    links = self._extract_links(soup, url)

                # Extract images
                images = []
                if extract_images:
                    images = self._extract_images(soup, url)

                # Extract metadata
                metadata = self._extract_metadata(soup, response)

                self.logger.info(f"✅ Successfully scraped {url}")

                # Format the content
                content = f"**Scraped Content from {url}**\n\n"

                # Add text content
                if text_content and extract_text:
                    content += f"**Text Content:**\n{text_content}\n\n"

                # Add links
                if links and extract_links:
                    content += f"**Links Found ({len(links)}):**\n"
                    for link_info in links[:10]:  # Limit to first 10 links
                        if isinstance(link_info, dict):
                            content += f"- {link_info.get('text', 'No text')}: {link_info.get('url', 'No URL')}\n"
                        else:
                            content += f"- {link_info}\n"
                    if len(links) > 10:
                        content += f"... and {len(links) - 10} more links\n"
                    content += "\n"

                # Add images
                if images and extract_images:
                    content += f"**Images Found ({len(images)}):**\n"
                    for img_info in images[:5]:  # Limit to first 5 images
                        if isinstance(img_info, dict):
                            content += f"- {img_info.get('alt', 'No alt text')}: {img_info.get('src', 'No src')}\n"
                        else:
                            content += f"- {img_info}\n"
                    if len(images) > 5:
                        content += f"... and {len(images) - 5} more images\n"
                    content += "\n"

                # Add metadata
                if title:
                    content += f"**Page Title:** {title}\n"
                if metadata.get("description"):
                    content += f"**Meta Description:** {metadata['description']}\n"

                return {
                    "success": True,
                    "url": url,
                    "title": title,
                    "meta_description": metadata.get("description"),
                    "text_content": text_content,
                    "links": links[:50],  # Limit to 50 links
                    "images": images[:20],  # Limit to 20 images
                    "metadata": metadata,
                    "formatted": content,
                }

        except Exception as e:
            self.logger.error(f"Scrape webpage error: {e}")
            raise Exception(f"Webpage scraping failed: {str(e)}")

    async def extract_text(self, url: str, max_length: int = 5000) -> Dict[str, Any]:
        """Extract only text content from a webpage.

        Args:
            url: URL of the webpage to extract text from
            max_length: Maximum length of extracted text

        Returns:
            Extracted text content
        """
        try:
            self.logger.info(f"📄 Extracting text from: {url}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()

                # Parse HTML content
                soup = BeautifulSoup(response.content, "html.parser")

                # Extract title and text
                title = self._extract_title(soup)
                text_content = self._extract_text(soup, max_length)

                self.logger.info(f"✅ Successfully extracted text from {url}")

                content = f"**Text Content from {url}**\n\n"
                content += text_content

                # Add metadata if available
                if title:
                    content += f"\n\n**Page Title:** {title}"
                content += f"\n**Content Length:** {len(text_content)} characters"

                return {
                    "success": True,
                    "url": url,
                    "title": title,
                    "text": text_content,
                    "length": len(text_content),
                    "formatted": content,
                }

        except Exception as e:
            self.logger.error(f"Extract text error: {e}")
            raise Exception(f"Text extraction failed: {str(e)}")

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

    def _extract_links(
        self, soup: BeautifulSoup, base_url: str
    ) -> List[Dict[str, str]]:
        """Extract links from HTML"""
        links = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text().strip()

            # Convert relative URLs to absolute
            if href.startswith("http"):
                full_url = href
            elif href.startswith("/"):
                # Parse base URL to get scheme and host
                try:
                    from urllib.parse import urlparse

                    parsed = urlparse(base_url)
                    full_url = f"{parsed.scheme}://{parsed.netloc}{href}"
                except Exception:
                    full_url = href
            else:
                full_url = href

            links.append({"text": text or "No text", "url": full_url})
        return links

    def _extract_images(
        self, soup: BeautifulSoup, base_url: str
    ) -> List[Dict[str, str]]:
        """Extract image URLs from HTML"""
        images = []
        for img in soup.find_all("img", src=True):
            src = img["src"]
            alt = img.get("alt", "")

            # Convert relative URLs to absolute
            if src.startswith("http"):
                full_url = src
            elif src.startswith("/"):
                # Parse base URL to get scheme and host
                try:
                    from urllib.parse import urlparse

                    parsed = urlparse(base_url)
                    full_url = f"{parsed.scheme}://{parsed.netloc}{src}"
                except Exception:
                    full_url = src
            else:
                full_url = src

            images.append({"src": full_url, "alt": alt or "No alt text"})
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
