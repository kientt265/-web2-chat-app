"""
MCP Manager - Manages multiple MCP servers within the service.
"""

import asyncio
import logging
import importlib
from typing import Dict, List, Any, Optional
import httpx

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
        self.process: Optional[asyncio.subprocess.Process] = None
        self.server_instance = None
        self.is_running = False
        self.port = config.get("port", 8000)
    
    async def start(self):
        """Start the MCP server."""
        try:
            if self.config.get("type") == "fastmcp":
                # Start FastMCP server
                await self._start_fastmcp_server()
            else:
                # Start process-based server
                await self._start_process_server()
            
            self.is_running = True
            logger.info(f"Started MCP server '{self.name}' on port {self.port}")
            
        except Exception as e:
            logger.error(f"Failed to start MCP server '{self.name}': {e}")
            raise
    
    async def _start_fastmcp_server(self):
        """Start FastMCP server as a background task."""
        try:
            # Import the server module
            module_name = self.config.get("module")
            if not module_name:
                raise ValueError(f"No module specified for FastMCP server '{self.name}'")
            
            # Dynamically import the server module
            module = importlib.import_module(module_name)
            
            # Get the FastMCP app instance
            if hasattr(module, 'app'):
                self.server_instance = module.app
            else:
                raise ValueError(f"FastMCP server module '{module_name}' must have 'app' attribute")
            
            # Start the server in a background task using asyncio.create_task
            # We'll create a simple HTTP server using the app instance
            import uvicorn
            
            # Create a background task to run the server
            config = uvicorn.Config(
                app=self.server_instance,
                host="0.0.0.0", 
                port=self.port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            
            # Start server in background task
            asyncio.create_task(server.serve())
            
            # Give it a moment to start
            await asyncio.sleep(1.0)
            
            logger.info(f"FastMCP server '{self.name}' started on port {self.port}")
            
        except Exception as e:
            logger.error(f"Failed to start FastMCP server '{self.name}': {e}")
            raise
    
    async def _start_process_server(self):
        """Start process-based MCP server."""
        try:
            command = self.config.get("command", [])
            if not command:
                raise ValueError(f"No command specified for process server '{self.name}'")
            
            args = self.config.get("args", [])
            env = self.config.get("env", {})
            
            full_command = command + args
            
            # Start the process
            self.process = await asyncio.create_subprocess_exec(
                *full_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            logger.info(f"Process MCP server '{self.name}' started with PID {self.process.pid}")
            
        except Exception as e:
            logger.error(f"Failed to start process server '{self.name}': {e}")
            raise
    
    async def _health_check(self):
        """Check if the server is responding."""
        try:
            async with httpx.AsyncClient() as client:
                # Try to connect to the server
                response = await client.get(
                    f"http://localhost:{self.port}/health",
                    timeout=5.0
                )
                if response.status_code != 200:
                    raise Exception(f"Server health check failed: {response.status_code}")
                    
        except Exception as e:
            logger.warning(f"Health check failed for server '{self.name}': {e}")
            # Don't raise - server might not have health endpoint
    
    async def stop(self):
        """Stop the MCP server."""
        try:
            if self.process:
                # Stop process-based server
                self.process.terminate()
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    self.process.kill()
                    await self.process.wait()
                
                self.process = None
            
            # For FastMCP servers, we can't easily stop them since they're running
            # in background tasks. They'll be stopped when the main process exits.
            
            self.is_running = False
            logger.info(f"Stopped MCP server '{self.name}'")
            
        except Exception as e:
            logger.error(f"Failed to stop MCP server '{self.name}': {e}")
    
    async def get_tools(self) -> List[Dict[str, Any]]:
        """Get available tools from the server.
        
        Returns:
            List of tool definitions
        """
        if not self.is_running:
            return []
        
        try:
            if self.config.get("type") == "fastmcp":
                # For FastMCP servers, return configured tools
                return [
                    {"name": tool, "server": self.name}
                    for tool in self.config.get("tools", [])
                ]
            else:
                # For process servers, we'd need to query via MCP protocol
                # This is a simplified implementation
                return []
                
        except Exception as e:
            logger.error(f"Failed to get tools from server '{self.name}': {e}")
            return []


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
        
        if server_process.config.get("type") == "fastmcp":
            # For FastMCP servers, call via HTTP
            return await self._call_fastmcp_tool(server_process, tool_name, arguments)
        else:
            # For process servers, call via MCP protocol
            return await self._call_process_tool(server_process, tool_name, arguments)
    
    async def _call_fastmcp_tool(
        self, 
        server_process: MCPServerProcess, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Any:
        """Call tool on FastMCP server via HTTP.
        
        Args:
            server_process: Server process instance
            tool_name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        try:
            async with httpx.AsyncClient() as client:
                # Call the tool endpoint
                response = await client.post(
                    f"http://localhost:{server_process.port}/tools/{tool_name}",
                    json=arguments,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"Tool call failed: {response.status_code} - {response.text}")
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to call FastMCP tool '{tool_name}': {e}")
            raise
    
    async def _call_process_tool(
        self, 
        server_process: MCPServerProcess, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Any:
        """Call tool on process server via MCP protocol.
        
        Args:
            server_process: Server process instance
            tool_name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        # This would implement the MCP protocol communication
        # For now, return a placeholder
        raise NotImplementedError("Process-based MCP tool calling not implemented yet")
