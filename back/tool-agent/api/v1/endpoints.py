"""Agent API Service

This module defines the FastAPI router and endpoints for the Agent API Service.
"""

from fastapi import APIRouter, HTTPException
from core.agent_manager import agent_manager
from services import get_http_mcp_client
from .schemas import (
    MessageRequest,
    MessageResponse,
    ToolsResponse,
    RefreshResponse,
    ToolInfo,
    MCPStatusResponse,
    MCPServerStatus,
)

router = APIRouter()


@router.post("/process")
async def process_message(request: MessageRequest) -> MessageResponse:
    """Process user input and return the response."""
    response = await agent_manager.process_message(
        request.session_id, request.user_input
    )
    return MessageResponse(response=response)


@router.get("/tools", response_model=ToolsResponse)
async def get_tools():
    """Get all available tools"""
    try:
        http_mcp_client = get_http_mcp_client()
        tools = await http_mcp_client.get_all_tools()

        tool_infos = []
        for tool in tools:
            tool_info = ToolInfo(
                name=tool.get("name", "unknown"),
                description=tool.get("description", "No description available"),
                # Add more fields as needed
            )
            tool_infos.append(tool_info)

        return ToolsResponse(tools=tool_infos, total=len(tool_infos))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tools: {str(e)}")


@router.post("/tools/refresh", response_model=RefreshResponse)
async def refresh_tools():
    """Refresh the agent's tools"""
    try:
        # Refresh tools in agent manager
        await agent_manager.refresh_tools()

        return RefreshResponse(
            success=True, message="Successfully refreshed tools"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to refresh tools: {str(e)}"
        )


@router.get("/mcp/status", response_model=MCPStatusResponse)
async def get_mcp_status():
    """Get MCP server status"""
    try:
        http_mcp_client = get_http_mcp_client()
        servers = await http_mcp_client.get_servers()

        server_statuses = []
        for server in servers:
            status = MCPServerStatus(
                name=server.get("name", "unknown"),
                status="connected" if server.get("running", False) else "disconnected",
                tools_count=server.get("tool_count", 0),
            )
            server_statuses.append(status)

        return MCPStatusResponse(
            servers=server_statuses, total_servers=len(server_statuses)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get MCP status: {str(e)}"
        )
