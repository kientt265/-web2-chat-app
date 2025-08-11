"""
Schemas for the Agent API Service
"""

from typing import List, Dict, Any
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
    total_count: int


class RefreshResponse(BaseModel):
    """Response schema for tool refresh operation."""

    message: str
    tools_count: int
