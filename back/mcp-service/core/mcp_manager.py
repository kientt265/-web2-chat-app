"""
MCP Manager - Manages multiple MCP servers within the service.
"""

import asyncio
import logging
import importlib
from typing import Dict, List, Any, Optional
import httpx

# Import server classes
from servers.calculator import CalculatorServer  
from servers.webscraper import WebscraperServer

logger = logging.getLogger(__name__)


class MCPServerProcess:
    """Represents a running MCP server process."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize MCP server process.
        
        Args:
            name: Server name
            config: Server configuration
        """
        self.name = name
        self.config = config
        self.server_instance = None
        self.is_running = False
        self.port = config.get("port", 8000)
        
        # Create server instance based on name
        self._create_server_instance()
    
    def _create_server_instance(self):
        """Create the appropriate server instance."""
        if self.name == "calculator":
            self.server_instance = CalculatorServer(self.config)
        elif self.name == "webscraper":
            self.server_instance = WebscraperServer(self.config)
        else:
            raise ValueError(f"Unknown server type: {self.name}")
    
    async def start(self):
        """Start the MCP server."""
        try:
            if self.server_instance is None:
                raise ValueError(f"No server instance for '{self.name}'")
            
            # Since we're using the layered architecture, the server
            # doesn't need to actually run as a separate process
            # The tools are available through the API handler
            self.is_running = True
            logger.info(f"Started MCP server '{self.name}' with layered architecture")
            
        except Exception as e:
            logger.error(f"Failed to start MCP server '{self.name}': {e}")
            raise
    
    async def stop(self):
        """Stop the MCP server."""
        try:
            if self.server_instance:
                await self.server_instance.stop()
            
            self.is_running = False
            logger.info(f"Stopped MCP server '{self.name}'")
            
        except Exception as e:
            logger.error(f"Failed to stop MCP server '{self.name}': {e}")
    
    async def get_tools(self) -> List[Dict[str, Any]]:
        """Get available tools from the server.
        
        Returns:
            List of tool definitions
        """
        if not self.is_running or not self.server_instance:
            return []
        
        try:
            tool_definitions = self.server_instance.get_tool_definitions()
            return [
                {
                    "name": tool_name,
                    "description": tool_def.get("description", ""),
                    "parameters": tool_def.get("parameters", {}),
                    "server": self.name
                }
                for tool_name, tool_def in tool_definitions.items()
            ]
                
        except Exception as e:
            logger.error(f"Failed to get tools from server '{self.name}': {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on this server.
        
        Args:
            tool_name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        if not self.is_running or not self.server_instance:
            raise ValueError(f"Server '{self.name}' is not running")
        
        try:
            result = await self.server_instance.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            logger.error(f"Failed to call tool '{tool_name}' on server '{self.name}': {e}")
            raise


class MCPManager:
    """Manages multiple MCP servers."""
    
    def __init__(self, config):
        """Initialize MCP manager.
        
        Args:
            config: Configuration instance
        """
        self.config = config
        self.servers: Dict[str, MCPServerProcess] = {}
    
    async def start_all_servers(self):
        """Start all configured MCP servers."""
        server_configs = self.config.get_mcp_servers()
        
        for server_config in server_configs:
            server_name = server_config["name"]
            
            try:
                server_process = MCPServerProcess(server_name, server_config)
                await server_process.start()
                self.servers[server_name] = server_process
                
            except Exception as e:
                logger.error(f"Failed to start server '{server_name}': {e}")
        
        logger.info(f"Started {len(self.servers)} MCP servers")
    
    async def stop_all_servers(self):
        """Stop all MCP servers."""
        for server_name, server_process in self.servers.items():
            try:
                await server_process.stop()
            except Exception as e:
                logger.error(f"Failed to stop server '{server_name}': {e}")
        
        self.servers.clear()
        logger.info("Stopped all MCP servers")
    
    async def restart_all_servers(self):
        """Restart all MCP servers."""
        await self.stop_all_servers()
        await self.start_all_servers()
    
    async def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all servers.
        
        Returns:
            Dict mapping server names to their status
        """
        status = {}
        
        for server_name, server_process in self.servers.items():
            status[server_name] = {
                "running": server_process.is_running,
                "port": server_process.port,
                "type": server_process.config.get("type", "unknown")
            }
        
        return status
    
    async def get_server_info(self) -> List[Dict[str, Any]]:
        """Get information about all servers.
        
        Returns:
            List of server information
        """
        server_info = []
        
        for server_name, server_process in self.servers.items():
            tools = await server_process.get_tools()
            
            server_info.append({
                "name": server_name,
                "running": server_process.is_running,
                "port": server_process.port,
                "type": server_process.config.get("type", "unknown"),
                "tools": [tool["name"] for tool in tools],
                "tool_count": len(tools)
            })
        
        return server_info
    
    async def list_server_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """List tools for a specific server.
        
        Args:
            server_name: Name of the server
            
        Returns:
            List of tool definitions
            
        Raises:
            ValueError: If server not found
        """
        if server_name not in self.servers:
            raise ValueError(f"Server '{server_name}' not found")
        
        server_process = self.servers[server_name]
        return await server_process.get_tools()
    
    async def call_tool(
        self, 
        server_name: str, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Any:
        """Call a tool on a specific server.
        
        Args:
            server_name: Name of the server
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            Tool result
            
        Raises:
            ValueError: If server or tool not found
        """
        if server_name not in self.servers:
            raise ValueError(f"Server '{server_name}' not found")
        
        server_process = self.servers[server_name]
        
        if not server_process.is_running:
            raise ValueError(f"Server '{server_name}' is not running")
        
        # Call tool through the server process
        return await server_process.call_tool(tool_name, arguments)
