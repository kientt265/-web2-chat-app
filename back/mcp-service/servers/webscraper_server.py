#!/usr/bin/env python3
"""
Web Scraper MCP Server

An MCP server that provides web scraping and content extraction tools.
This is part of the MCP microservice.
"""

import logging
from typing import Any
import os

import httpx
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webscraper-mcp-server")

# Web scraper service URL (configured via environment or default)
EXT_TOOL_SERVICE_URL = os.getenv("EXT_TOOL_SERVICE_URL", "http://ext-tool:3006")
SCRAPER_SERVICE_URL = f"{EXT_TOOL_SERVICE_URL}/tools/scraper"

# Create FastMCP app
app = FastMCP("webscraper")


@app.tool()
def scrape_webpage(
    url: str,
    extract_links: bool = True,
    extract_images: bool = True,
    extract_text: bool = True,
    max_length: int = 5000
) -> str:
    """Scrape content from a webpage including text, links, and images.
    
    Args:
        url: URL of the webpage to scrape
        extract_links: Whether to extract all links from the page
        extract_images: Whether to extract image URLs from the page
        extract_text: Whether to extract text content from the page
        max_length: Maximum length of extracted text content
    
    Returns:
        String containing scraped webpage content
    """
    try:
        import asyncio
        
        async def _scrape():
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{SCRAPER_SERVICE_URL}/scrape",
                    json={
                        "url": url,
                        "extract_links": extract_links,
                        "extract_images": extract_images,
                        "extract_text": extract_text,
                        "max_length": max_length
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get("success", False):
                    content = f"**Scraped Content from {url}**\n\n"
                    
                    # Add text content
                    if result.get("text_content") and extract_text:
                        content += f"**Text Content:**\n{result['text_content']}\n\n"
                    
                    # Add links
                    if result.get("links") and extract_links:
                        content += f"**Links Found ({len(result['links'])}):**\n"
                        for link in result['links'][:10]:  # Limit to first 10 links
                            content += f"- {link.get('text', 'No text')}: {link.get('url', 'No URL')}\n"
                        if len(result['links']) > 10:
                            content += f"... and {len(result['links']) - 10} more links\n"
                        content += "\n"
                    
                    # Add images
                    if result.get("images") and extract_images:
                        content += f"**Images Found ({len(result['images'])}):**\n"
                        for img in result['images'][:5]:  # Limit to first 5 images
                            content += f"- {img.get('alt', 'No alt text')}: {img.get('src', 'No src')}\n"
                        if len(result['images']) > 5:
                            content += f"... and {len(result['images']) - 5} more images\n"
                        content += "\n"
                    
                    # Add metadata
                    if result.get("title"):
                        content += f"**Page Title:** {result['title']}\n"
                    if result.get("meta_description"):
                        content += f"**Meta Description:** {result['meta_description']}\n"
                    
                    return content
                else:
                    return f"Scraping Error: {result.get('error', 'Unknown error')}"
        
        return asyncio.run(_scrape())
        
    except Exception as e:
        logger.error(f"Scrape webpage error: {e}")
        return f"Error scraping webpage: {str(e)}"


@app.tool()
def extract_text(url: str, max_length: int = 5000) -> str:
    """Extract only text content from a webpage (faster than full scraping).
    
    Args:
        url: URL of the webpage to extract text from
        max_length: Maximum length of extracted text
    
    Returns:
        String containing extracted text content
    """
    try:
        import asyncio
        
        async def _extract():
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    f"{SCRAPER_SERVICE_URL}/extract-text",
                    params={
                        "url": url,
                        "max_length": max_length
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                content = f"**Text Content from {url}**\n\n"
                
                if result.get("success", True):  # Assume success if not specified
                    content += result.get("text", result.get("content", "No text content found"))
                    
                    # Add metadata if available
                    if result.get("title"):
                        content += f"\n\n**Page Title:** {result['title']}"
                    if result.get("length"):
                        content += f"\n**Content Length:** {result['length']} characters"
                        
                    return content
                else:
                    return f"Text Extraction Error: {result.get('error', 'Unknown error')}"
        
        return asyncio.run(_extract())
        
    except Exception as e:
        logger.error(f"Extract text error: {e}")
        return f"Error extracting text: {str(e)}"


if __name__ == "__main__":
    logger.info("Starting Web Scraper MCP Server")
    # This will be managed by the MCP service, not run directly
    app.run(transport='sse', port=8002)
