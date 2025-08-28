"""
Calculator MCP Server - Restructured with API and Core layers.
"""

import logging
from typing import Any, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.server_base import BaseMCPServer
from .core import CalculatorService
from .api import CalculatorAPIHandler


logger = logging.getLogger(__name__)


class CalculatorServer(BaseMCPServer):
    """Calculator MCP Server with layered architecture."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize calculator server."""
        super().__init__("calculator", config)
        self.logger.info("Calculator MCP Server initialized with layered architecture")

    def create_service(self) -> CalculatorService:
        """Create the calculator service instance."""
        return CalculatorService(self.config)

    def create_api_handler(self) -> CalculatorAPIHandler:
        """Create the calculator API handler instance."""
        return CalculatorAPIHandler(self.service)


# For backward compatibility and standalone running
if __name__ == "__main__":
    import asyncio
    import os

    async def main():
        # Configuration
        # Initialize service with configuration
        service_config = {}

        # Create and start server
        server = CalculatorServer(service_config)
        await server.start(
            host="0.0.0.0", port=int(os.getenv("CALCULATOR_SERVER_PORT", "8001"))
        )

    asyncio.run(main())
