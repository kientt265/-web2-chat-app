"""Agent API Service

This module defines the FastAPI router and endpoints for the Agent API Service.
"""

from fastapi import APIRouter
from core.agent_manager import agent_manager
from .schemas import MessageRequest, MessageResponse

router = APIRouter()


@router.post("/process")
async def process_message(request: MessageRequest) -> MessageResponse:
    """Process user input and return the response."""
    response = agent_manager.process_message(request.session_id, request.user_input)
    return MessageResponse(response=response)
