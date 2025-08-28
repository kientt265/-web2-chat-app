"""
Base MCP server class.
"""

import logging
from typing import Any, Dict, List
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class BaseMCPServer(ABC):
    """Base class for MCP servers."""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        """Initialize base MCP server.
        
        Args:
            name: Server name
            config: Server configuration
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        
        # Initialize core service and API handler
        self.service = self.create_service()
        self.api_handler = self.create_api_handler()
        
        # Store tool definitions for easy access
        self._tool_definitions = self.api_handler.get_tool_definitions()
        
        self.logger.info(f"Initialized MCP server '{self.name}' with {len(self._tool_definitions)} tools")
    
    @abstractmethod
    def create_service(self):
        """Create the core service instance.
        
        Returns:
            Service instance
        """
        pass
    
    @abstractmethod
    def create_api_handler(self):
        """Create the API handler instance.
        
        Returns:
            API handler instance
        """
        pass
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on this server.
        
        Args:
            tool_name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        if tool_name not in self._tool_definitions:
            raise ValueError(f"Tool '{tool_name}' not found on server '{self.name}'")
        
        return await self.api_handler.handle_tool_call(tool_name, arguments)
    
    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get tool definitions for this server.
        
        Returns:
            Tool definitions
        """
        return self._tool_definitions
    
    def get_tool_names(self) -> List[str]:
        """Get list of tool names.
        
        Returns:
            List of tool names
        """
        return list(self._tool_definitions.keys())
    
    async def start(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the MCP server.
        
        Args:
            host: Server host
            port: Server port
        """
        try:
            self.logger.info(f"MCP server '{self.name}' is ready with layered architecture")
            # In the layered architecture, we don't need to start a separate server process
            # The tools are accessed directly through the API handler
        except Exception as e:
            self.logger.error(f"Failed to start MCP server '{self.name}': {e}")
            raise
    
    async def stop(self):
        """Stop the MCP server."""
        try:
            # Cleanup service resources
            if hasattr(self.service, 'cleanup'):
                await self.service.cleanup()
            
            self.logger.info(f"Stopped MCP server '{self.name}'")
        except Exception as e:
            self.logger.error(f"Error stopping MCP server '{self.name}': {e}")
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information.
        
        Returns:
            Server information dict
        """
        return {
            "name": self.name,
            "tools": self.get_tool_names(),
            "tool_count": len(self._tool_definitions),
            "config": self.config,
            "type": "layered"
        }
