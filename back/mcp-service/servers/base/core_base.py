"""
Base service class for MCP servers core logic.
"""

import logging
import httpx
import os
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class BaseService(ABC):
    """Base class for MCP server core services."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize base service.
        
        Args:
            config: Service configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self._http_client: Optional[httpx.AsyncClient] = None
    
    @property
    def http_client(self) -> httpx.AsyncClient:
        """Get HTTP client instance."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=60.0)
        return self._http_client
    
    async def cleanup(self):
        """Cleanup resources."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the service is healthy.
        
        Returns:
            True if service is healthy, False otherwise
        """
        pass
