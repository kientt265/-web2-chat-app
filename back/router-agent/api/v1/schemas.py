"""
Pydantic schemas for Router Agent API.

This module defines the request and response models used by the Router Agent API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict


class RouterQuery(BaseModel):
    """Schema for router agent query requests."""

    message: str = Field(..., description="The user message to be processed")
    session_id: Optional[str] = Field(
        default="default", description="Session identifier for conversation context"
    )
    force_agent: Optional[str] = Field(
        default=None,
        description="Force routing to specific agent (tool-agent, message-history-agent, general-agent)",
    )


class RouterResponse(BaseModel):
    """Schema for router agent responses."""

    response: str = Field(..., description="The response from the selected agent")
    routed_to: str = Field(..., description="Which agent processed the request")
    session_id: str = Field(..., description="Session identifier")
    query: str = Field(..., description="Original user query")
    processing_time_ms: Optional[float] = Field(
        default=None, description="Time taken to process the request in milliseconds"
    )
    routing_confidence: Optional[float] = Field(
        default=None, description="Confidence score for routing decision (0.0-1.0)"
    )
    routing_reasoning: Optional[str] = Field(
        default=None, description="Explanation of routing decision"
    )
    routing_method: Optional[str] = Field(
        default=None,
        description="Method used for routing (llm-based, rule-based, fallback)",
    )


class AgentInfo(BaseModel):
    """Schema for agent information."""

    type: str = Field(..., description="Agent type identifier")
    description: str = Field(..., description="Description of agent capabilities")
    endpoint: str = Field(..., description="Agent service endpoint")


class RouterStatus(BaseModel):
    """Schema for router status information."""

    status: str = Field(..., description="Router service status")
    available_agents: List[AgentInfo] = Field(
        ..., description="List of available agents"
    )
    llm_available: bool = Field(..., description="Whether LLM routing is available")
    routing_method: str = Field(
        ..., description="Current routing method (llm or rule-based)"
    )


class RoutingAnalysis(BaseModel):
    """Schema for query routing analysis."""

    query: str = Field(..., description="The analyzed query")
    recommended_agent: str = Field(..., description="Recommended agent for this query")
    confidence: Optional[float] = Field(
        default=None, description="Confidence score for the routing decision"
    )
    reasoning: Optional[str] = Field(
        default=None, description="Explanation of routing decision"
    )
    alternative_agents: Optional[List[str]] = Field(
        default=None, description="Alternative agents that could handle this query"
    )
