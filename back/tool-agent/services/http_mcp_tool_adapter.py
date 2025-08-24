"""
HTTP MCP Tool Adapter

Converts HTTP MCP responses to LangChain tools for the agent manager.
"""

import asyncio
import logging
from typing import List, Dict, Any, Type
from langchain.tools import Tool, StructuredTool
from pydantic import BaseModel, Field, create_model

from .http_mcp_client import HTTPMCPClient

logger = logging.getLogger(__name__)


class HTTPMCPToolAdapter:
    """Adapts HTTP MCP tools to LangChain tools."""
    
    def __init__(self, http_client: HTTPMCPClient):
        """Initialize tool adapter.
        
        Args:
            http_client: HTTP MCP client instance
        """
        self.http_client = http_client
        self.tools_cache: List[Tool] = []
    
    async def load_tools(self) -> List[Tool]:
        """Load all tools from HTTP MCP service and convert to LangChain tools.
        
        Returns:
            List of LangChain tools
        """
        try:
            # Get all tools from MCP service
            mcp_tools = await self.http_client.get_all_tools()
            
            langchain_tools = []
            
            for mcp_tool in mcp_tools:
                langchain_tool = self._create_langchain_tool(mcp_tool)
                if langchain_tool:
                    langchain_tools.append(langchain_tool)
            
            self.tools_cache = langchain_tools
            logger.info(f"Loaded {len(langchain_tools)} tools from HTTP MCP service")
            return langchain_tools
            
        except Exception as e:
            logger.error(f"Failed to load tools from HTTP MCP service: {e}")
            return []
    
    def _get_tool_input_schema(self, tool_name: str, server_name: str) -> Type[BaseModel]:
        """Create input schema for a specific tool.
        
        Args:
            tool_name: Name of the tool
            server_name: Name of the server
            
        Returns:
            Pydantic model class for tool input
        """
        # Create tool-specific input schemas
        if server_name == "calculator":
            if tool_name == "calculate":
                return create_model(
                    f"{server_name}_{tool_name}_Input",
                    expression=(str, Field(description="Mathematical expression to evaluate"))
                )
            elif tool_name == "calculate_statistics":
                return create_model(
                    f"{server_name}_{tool_name}_Input",
                    data=(str, Field(description="Comma-separated list of numbers"))
                )
            elif tool_name == "convert_units":
                return create_model(
                    f"{server_name}_{tool_name}_Input",
                    value=(float, Field(description="Value to convert")),
                    from_unit=(str, Field(description="Source unit")),
                    to_unit=(str, Field(description="Target unit"))
                )
            elif tool_name == "list_math_functions":
                return create_model(f"{server_name}_{tool_name}_Input")
        
        elif server_name == "webscraper":
            if tool_name == "scrape_webpage":
                return create_model(
                    f"{server_name}_{tool_name}_Input",
                    url=(str, Field(description="URL to scrape")),
                    selector=(str, Field(description="CSS selector", default=""))
                )
            elif tool_name == "extract_text":
                return create_model(
                    f"{server_name}_{tool_name}_Input",
                    url=(str, Field(description="URL to extract text from"))
                )
        
        # Default fallback
        return create_model(
            f"{server_name}_{tool_name}_Input",
            arguments=(Dict[str, Any], Field(description="Tool arguments", default_factory=dict))
        )
    
    def _create_langchain_tool(self, mcp_tool: Dict[str, Any]) -> Tool:
        """Create LangChain tool from HTTP MCP tool definition.
        
        Args:
            mcp_tool: HTTP MCP tool definition
            
        Returns:
            LangChain Tool or None
        """
        try:
            tool_name = mcp_tool.get("name")
            server_name = mcp_tool.get("server")
            tool_description = mcp_tool.get("description", f"Tool '{tool_name}' from server '{server_name}'")
            
            if not tool_name or not server_name:
                logger.warning(f"Invalid HTTP MCP tool definition: {mcp_tool}")
                return None
            
            # Get appropriate input schema
            input_schema = self._get_tool_input_schema(tool_name, server_name)
            
            def tool_func(**kwargs) -> str:
                """Tool function that calls HTTP MCP service."""
                try:
                    # Create an event loop if not running in one
                    try:
                        loop = asyncio.get_running_loop()
                        # If we're in an event loop, we need to create a task
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, self._async_tool_call(server_name, tool_name, kwargs))
                            result = future.result()
                    except RuntimeError:
                        # No event loop running, we can use asyncio.run directly
                        result = asyncio.run(self._async_tool_call(server_name, tool_name, kwargs))
                    
                    return result
                        
                except Exception as e:
                    error_msg = f"Error calling HTTP MCP tool {tool_name}: {str(e)}"
                    logger.error(error_msg)
                    return error_msg
            
            # Create structured tool
            return StructuredTool.from_function(
                func=tool_func,
                name=f"{server_name}_{tool_name}",
                description=tool_description,
                args_schema=input_schema,
            )
            
        except Exception as e:
            logger.error(f"Failed to create LangChain tool from HTTP MCP tool {mcp_tool}: {e}")
            return None
    
    async def _async_tool_call(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Async tool call wrapper."""
        try:
            result = await self.http_client.call_tool(server_name, tool_name, arguments)
            
            # Format result as string
            if isinstance(result, dict):
                if "error" in result and result["error"]:
                    return f"Error: {result['error']}"
                elif "result" in result:
                    nested_result = result["result"]
                    if isinstance(nested_result, dict):
                        # Handle nested result structure (like calculator returns)
                        if "success" in nested_result and not nested_result["success"]:
                            return f"Error: {nested_result.get('error', 'Unknown error')}"
                        elif "result" in nested_result:
                            return f"Result: {nested_result['result']}"
                        else:
                            return str(nested_result)
                    else:
                        return str(nested_result)
                elif "content" in result:
                    return str(result["content"])
                else:
                    return str(result)
            else:
                return str(result)
                
        except Exception as e:
            error_msg = f"Error calling HTTP MCP tool {tool_name}: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def get_cached_tools(self) -> List[Tool]:
        """Get cached tools.
        
        Returns:
            List of cached tools
        """
        return self.tools_cache.copy()
    
    async def refresh_tools(self) -> List[Tool]:
        """Refresh tools from HTTP MCP service.
        
        Returns:
            Updated list of tools
        """
        self.tools_cache.clear()
        return await self.load_tools()
