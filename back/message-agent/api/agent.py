"""
Agent-based query endpoints using LangGraph
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi.responses import ORJSONResponse

from managers.agent_manager import agent_manager
from core.logging import get_logger

router = APIRouter(prefix="/agent", tags=["agent"])
logger = get_logger(__name__)


class AgentQueryRequest(BaseModel):
    """Request model for agent queries"""
    query: str
    conversation_id: Optional[str] = None
    sender_id: Optional[str] = None
    agent_type: str = "message_agent"

@router.post("/query", response_model=None)
async def query_agent(request: AgentQueryRequest) -> ORJSONResponse:
    """
    Process a query using the LangGraph-based message agent
    
    This endpoint uses LangGraph to orchestrate the message retrieval
    and response generation workflow.
    """
    try:
        logger.info(f"Received agent query: {request.query[:50]}...")
        
        result = await agent_manager.process_message_query(
            query=request.query,
            conversation_id=request.conversation_id,
            sender_id=request.sender_id,
            agent_type=request.agent_type
        )

        return ORJSONResponse(
            content={
                "response": result.get("response"),
                "search_results": result.get("search_results"),
                "message_count": result.get("message_count"),
                "conversation_id": result.get("conversation_id"),
                "query": result.get("query"),
                "success": result.get("success"),
                "error": result.get("error"),
                "agent_type": result.get("agent_type"),
                "timestamp": result.get("timestamp")
            }
        )

    except Exception as e:
        logger.error(f"Error processing agent query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_agent_status():
    """Get status of all managed agents"""
    try:
        status = agent_manager.get_agent_status()
        return status
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_conversations(max_age_hours: int = 24):
    """Cleanup old conversation tracking data"""
    try:
        agent_manager.cleanup_old_conversations(max_age_hours)
        return {"message": "Conversation cleanup completed", "max_age_hours": max_age_hours}
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))
