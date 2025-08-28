"""
Webscraper MCP Server - Restructured with API and Core layers.
"""

import logging
from typing import Any, Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.server_base import BaseMCPServer
from .core import WebscraperService
from .api import WebscraperAPIHandler


logger = logging.getLogger(__name__)


class WebscraperServer(BaseMCPServer):
    """Webscraper MCP Server with layered architecture."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize webscraper server."""
        super().__init__("webscraper", config)
        self.logger.info("Webscraper MCP Server initialized with layered architecture")
    
    def create_service(self) -> WebscraperService:
        """Create the webscraper service instance."""
        return WebscraperService(self.config)
    
    def create_api_handler(self) -> WebscraperAPIHandler:
        """Create the webscraper API handler instance."""
        return WebscraperAPIHandler(self.service)


# For backward compatibility and standalone running
if __name__ == "__main__":
    import asyncio
    import os
    
    async def main():
        # Configuration
        # Initialize service with configuration
        service_config = {}
        
        # Create and start server
        server = WebscraperServer(service_config)
        await server.start(
            host="0.0.0.0",
            port=int(os.getenv("WEBSCRAPER_SERVER_PORT", "8002"))
        )
    
    asyncio.run(main())
