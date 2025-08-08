"""
Schemas for the Agent API Service
"""

from pydantic import BaseModel


class MessageRequest(BaseModel):
    """Request schema for processing a message."""

    session_id: str
    user_input: str


class MessageResponse(BaseModel):
    """Response schema for returning the processed message."""

    response: str
