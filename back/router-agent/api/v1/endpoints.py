"""
API endpoints for Router Agent Service.

This module defines the FastAPI endpoints for the router agent that intelligently
routes user queries to appropriate specialized agents.
"""

import time
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict

from api.v1.schemas import (
    RouterQuery,
    RouterResponse,
    RouterStatus,
    RoutingAnalysis,
    AgentInfo,
)
from core.router_manager import router_manager, AgentType
from core.websocket_manager import websocket_manager

router = APIRouter()


@router.post("/route", response_model=RouterResponse)
async def route_query(query: RouterQuery) -> RouterResponse:
    """
    Route a user query to the appropriate specialized agent.

    This endpoint analyzes the user's query and routes it to the most suitable agent:
    - Tool Agent: For calculations, web scraping, external tools
    - Message History Agent: For conversation history and message search
    - General Agent: For general conversation and other queries
    """
    start_time = time.time()

    try:
        # Force specific agent if requested
        if query.force_agent:
            try:
                forced_agent = AgentType(query.force_agent)
                if forced_agent == AgentType.TOOL_AGENT:
                    response = await router_manager.process_with_tool_agent(
                        query.message, query.session_id
                    )
                elif forced_agent == AgentType.MESSAGE_HISTORY_AGENT:
                    response = await router_manager.process_with_history_agent(
                        query.message, query.session_id
                    )
                else:  # GENERAL_AGENT
                    response = await router_manager.process_with_general_agent(
                        query.message, query.session_id
                    )

                result = {
                    "response": response,
                    "routed_to": forced_agent.value,
                    "session_id": query.session_id,
                    "query": query.message,
                }
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid agent type: {query.force_agent}"
                )
        else:
            # Use intelligent routing
            result = await router_manager.process_query(query.message, query.session_id)

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        return RouterResponse(**result, processing_time_ms=processing_time)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Routing failed: {str(e)}")


@router.post("/analyze", response_model=RoutingAnalysis)
async def analyze_query(query: RouterQuery) -> RoutingAnalysis:
    """
    Analyze a query and return routing recommendation without executing it.

    This endpoint helps understand how the router would handle a query
    without actually processing it through the selected agent.
    """
    try:
        # Determine routing without processing
        agent_type = router_manager.route_query(query.message, query.session_id)

        # Provide reasoning based on routing method
        if router_manager.model:
            reasoning = "LLM-based analysis of query content and intent"
            routing_method = "llm"
        else:
            reasoning = "Rule-based keyword and pattern matching"
            routing_method = "rule-based"

        # Suggest alternative agents
        all_agents = [agent.value for agent in AgentType]
        alternative_agents = [
            agent for agent in all_agents if agent != agent_type.value
        ]

        return RoutingAnalysis(
            query=query.message,
            recommended_agent=agent_type.value,
            confidence=0.8
            if router_manager.model
            else 0.6,  # Lower confidence for rule-based
            reasoning=f"{routing_method.title()} routing: {reasoning}",
            alternative_agents=alternative_agents,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/status", response_model=RouterStatus)
async def get_router_status() -> RouterStatus:
    """
    Get the current status of the router service and available agents.
    """
    try:
        agents_info = router_manager.get_available_agents()
        agent_objects = [AgentInfo(**agent) for agent in agents_info]

        return RouterStatus(
            status="healthy",
            available_agents=agent_objects,
            llm_available=router_manager.model is not None,
            routing_method="llm" if router_manager.model else "rule-based",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.get("/agents")
async def list_agents() -> Dict:
    """
    List all available agents and their capabilities.
    """
    try:
        agents = router_manager.get_available_agents()
        return {
            "agents": agents,
            "total_count": len(agents),
            "routing_method": "llm" if router_manager.model else "rule-based",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")


@router.post("/direct/{agent_type}")
async def direct_agent_call(agent_type: str, query: RouterQuery) -> RouterResponse:
    """
    Directly call a specific agent bypassing the routing logic.

    Useful for testing individual agents or when you know exactly
    which agent should handle the request.
    """
    start_time = time.time()

    try:
        # Validate agent type
        try:
            target_agent = AgentType(agent_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent type: {agent_type}. Available: {[a.value for a in AgentType]}",
            )

        # Call the specific agent
        if target_agent == AgentType.TOOL_AGENT:
            response = await router_manager.process_with_tool_agent(
                query.message, query.session_id
            )
        elif target_agent == AgentType.MESSAGE_HISTORY_AGENT:
            response = await router_manager.process_with_history_agent(
                query.message, query.session_id
            )
        else:  # GENERAL_AGENT
            response = await router_manager.process_with_general_agent(
                query.message, query.session_id
            )

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        return RouterResponse(
            response=response,
            routed_to=target_agent.value,
            session_id=query.session_id,
            query=query.message,
            processing_time_ms=processing_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Direct call failed: {str(e)}")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time agent communication.
    
    Supports the following message types:
    - ping: Health check (responds with pong)
    - query: Route and process a query
    - analyze: Analyze query without processing
    - status: Get router status
    - direct: Direct call to specific agent
    
    Message format:
    {
        "type": "query|analyze|status|direct|ping",
        "data": {...},
        "message_id": "optional-id",
        "session_id": "optional-session-id"
    }
    """
    client_host = websocket.client.host if websocket.client else None
    connection_id = await websocket_manager.connect(websocket, client_host)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            
            # Handle message
            await websocket_manager.handle_message(connection_id, data)
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(connection_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        websocket_manager.disconnect(connection_id)


@router.get("/ws/stats")
async def websocket_stats() -> Dict:
    """Get WebSocket connection statistics."""
    try:
        return websocket_manager.get_connection_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get WebSocket stats: {str(e)}")
