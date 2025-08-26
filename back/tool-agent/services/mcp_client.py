"""
Model Context Protocol (MCP) Client for Tool Agent

This module provides MCP client functionality to connect to MCP servers
and load tools through the Model Context Protocol standard.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Union
from langchain.tools import Tool, StructuredTool
from pydantic import BaseModel, Field, model_validator
import httpx

logger = logging.getLogger(__name__)


class MCPToolInput(BaseModel):
    """Input schema for MCP tools."""

    arguments: Dict[str, Any] = Field(
        description="Arguments for the MCP tool", default_factory=dict
    )


class MCPMessage(BaseModel):
    """MCP message structure."""

    id: Union[int, str]
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class MCPServerConfig(BaseModel):
    """Configuration for MCP server connection."""

    name: str
    command: Optional[List[str]] = None  # Optional for HTTP-based servers
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    url: Optional[str] = None  # For HTTP-based MCP servers

    @model_validator(mode="after")
    def validate_command_or_url(self):
        """Validate that either command or url is provided."""
        if not self.command and not self.url:
            raise ValueError(
                "Either 'command' or 'url' must be provided for MCP server configuration"
            )
        return self


class MCPClient:
    """Client for connecting to MCP servers and loading tools."""

    def __init__(self, server_config: MCPServerConfig):
        """Initialize MCP client.

        Args:
            server_config: Configuration for MCP server connection
        """
        self.server_config = server_config
        self.tools_cache: Dict[str, Dict[str, Any]] = {}
        self._message_id = 0

    def _next_message_id(self) -> int:
        """Get next message ID."""
        self._message_id += 1
        return self._message_id

    async def _send_mcp_request(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send MCP request to server.

        Args:
            method: MCP method name
            params: Method parameters

        Returns:
            MCP response result
        """
        if self.server_config.url:
            # HTTP-based MCP server
            return await self._send_http_request(method, params)
        else:
            # Process-based MCP server (stdio)
            return await self._send_stdio_request(method, params)

    async def _send_http_request(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send HTTP request to MCP server.

        Args:
            method: MCP method name
            params: Method parameters

        Returns:
            Response result
        """
        try:
            message = {
                "jsonrpc": "2.0",
                "id": self._next_message_id(),
                "method": method,
                "params": params or {},
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.server_config.url,
                    json=message,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()

                result = response.json()
                if "error" in result:
                    raise Exception(f"MCP error: {result['error']}")

                return result.get("result", {})

        except Exception as e:
            logger.error(f"HTTP MCP request failed: {e}")
            raise

    async def _send_stdio_request(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send request to process-based MCP server via stdio.

        Args:
            method: MCP method name
            params: Method parameters

        Returns:
            Response result
        """
        try:
            # Create message
            message = {
                "jsonrpc": "2.0",
                "id": self._next_message_id(),
                "method": method,
                "params": params or {},
            }

            # Start MCP server process
            cmd = self.server_config.command
            if self.server_config.args:
                cmd.extend(self.server_config.args)

            env = self.server_config.env or {}

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**env},
            )

            # Send message
            message_json = json.dumps(message) + "\n"
            process.stdin.write(message_json.encode())
            await process.stdin.drain()
            process.stdin.close()

            # Read response
            stdout, stderr = await process.communicate()

            if stderr:
                logger.warning(f"MCP server stderr: {stderr.decode()}")

            if process.returncode != 0:
                raise Exception(f"MCP server exited with code {process.returncode}")

            # Parse response
            response_text = stdout.decode().strip()
            if not response_text:
                raise Exception("Empty response from MCP server")

            result = json.loads(response_text)
            if "error" in result:
                raise Exception(f"MCP error: {result['error']}")

            return result.get("result", {})

        except Exception as e:
            logger.error(f"Stdio MCP request failed: {e}")
            raise

    async def initialize(self) -> bool:
        """Initialize connection to MCP server.

        Returns:
            True if initialization successful
        """
        try:
            # Send initialize request
            result = await self._send_mcp_request(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "tool-agent-mcp-client", "version": "1.0.0"},
                },
            )

            logger.info(f"MCP server initialized: {result}")

            # Send initialized notification
            await self._send_mcp_request("notifications/initialized")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize MCP server: {e}")
            return False

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from MCP server.

        Returns:
            List of tool definitions
        """
        try:
            result = await self._send_mcp_request("tools/list")
            tools = result.get("tools", [])

            # Cache tools for later use
            for tool in tools:
                self.tools_cache[tool["name"]] = tool

            logger.info(
                f"Listed {len(tools)} tools from MCP server {self.server_config.name}"
            )
            return tools

        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool on the MCP server.

        Args:
            tool_name: Name of tool to call
            arguments: Tool arguments

        Returns:
            Tool result
        """
        try:
            result = await self._send_mcp_request(
                "tools/call", {"name": tool_name, "arguments": arguments}
            )

            return result

        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            raise


