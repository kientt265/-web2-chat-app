"""
Webscraper API handler.
"""

import logging
from typing import Any, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.api_base import BaseAPIHandler


logger = logging.getLogger(__name__)


class WebscraperAPIHandler(BaseAPIHandler):
    """API handler for webscraper server."""

    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get tool definitions for webscraper server."""
        return {
            "scrape_webpage": {
                "description": "Scrape content from a webpage including text, links, and images",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL of the webpage to scrape",
                        },
                        "extract_links": {
                            "type": "boolean",
                            "description": "Whether to extract all links from the page",
                            "default": True,
                        },
                        "extract_images": {
                            "type": "boolean",
                            "description": "Whether to extract image URLs from the page",
                            "default": True,
                        },
                        "extract_text": {
                            "type": "boolean",
                            "description": "Whether to extract text content from the page",
                            "default": True,
                        },
                        "max_length": {
                            "type": "integer",
                            "description": "Maximum length of extracted text content",
                            "default": 5000,
                        },
                    },
                    "required": ["url"],
                },
            },
            "extract_text": {
                "description": "Extract only text content from a webpage (faster than full scraping)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL of the webpage to extract text from",
                        },
                        "max_length": {
                            "type": "integer",
                            "description": "Maximum length of extracted text",
                            "default": 5000,
                        },
                    },
                    "required": ["url"],
                },
            },
        }

    async def handle_scrape_webpage(self, arguments: Dict[str, Any]) -> str:
        """Handle scrape_webpage tool call."""
        validated_args = self._validate_arguments(
            arguments,
            required_args=["url"],
            optional_args={
                "extract_links": True,
                "extract_images": True,
                "extract_text": True,
                "max_length": 5000,
            },
        )

        try:
            result = await self.service.scrape_webpage(
                url=validated_args["url"],
                extract_links=validated_args["extract_links"],
                extract_images=validated_args["extract_images"],
                extract_text=validated_args["extract_text"],
                max_length=validated_args["max_length"],
            )
            return result["formatted"]
        except Exception as e:
            raise Exception(f"Webpage scraping error: {str(e)}")

    async def handle_extract_text(self, arguments: Dict[str, Any]) -> str:
        """Handle extract_text tool call."""
        validated_args = self._validate_arguments(
            arguments, required_args=["url"], optional_args={"max_length": 5000}
        )

        try:
            result = await self.service.extract_text(
                url=validated_args["url"], max_length=validated_args["max_length"]
            )
            return result["formatted"]
        except Exception as e:
            raise Exception(f"Text extraction error: {str(e)}")
