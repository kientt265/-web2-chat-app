"""
HTTP MCP Client for connecting to the MCP microservice.

This client communicates with the MCP service via HTTP REST API instead of
the standard MCP protocol, making it simpler for our microservice architecture.
"""

import logging
from typing import List, Dict, Any, Optional
import httpx
import os

logger = logging.getLogger(__name__)


class HTTPMCPClient:
    """HTTP-based MCP client for communicating with MCP microservice."""
    
    def __init__(self, mcp_service_url: str = None):
        """Initialize HTTP MCP client.
        
        Args:
            mcp_service_url: URL of the MCP service
        """
        self.mcp_service_url = mcp_service_url or os.getenv("MCP_SERVICE_URL", "http://mcp-service:3005")
        self.servers_cache: Dict[str, Dict[str, Any]] = {}
        self.tools_cache: Dict[str, List[Dict[str, Any]]] = {}
    
    async def get_servers(self) -> List[Dict[str, Any]]:
        """Get list of available MCP servers.
        
        Returns:
            List of server information
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.mcp_service_url}/servers")
                response.raise_for_status()
                
                servers = response.json()
                
                # Cache server info
                for server in servers:
                    self.servers_cache[server["name"]] = server
                
                logger.info(f"Retrieved {len(servers)} servers from MCP service")
                return servers
                
        except Exception as e:
            logger.error(f"Failed to get servers from MCP service: {e}")
            return []
    
    async def get_server_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """Get tools available from a specific server.
        
        Args:
            server_name: Name of the server
            
        Returns:
            List of tool definitions
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.mcp_service_url}/servers/{server_name}/tools")
                response.raise_for_status()
                
                result = response.json()
                tools = result.get("tools", [])
                
                # Cache tools
                self.tools_cache[server_name] = tools
                
                logger.debug(f"Retrieved {len(tools)} tools from server '{server_name}'")
                return tools
                
        except Exception as e:
            logger.error(f"Failed to get tools from server '{server_name}': {e}")
            return []
    
    async def call_tool(
        self, 
        server_name: str, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool on a specific server.
        
        Args:
            server_name: Name of the server
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.mcp_service_url}/servers/{server_name}/tools/{tool_name}",
                    json=arguments
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get("result", {})
                
        except Exception as e:
            logger.error(f"Failed to call tool '{tool_name}' on server '{server_name}': {e}")
            raise
    
    async def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all tools from all servers.
        
        Returns:
            List of all available tools
        """
        all_tools = []
        
        # Get all servers
        servers = await self.get_servers()
        
        # Get tools from each server
        for server in servers:
            server_name = server["name"]
            tools = await self.get_server_tools(server_name)
            
            # Add server context to each tool
            for tool in tools:
                tool_with_server = tool.copy()
                tool_with_server["server"] = server_name
                all_tools.append(tool_with_server)
        
        logger.info(f"Retrieved {len(all_tools)} total tools from MCP service")
        return all_tools
    
    async def check_health(self) -> bool:
        """Check if MCP service is healthy.
        
        Returns:
            True if service is healthy
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.mcp_service_url}/health")
                return response.status_code == 200
                
        except Exception as e:
            logger.warning(f"MCP service health check failed: {e}")
            return False


# Global HTTP MCP client instance
_http_mcp_client: Optional[HTTPMCPClient] = None


def get_http_mcp_client() -> HTTPMCPClient:
    """Get global HTTP MCP client instance.
    
    Returns:
        HTTP MCP client instance
    """
    global _http_mcp_client
    
    if _http_mcp_client is None:
        _http_mcp_client = HTTPMCPClient()
    
    return _http_mcp_client