class MCPToolLoader:
    """Loads tools from MCP servers and converts them to LangChain tools."""

    def __init__(self, mcp_servers: List[MCPServerConfig]):
        """Initialize MCP tool loader.

        Args:
            mcp_servers: List of MCP server configurations
        """
        self.mcp_servers = mcp_servers
        self.clients: Dict[str, MCPClient] = {}
        self.loaded_tools: Dict[str, Tool] = {}

    async def initialize_clients(self) -> None:
        """Initialize all MCP clients."""
        for server_config in self.mcp_servers:
            try:
                client = MCPClient(server_config)
                success = await client.initialize()

                if success:
                    self.clients[server_config.name] = client
                    logger.info(f"Initialized MCP client for {server_config.name}")
                else:
                    logger.error(
                        f"Failed to initialize MCP client for {server_config.name}"
                    )

            except Exception as e:
                logger.error(f"Error initializing MCP client {server_config.name}: {e}")

    async def load_tools(self) -> List[Tool]:
        """Load all tools from all MCP servers.

        Returns:
            List of LangChain tools
        """
        tools = []

        # Initialize clients if not done already
        if not self.clients:
            await self.initialize_clients()

        # Load tools from each client
        for server_name, client in self.clients.items():
            try:
                mcp_tools = await client.list_tools()

                for mcp_tool in mcp_tools:
                    langchain_tool = self._create_langchain_tool(client, mcp_tool)
                    if langchain_tool:
                        tools.append(langchain_tool)
                        tool_key = f"mcp_{server_name}_{mcp_tool['name']}"
                        self.loaded_tools[tool_key] = langchain_tool
                        logger.debug(f"Loaded MCP tool: {mcp_tool['name']}")

            except Exception as e:
                logger.error(f"Failed to load tools from MCP server {server_name}: {e}")

        logger.info(f"Loaded {len(tools)} tools from {len(self.clients)} MCP servers")
        return tools

    def _create_langchain_tool(
        self, client: MCPClient, mcp_tool: Dict[str, Any]
    ) -> Optional[Tool]:
        """Create LangChain tool from MCP tool definition.

        Args:
            client: MCP client instance
            mcp_tool: MCP tool definition

        Returns:
            LangChain Tool or None
        """
        try:
            tool_name = mcp_tool.get("name")
            tool_description = mcp_tool.get("description", f"MCP tool: {tool_name}")

            if not tool_name:
                logger.warning(f"Invalid MCP tool definition: {mcp_tool}")
                return None

            async def tool_func(arguments: Dict[str, Any]) -> str:
                """Tool function that calls MCP server."""
                try:
                    result = await client.call_tool(tool_name, arguments)

                    # Format result as string
                    if isinstance(result, dict):
                        # Check for content in MCP response format
                        if "content" in result:
                            content = result["content"]
                            if isinstance(content, list) and content:
                                # Handle content array (MCP standard format)
                                text_parts = []
                                for item in content:
                                    if (
                                        isinstance(item, dict)
                                        and item.get("type") == "text"
                                    ):
                                        text_parts.append(item.get("text", ""))
                                return (
                                    "\n".join(text_parts) if text_parts else str(result)
                                )
                            else:
                                return str(content)
                        else:
                            return json.dumps(result, indent=2)
                    else:
                        return str(result)

                except Exception as e:
                    error_msg = f"Error calling MCP tool {tool_name}: {str(e)}"
                    logger.error(error_msg)
                    return error_msg

            # Create structured tool
            return StructuredTool.from_function(
                func=lambda arguments: asyncio.run(tool_func(arguments)),
                name=tool_name,
                description=tool_description,
                args_schema=MCPToolInput,
                coroutine=tool_func,
            )

        except Exception as e:
            logger.error(
                f"Failed to create LangChain tool from MCP tool {mcp_tool}: {e}"
            )
            return None

    async def refresh_tools(self) -> List[Tool]:
        """Refresh tools from all MCP servers.

        Returns:
            Updated list of tools
        """
        self.loaded_tools.clear()
        return await self.load_tools()

    def get_loaded_tools(self) -> List[Tool]:
        """Get list of currently loaded tools.

        Returns:
            List of loaded tools
        """
        return list(self.loaded_tools.values())


# Global MCP tool loader instance
_mcp_tool_loader: Optional[MCPToolLoader] = None


def get_mcp_servers_config() -> List[MCPServerConfig]:
    """Get MCP server configurations from configuration system.

    Returns:
        List of MCP server configurations
    """
    try:
        from core.config import get_config

        config = get_config()
        return config.get_mcp_servers()
    except ImportError:
        logger.warning("Configuration system not available, using default MCP configs")

        # Fallback to default configurations
        default_configs = [
            MCPServerConfig(
                name="filesystem",
                command=["npx", "@modelcontextprotocol/server-filesystem"],
                args=["/tmp"],
            ),
            MCPServerConfig(
                name="git",
                command=["npx", "@modelcontextprotocol/server-git"],
                args=["--repository", "."],
            ),
        ]

        return default_configs


def get_mcp_tool_loader() -> MCPToolLoader:
    """Get global MCP tool loader instance.

    Returns:
        MCP tool loader instance
    """
    global _mcp_tool_loader

    if _mcp_tool_loader is None:
        mcp_servers = get_mcp_servers_config()
        _mcp_tool_loader = MCPToolLoader(mcp_servers)

    return _mcp_tool_loader
