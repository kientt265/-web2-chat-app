"""
MCP Service - A dedicated microservice for hosting MCP (Model Context Protocol) servers.

This service provides standardized tool interfaces through MCP protocol,
allowing other services to connect and use tools like calculator and web scraper.
"""

import logging
import uvicorn
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any

from config import get_config
from core.mcp_manager import MCPManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global MCP manager instance
mcp_manager: MCPManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    global mcp_manager
    
    # Startup
    logger.info("Starting MCP Service")
    config = get_config()
    mcp_manager = MCPManager(config)
    
    # Start all MCP servers
    await mcp_manager.start_all_servers()
    
    yield
    
    # Shutdown
    logger.info("Shutting down MCP Service")
    if mcp_manager:
        await mcp_manager.stop_all_servers()


# Create FastAPI application
app = FastAPI(
    title="MCP Service",
    description="Model Context Protocol servers for tool integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "MCP Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    global mcp_manager
    
    # Get server status from MCP manager
    server_status = {}
    if mcp_manager:
        server_status = await mcp_manager.get_server_status()
    
    return {
        "status": "healthy",
        "servers": server_status
    }


@app.get("/servers")
async def list_servers():
    """List all available MCP servers."""
    global mcp_manager
    
    if not mcp_manager:
        return []
    
    return await mcp_manager.get_server_info()


@app.get("/servers/{server_name}/tools")
async def list_server_tools(server_name: str):
    """List tools available from a specific server."""
    global mcp_manager
    
    if not mcp_manager:
        raise HTTPException(status_code=503, detail="MCP manager not available")
    
    try:
        tools = await mcp_manager.list_server_tools(server_name)
        return {"server": server_name, "tools": tools}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/servers/{server_name}/tools/{tool_name}")
async def call_tool(server_name: str, tool_name: str, arguments: Dict[str, Any] = None):
    """Call a tool on a specific server."""
    global mcp_manager
    
    if not mcp_manager:
        raise HTTPException(status_code=503, detail="MCP manager not available")
    
    if arguments is None:
        arguments = {}
    
    try:
        result = await mcp_manager.call_tool(server_name, tool_name, arguments)
        return {"result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/servers/restart")
async def restart_servers():
    """Restart all MCP servers."""
    global mcp_manager
    
    if not mcp_manager:
        raise HTTPException(status_code=503, detail="MCP manager not available")
    
    try:
        await mcp_manager.restart_all_servers()
        return {"message": "All MCP servers restarted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restart servers: {str(e)}")


if __name__ == "__main__":
    # Get configuration
    config = get_config()
    
    # Run the application
    uvicorn.run(
        "main:app",
        host=config.get_setting("host", "0.0.0.0"),
        port=config.get_setting("port", 3005),
        reload=config.get_setting("debug", False),
        log_level="info"
    )
