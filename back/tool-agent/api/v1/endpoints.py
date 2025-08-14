"""Agent API Service

This module defines the FastAPI router and endpoints for the Agent API Service.
"""

from fastapi import APIRouter
from core.agent_manager import agent_manager
from .schemas import (
    MessageRequest,
    MessageResponse,
    ToolsResponse,
    RefreshResponse,
    ToolInfo,
)

router = APIRouter()


@router.post("/process")
async def process_message(request: MessageRequest) -> MessageResponse:
    """Process user input and return the response."""
    response = agent_manager.process_message(request.session_id, request.user_input)
    return MessageResponse(response=response)


@router.get("/tools")
async def get_available_tools() -> ToolsResponse:
    """Get list of all available tools."""
    tools = agent_manager.get_available_tools()
    tool_info_list = [
        ToolInfo(name=tool["name"], description=tool["description"]) for tool in tools
    ]
    return ToolsResponse(tools=tool_info_list, total_count=len(tool_info_list))


@router.post("/tools/refresh")
async def refresh_tools() -> RefreshResponse:
    """Refresh tools from service registry."""
    await agent_manager.refresh_tools()
    tools = agent_manager.get_available_tools()
    return RefreshResponse(
        message="Tools refreshed successfully", tools_count=len(tools)
    )
