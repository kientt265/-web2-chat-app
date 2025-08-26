"""
MCP Service - A dedicated microservice for hosting MCP (Model Context Protocol) servers.

This service provides standardized tool interfaces through MCP protocol,
allowing other services to connect and use tools like calculator and web scraper.
"""

import asyncio
import logging
import uvicorn
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any

from config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    
    # Startup
    logger.info("Starting MCP Service")
    yield
    
    # Shutdown
    logger.info("Shutting down MCP Service")


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
    config = get_config()
    
    # Simple health check - just verify we can reach ext-tool
    try:
        ext_tool_url = config.get_setting("ext_tool_service_url")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ext_tool_url}/health")
            ext_tool_healthy = response.status_code == 200
    except:
        ext_tool_healthy = False
    
    return {
        "status": "healthy",
        "ext_tool_status": "healthy" if ext_tool_healthy else "unhealthy",
        "servers": {
            "calculator": {"running": True, "port": 8001, "type": "proxy"},
            "webscraper": {"running": True, "port": 8002, "type": "proxy"}
        }
    }


@app.get("/servers")
async def list_servers():
    """List all available MCP servers."""
    return [
        {
            "name": "calculator",
            "running": True,
            "port": 8001,
            "type": "proxy",
            "tools": ["calculate", "calculate_statistics", "convert_units", "list_math_functions"],
            "tool_count": 4
        },
        {
            "name": "webscraper",
            "running": True,
            "port": 8002,
            "type": "proxy", 
            "tools": ["scrape_webpage", "extract_text"],
            "tool_count": 2
        }
    ]


@app.get("/servers/{server_name}/tools")
async def list_server_tools(server_name: str):
    """List tools available from a specific server."""
    tools_mapping = {
        "calculator": [
            {"name": "calculate", "description": "Perform mathematical calculations"},
            {"name": "calculate_statistics", "description": "Calculate statistical measures"},
            {"name": "convert_units", "description": "Convert between units"},
            {"name": "list_math_functions", "description": "List available math functions"}
        ],
        "webscraper": [
            {"name": "scrape_webpage", "description": "Scrape content from webpage"},
            {"name": "extract_text", "description": "Extract text from webpage"}
        ]
    }
    
    if server_name not in tools_mapping:
        raise HTTPException(status_code=404, detail=f"Server '{server_name}' not found")
    
    return {"server": server_name, "tools": tools_mapping[server_name]}


@app.post("/servers/{server_name}/tools/{tool_name}")
async def call_tool(server_name: str, tool_name: str, arguments: Dict[str, Any] = None):
    """Call a tool on a specific server."""
    if arguments is None:
        arguments = {}
    
    try:
        # For now, directly proxy to ext-tool service
        config = get_config()
        ext_tool_url = config.get_setting("ext_tool_service_url")
        
        # Map server and tool names to ext-tool endpoints
        tool_mapping = {
            "calculator": {
                "calculate": "/tools/calculator/calculate",
                "calculate_statistics": "/tools/calculator/statistics", 
                "convert_units": "/tools/calculator/convert",
                "list_math_functions": "/tools/calculator/functions"
            },
            "webscraper": {
                "scrape_webpage": "/tools/scraper/scrape",
                "extract_text": "/tools/scraper/extract-text"
            }
        }
        
        if server_name not in tool_mapping:
            raise HTTPException(status_code=404, detail=f"Server '{server_name}' not found")
        
        if tool_name not in tool_mapping[server_name]:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found on server '{server_name}'")
        
        endpoint = tool_mapping[server_name][tool_name]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Make request to ext-tool service
            # Different tools use different HTTP methods
            if server_name == "calculator" or (server_name == "webscraper" and tool_name == "scrape_webpage"):
                # POST request for calculator tools and scrape_webpage
                response = await client.post(f"{ext_tool_url}{endpoint}", json=arguments)
            else:
                # GET request for other tools like extract_text
                response = await client.get(f"{ext_tool_url}{endpoint}", params=arguments)
            
            response.raise_for_status()
            result = response.json()
            
            return {"result": result}
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to ext-tool service: {str(e)}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Tool execution failed: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/servers/restart")
async def restart_servers():
    """Restart all MCP servers."""
    # Since we're just proxying, there's nothing to restart
    return {"message": "All proxy servers are always running"}


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
