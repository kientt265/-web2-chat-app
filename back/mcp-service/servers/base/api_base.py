"""
Base API handler for MCP servers.
"""

import logging
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class BaseAPIHandler(ABC):
    """Base class for MCP server API handlers."""
    
    def __init__(self, service_instance):
        """Initialize API handler with core service instance.
        
        Args:
            service_instance: Instance of the core service
        """
        self.service = service_instance
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    @abstractmethod
    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get tool definitions for this server.
        
        Returns:
            Dictionary mapping tool names to their definitions
        """
        pass
    
    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a tool call request.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool not found or arguments invalid
        """
        try:
            # Validate tool exists
            tool_definitions = self.get_tool_definitions()
            if tool_name not in tool_definitions:
                raise ValueError(f"Tool '{tool_name}' not found")
            
            # Get tool handler method
            handler_method = getattr(self, f"handle_{tool_name}", None)
            if handler_method is None:
                raise ValueError(f"No handler method found for tool '{tool_name}'")
            
            # Call the handler
            result = await handler_method(arguments)
            
            return {
                "success": True,
                "result": result,
                "tool": tool_name
            }
            
        except Exception as e:
            self.logger.error(f"Error handling tool call '{tool_name}': {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name
            }
    
    def _validate_arguments(self, arguments: Dict[str, Any], required_args: list, optional_args: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate and process tool arguments.
        
        Args:
            arguments: Raw arguments
            required_args: List of required argument names
            optional_args: Dict of optional arguments with default values
            
        Returns:
            Validated arguments dict
            
        Raises:
            ValueError: If required arguments are missing
        """
        validated = {}
        
        # Check required arguments
        for arg_name in required_args:
            if arg_name not in arguments:
                raise ValueError(f"Missing required argument: {arg_name}")
            validated[arg_name] = arguments[arg_name]
        
        # Add optional arguments with defaults
        if optional_args:
            for arg_name, default_value in optional_args.items():
                validated[arg_name] = arguments.get(arg_name, default_value)
        
        return validated
