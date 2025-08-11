"""Service discovery client for discovering and calling external tool services.

This module provides a client for interacting with the service registry to discover
available tool services and dynamically load tools from remote services.
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
import httpx
from langchain.tools import Tool, StructuredTool
from langchain_core.pydantic_v1 import BaseModel, Field

logger = logging.getLogger(__name__)


class ToolInput(BaseModel):
    """Input schema for remote tools."""
    input: str = Field(description="Input data for the tool, can be JSON string or plain text")


class ServiceDiscoveryClient:
    """Client for discovering and calling external tool services."""
    
    def __init__(self, registry_url: str):
        """Initialize service discovery client.
        
        Args:
            registry_url: Base URL of the service registry
        """
        self.registry_url = registry_url
    
    async def discover_tool_services(self) -> List[Dict[str, Any]]:
        """Discover available tool services.
        
        Returns:
            List of tool service information
        """
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.post(
                    f"{self.registry_url}/api/v1/discover",
                    json={
                        "service_type": "tool",
                        "status": "healthy"
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                return data.get("services", [])
            
        except Exception as e:
            logger.error(f"Failed to discover tool services: {e}")
            return []
    
    async def get_service_tools(self, service_url: str) -> List[Dict[str, Any]]:
        """Get available tools from a service.
        
        Args:
            service_url: Base URL of the tool service
            
        Returns:
            List of tool definitions
        """
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(f"{service_url}/tools")
                response.raise_for_status()
                
                data = response.json()
                return data.get("tools", [])
            
        except Exception as e:
            logger.error(f"Failed to get tools from {service_url}: {e}")
            return []
    
    async def call_tool(
        self,
        service_url: str,
        tool_path: str,
        method: str = "POST",
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Call a tool on a remote service.
        
        Args:
            service_url: Base URL of the tool service
            tool_path: Tool endpoint path
            method: HTTP method
            data: Request data
            
        Returns:
            Tool response
        """
        try:
            url = f"{service_url}{tool_path}"
            
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=data)
                else:
                    response = await client.request(
                        method=method,
                        url=url,
                        json=data
                    )
                
                response.raise_for_status()
                return response.json()
            
        except Exception as e:
            logger.error(f"Failed to call tool {tool_path} on {service_url}: {e}")
            raise


class DynamicToolLoader:
    """Loads tools dynamically from discovered services."""
    
    def __init__(self, service_discovery: ServiceDiscoveryClient):
        """Initialize dynamic tool loader.
        
        Args:
            service_discovery: Service discovery client
        """
        self.service_discovery = service_discovery
        self.loaded_tools: Dict[str, Tool] = {}
    
    async def load_tools(self) -> List[Tool]:
        """Load all available tools from discovered services.
        
        Returns:
            List of LangChain tools
        """
        tools = []
        
        # Discover tool services
        services = await self.service_discovery.discover_tool_services()
        logger.info(f"Discovered {len(services)} tool services")
        
        for service in services:
            service_url = f"http://{service['host']}:{service['port']}"
            service_name = service['name']
            
            logger.info(f"Loading tools from service: {service_name}")
            
            # Get tools from this service
            try:
                service_tools = await self.service_discovery.get_service_tools(service_url)
                
                for tool_info in service_tools:
                    tool = self._create_tool(service_url, tool_info)
                    if tool:
                        tools.append(tool)
                        tool_key = f"{service_name}_{tool_info['name']}"
                        self.loaded_tools[tool_key] = tool
                        logger.debug(f"Loaded tool: {tool.name}")
                
            except Exception as e:
                logger.error(f"Failed to load tools from {service_name}: {e}")
        
        logger.info(f"Successfully loaded {len(tools)} tools")
        return tools
    
    def _create_tool(self, service_url: str, tool_info: Dict[str, Any]) -> Optional[Tool]:
        """Create a LangChain tool from service tool information.
        
        Args:
            service_url: Base URL of the service
            tool_info: Tool information from service
            
        Returns:
            LangChain Tool or None
        """
        try:
            tool_name = tool_info.get("name")
            tool_path = tool_info.get("path")
            tool_description = tool_info.get("description", f"Tool: {tool_name}")
            
            if not tool_name or not tool_path:
                logger.warning(f"Invalid tool info: {tool_info}")
                return None

            async def tool_func(input_data: str) -> str:
                """Tool function that calls the remote service."""
                try:
                    # Parse input if it's JSON
                    try:
                        data = json.loads(input_data)
                    except json.JSONDecodeError:
                        # If not JSON, send as text
                        data = {"input": input_data}
                    
                    result = await self.service_discovery.call_tool(
                        service_url=service_url,
                        tool_path=tool_path,
                        method="POST",
                        data=data
                    )
                    
                    # Return result as string
                    if isinstance(result, dict):
                        return json.dumps(result)
                    else:
                        return str(result)
                    
                except Exception as e:
                    error_msg = f"Error calling tool {tool_name}: {str(e)}"
                    logger.error(error_msg)
                    return error_msg

            # Create the structured tool with proper schema
            return StructuredTool.from_function(
                func=lambda input: asyncio.run(tool_func(input)),
                name=tool_name,
                description=tool_description,
                args_schema=ToolInput,
                coroutine=tool_func
            )
            
        except Exception as e:
            logger.error(f"Failed to create tool from {tool_info}: {e}")
            return None
    
    def get_loaded_tools(self) -> List[Tool]:
        """Get list of currently loaded tools.
        
        Returns:
            List of loaded tools
        """
        return list(self.loaded_tools.values())
    
    async def refresh_tools(self) -> List[Tool]:
        """Refresh the list of available tools.
        
        Returns:
            Updated list of tools
        """
        self.loaded_tools.clear()
        return await self.load_tools()


# Global instances
_service_discovery_client: Optional[ServiceDiscoveryClient] = None
_dynamic_tool_loader: Optional[DynamicToolLoader] = None


def get_service_discovery_client() -> ServiceDiscoveryClient:
    """Get the global service discovery client."""
    global _service_discovery_client
    
    if _service_discovery_client is None:
        registry_url = os.getenv("SERVICE_REGISTRY_URL", "http://service-registry:3003")
        _service_discovery_client = ServiceDiscoveryClient(registry_url)
    
    return _service_discovery_client


def get_dynamic_tool_loader() -> DynamicToolLoader:
    """Get the global dynamic tool loader."""
    global _dynamic_tool_loader
    
    if _dynamic_tool_loader is None:
        service_discovery = get_service_discovery_client()
        _dynamic_tool_loader = DynamicToolLoader(service_discovery)
    
    return _dynamic_tool_loader
