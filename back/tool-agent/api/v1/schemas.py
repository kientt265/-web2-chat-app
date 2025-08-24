"""
Schemas for the Agent API Service
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class MessageRequest(BaseModel):
    """Request schema for processing a message."""

    session_id: str
    user_input: str


class MessageResponse(BaseModel):
    """Response schema for returning the processed message."""

    response: str


class ToolInfo(BaseModel):
    """Tool information schema."""

    name: str
    description: str


class ToolsResponse(BaseModel):
    """Response schema for listing available tools."""

    tools: List[ToolInfo]
    total: int


class RefreshResponse(BaseModel):
    """Response schema for tool refresh operation."""

    success: bool
    message: str


class MCPServerStatus(BaseModel):
    """Status of an MCP server."""
    
    name: str
    status: str
    tools_count: int


class MCPStatusResponse(BaseModel):
    """Response schema for MCP server status."""
    
    servers: List[MCPServerStatus]
    total_servers: int
