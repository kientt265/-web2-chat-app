"""
WebSocket Manager for Router Agent Service.

This module provides WebSocket connection management and real-time
communication capabilities for the router agent service.
"""

import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError
import logging

from core.router_manager import router_manager, AgentType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketMessage(BaseModel):
    """WebSocket message schema."""
    type: str  # 'query', 'status', 'ping', etc.
    data: Dict[str, Any]
    message_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: Optional[str] = None


class WebSocketResponse(BaseModel):
    """WebSocket response schema."""
    type: str  # 'response', 'error', 'status', 'pong', etc.
    data: Dict[str, Any]
    message_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: str
    processing_time_ms: Optional[float] = None


class ConnectionInfo(BaseModel):
    """Connection information."""
    connection_id: str
    session_id: Optional[str] = None
    connected_at: datetime
    last_activity: datetime
    client_ip: Optional[str] = None


class WebSocketManager:
    """Manages WebSocket connections for real-time agent communication."""

    def __init__(self):
        """Initialize WebSocket manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_info: Dict[str, ConnectionInfo] = {}
        self.session_connections: Dict[str, List[str]] = {}  # session_id -> [connection_ids]

    async def connect(self, websocket: WebSocket, client_ip: Optional[str] = None) -> str:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        connection_id = str(uuid.uuid4())
        now = datetime.now()
        
        self.active_connections[connection_id] = websocket
        self.connection_info[connection_id] = ConnectionInfo(
            connection_id=connection_id,
            connected_at=now,
            last_activity=now,
            client_ip=client_ip
        )
        
        logger.info(f"WebSocket connection established: {connection_id}")
        
        # Send welcome message
        await self._send_message(connection_id, WebSocketResponse(
            type="connection",
            data={
                "status": "connected",
                "connection_id": connection_id,
                "message": "Welcome to Router Agent WebSocket"
            },
            timestamp=now.isoformat()
        ))
        
        return connection_id

    def disconnect(self, connection_id: str):
        """Handle WebSocket disconnection."""
        if connection_id in self.active_connections:
            # Remove from active connections
            del self.active_connections[connection_id]
            
            # Get connection info before removing
            conn_info = self.connection_info.get(connection_id)
            if conn_info and conn_info.session_id:
                # Remove from session connections
                if conn_info.session_id in self.session_connections:
                    if connection_id in self.session_connections[conn_info.session_id]:
                        self.session_connections[conn_info.session_id].remove(connection_id)
                    if not self.session_connections[conn_info.session_id]:
                        del self.session_connections[conn_info.session_id]
            
            # Remove connection info
            if connection_id in self.connection_info:
                del self.connection_info[connection_id]
            
            logger.info(f"WebSocket connection closed: {connection_id}")

    async def _send_message(self, connection_id: str, response: WebSocketResponse):
        """Send a message to a specific connection."""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(response.model_dump_json())
                
                # Update last activity
                if connection_id in self.connection_info:
                    self.connection_info[connection_id].last_activity = datetime.now()
                    
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                self.disconnect(connection_id)

    async def broadcast_to_session(self, session_id: str, response: WebSocketResponse):
        """Broadcast a message to all connections in a session."""
        if session_id in self.session_connections:
            disconnected_connections = []
            
            for connection_id in self.session_connections[session_id]:
                try:
                    await self._send_message(connection_id, response)
                except Exception as e:
                    logger.error(f"Failed to broadcast to {connection_id}: {e}")
                    disconnected_connections.append(connection_id)
            
            # Clean up disconnected connections
            for connection_id in disconnected_connections:
                self.disconnect(connection_id)

    async def handle_message(self, connection_id: str, message_data: str) -> None:
        """Handle incoming WebSocket message."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Parse message
            raw_message = json.loads(message_data)
            message = WebSocketMessage(**raw_message)
            
            # Update connection info
            if connection_id in self.connection_info:
                conn_info = self.connection_info[connection_id]
                conn_info.last_activity = datetime.now()
                
                # Associate with session if provided
                if message.session_id and not conn_info.session_id:
                    conn_info.session_id = message.session_id
                    if message.session_id not in self.session_connections:
                        self.session_connections[message.session_id] = []
                    self.session_connections[message.session_id].append(connection_id)

            # Route message based on type
            response = await self._route_message(message)
            
            # Calculate processing time
            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
            response.processing_time_ms = processing_time
            
            # Send response
            await self._send_message(connection_id, response)
            
        except ValidationError as e:
            error_response = WebSocketResponse(
                type="error",
                data={
                    "error": "Invalid message format",
                    "details": str(e),
                    "code": "VALIDATION_ERROR"
                },
                timestamp=datetime.now().isoformat()
            )
            await self._send_message(connection_id, error_response)
            
        except json.JSONDecodeError as e:
            error_response = WebSocketResponse(
                type="error", 
                data={
                    "error": "Invalid JSON format",
                    "details": str(e),
                    "code": "JSON_ERROR"
                },
                timestamp=datetime.now().isoformat()
            )
            await self._send_message(connection_id, error_response)
            
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            error_response = WebSocketResponse(
                type="error",
                data={
                    "error": "Internal server error",
                    "details": str(e),
                    "code": "INTERNAL_ERROR"
                },
                timestamp=datetime.now().isoformat()
            )
            await self._send_message(connection_id, error_response)

    async def _route_message(self, message: WebSocketMessage) -> WebSocketResponse:
        """Route message to appropriate handler."""
        message_type = message.type.lower()
        
        if message_type == "ping":
            return await self._handle_ping(message)
        elif message_type == "query":
            return await self._handle_query(message)
        elif message_type == "analyze":
            return await self._handle_analyze(message)
        elif message_type == "status":
            return await self._handle_status(message)
        elif message_type == "direct":
            return await self._handle_direct(message)
        else:
            return WebSocketResponse(
                type="error",
                data={
                    "error": f"Unknown message type: {message_type}",
                    "code": "UNKNOWN_MESSAGE_TYPE"
                },
                message_id=message.message_id,
                session_id=message.session_id,
                timestamp=datetime.now().isoformat()
            )

    async def _handle_ping(self, message: WebSocketMessage) -> WebSocketResponse:
        """Handle ping message."""
        return WebSocketResponse(
            type="pong",
            data={"message": "pong"},
            message_id=message.message_id,
            session_id=message.session_id,
            timestamp=datetime.now().isoformat()
        )

    async def _handle_query(self, message: WebSocketMessage) -> WebSocketResponse:
        """Handle query routing message."""
        try:
            user_message = message.data.get("message", "")
            session_id = message.session_id or "default"
            force_agent = message.data.get("force_agent")
            
            if not user_message:
                return WebSocketResponse(
                    type="error",
                    data={
                        "error": "Missing 'message' in query data",
                        "code": "MISSING_MESSAGE"
                    },
                    message_id=message.message_id,
                    session_id=message.session_id,
                    timestamp=datetime.now().isoformat()
                )

            # Process query with router manager
            if force_agent:
                try:
                    forced_agent = AgentType(force_agent)
                    if forced_agent == AgentType.TOOL_AGENT:
                        response = await router_manager.process_with_tool_agent(
                            user_message, session_id
                        )
                    elif forced_agent == AgentType.MESSAGE_HISTORY_AGENT:
                        response = await router_manager.process_with_history_agent(
                            user_message, session_id
                        )
                    else:  # GENERAL_AGENT
                        response = await router_manager.process_with_general_agent(
                            user_message, session_id
                        )
                    
                    result = {
                        "response": response,
                        "routed_to": forced_agent.value,
                        "session_id": session_id,
                        "query": user_message,
                        "forced": True
                    }
                except ValueError:
                    return WebSocketResponse(
                        type="error",
                        data={
                            "error": f"Invalid agent type: {force_agent}",
                            "code": "INVALID_AGENT"
                        },
                        message_id=message.message_id,
                        session_id=message.session_id,
                        timestamp=datetime.now().isoformat()
                    )
            else:
                result = await router_manager.process_query(user_message, session_id)
            
            return WebSocketResponse(
                type="response",
                data=result,
                message_id=message.message_id,
                session_id=message.session_id,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return WebSocketResponse(
                type="error",
                data={
                    "error": f"Query processing failed: {str(e)}",
                    "code": "QUERY_ERROR"
                },
                message_id=message.message_id,
                session_id=message.session_id,
                timestamp=datetime.now().isoformat()
            )

    async def _handle_analyze(self, message: WebSocketMessage) -> WebSocketResponse:
        """Handle query analysis message."""
        try:
            user_message = message.data.get("message", "")
            session_id = message.session_id or "default"
            
            if not user_message:
                return WebSocketResponse(
                    type="error",
                    data={
                        "error": "Missing 'message' in analyze data",
                        "code": "MISSING_MESSAGE"
                    },
                    message_id=message.message_id,
                    session_id=message.session_id,
                    timestamp=datetime.now().isoformat()
                )
            
            # Analyze routing without processing
            agent_type = router_manager.route_query(user_message, session_id)
            confidence_info = await router_manager.get_routing_confidence(user_message, agent_type)
            
            # Get alternative agents
            all_agents = [agent.value for agent in AgentType]
            alternative_agents = [agent for agent in all_agents if agent != agent_type.value]
            
            analysis_result = {
                "query": user_message,
                "recommended_agent": agent_type.value,
                "confidence": confidence_info["confidence"],
                "reasoning": confidence_info["reasoning"],
                "method": confidence_info["method"],
                "alternative_agents": alternative_agents
            }
            
            return WebSocketResponse(
                type="analysis",
                data=analysis_result,
                message_id=message.message_id,
                session_id=message.session_id,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
            return WebSocketResponse(
                type="error",
                data={
                    "error": f"Query analysis failed: {str(e)}",
                    "code": "ANALYSIS_ERROR"
                },
                message_id=message.message_id,
                session_id=message.session_id,
                timestamp=datetime.now().isoformat()
            )

    async def _handle_status(self, message: WebSocketMessage) -> WebSocketResponse:
        """Handle status request message."""
        try:
            agents_info = router_manager.get_available_agents()
            
            status_data = {
                "status": "healthy",
                "available_agents": agents_info,
                "llm_available": router_manager.model is not None,
                "routing_method": "llm" if router_manager.model else "rule-based",
                "active_connections": len(self.active_connections),
                "active_sessions": len(self.session_connections)
            }
            
            return WebSocketResponse(
                type="status",
                data=status_data,
                message_id=message.message_id,
                session_id=message.session_id,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return WebSocketResponse(
                type="error",
                data={
                    "error": f"Status check failed: {str(e)}",
                    "code": "STATUS_ERROR"
                },
                message_id=message.message_id,
                session_id=message.session_id,
                timestamp=datetime.now().isoformat()
            )

    async def _handle_direct(self, message: WebSocketMessage) -> WebSocketResponse:
        """Handle direct agent call message."""
        try:
            agent_type = message.data.get("agent_type", "")
            user_message = message.data.get("message", "")
            session_id = message.session_id or "default"
            
            if not agent_type or not user_message:
                return WebSocketResponse(
                    type="error",
                    data={
                        "error": "Missing 'agent_type' or 'message' in direct data",
                        "code": "MISSING_PARAMETERS"
                    },
                    message_id=message.message_id,
                    session_id=message.session_id,
                    timestamp=datetime.now().isoformat()
                )
            
            # Validate agent type
            try:
                target_agent = AgentType(agent_type)
            except ValueError:
                return WebSocketResponse(
                    type="error",
                    data={
                        "error": f"Invalid agent type: {agent_type}",
                        "available_agents": [a.value for a in AgentType],
                        "code": "INVALID_AGENT"
                    },
                    message_id=message.message_id,
                    session_id=message.session_id,
                    timestamp=datetime.now().isoformat()
                )
            
            # Call the specific agent
            if target_agent == AgentType.TOOL_AGENT:
                response = await router_manager.process_with_tool_agent(user_message, session_id)
            elif target_agent == AgentType.MESSAGE_HISTORY_AGENT:
                response = await router_manager.process_with_history_agent(user_message, session_id)
            else:  # GENERAL_AGENT
                response = await router_manager.process_with_general_agent(user_message, session_id)
            
            result = {
                "response": response,
                "routed_to": target_agent.value,
                "session_id": session_id,
                "query": user_message,
                "direct_call": True
            }
            
            return WebSocketResponse(
                type="response",
                data=result,
                message_id=message.message_id,
                session_id=message.session_id,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error in direct call: {e}")
            return WebSocketResponse(
                type="error",
                data={
                    "error": f"Direct call failed: {str(e)}",
                    "code": "DIRECT_CALL_ERROR"
                },
                message_id=message.message_id,
                session_id=message.session_id,
                timestamp=datetime.now().isoformat()
            )

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics."""
        return {
            "active_connections": len(self.active_connections),
            "active_sessions": len(self.session_connections),
            "connection_details": [
                {
                    "connection_id": conn_info.connection_id,
                    "session_id": conn_info.session_id,
                    "connected_at": conn_info.connected_at.isoformat(),
                    "last_activity": conn_info.last_activity.isoformat(),
                    "client_ip": conn_info.client_ip
                }
                for conn_info in self.connection_info.values()
            ]
        }


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
