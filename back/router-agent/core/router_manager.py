"""
Router Manager module for intelligently routing user queries to specialized agents.

This module provides the RouterManager class which analyzes user queries and
routes them to appropriate specialized agents including tool-agent and message-history-agent.
"""

import httpx
from typing import Dict, List
from typing_extensions import TypedDict
from enum import Enum

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

from config.settings import config
from prompts.router_prompts import router_prompts

# Load environment variables
load_dotenv()


class AgentType(Enum):
    """Enumeration of available agent types."""

    TOOL_AGENT = "tool-agent"
    MESSAGE_HISTORY_AGENT = "message-history-agent"
    GENERAL_AGENT = "general-agent"

class State(TypedDict):
    input: str
    decision: str
    output: str


class RouterManager:
    """
    Manages intelligent routing of user queries to specialized agents.
    """

    def __init__(self):
        """Initialize the RouterManager with routing capabilities."""
        self.model = None
        self.agent_endpoints = config.get_agent_endpoints()

        # Initialize the LLM for routing decisions
        if config.is_llm_available():
            try:
                self.model = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    temperature=0.1
                )
                print("✅ Router LLM initialized successfully")
            except Exception as e:
                print(f"Warning: Could not initialize Router LLM: {e}")
                print("Router will use rule-based routing as fallback")
        else:
            print("No Google API key found, using rule-based routing")

    def _analyze_query_with_llm(
        self, user_input: str, enhanced: bool = True
    ) -> AgentType:
        """
        Use LLM to analyze the user query and determine the best agent.

        Args:
            user_input: The user's input message
            enhanced: Whether to use enhanced prompt with examples

        Returns:
            AgentType: The recommended agent type
        """
        if not self.model:
            return self._analyze_query_with_rules(user_input)

        try:
            # Get the routing prompt from centralized prompts
            routing_content = router_prompts.get_routing_prompt(
                user_input, enhanced=enhanced
            )

            messages = [
                SystemMessage(content=router_prompts.SYSTEM_PROMPT),
                HumanMessage(content=routing_content),
            ]

            response = self.model.invoke(messages)

            # Extract the agent type from response
            agent_decision = response.content.strip().upper()

            if "TOOL_AGENT" in agent_decision:
                return AgentType.TOOL_AGENT
            elif "MESSAGE_HISTORY_AGENT" in agent_decision:
                return AgentType.MESSAGE_HISTORY_AGENT
            else:
                return AgentType.GENERAL_AGENT

        except Exception as e:
            print(f"LLM routing failed, falling back to rule-based: {e}")
            return self._analyze_query_with_rules(user_input)

    def _analyze_query_with_rules(self, user_input: str) -> AgentType:
        """
        Rule-based fallback for query analysis.

        Args:
            user_input: The user's input message

        Returns:
            AgentType: The recommended agent type
        """
        query_lower = user_input.lower()

        # Tool agent keywords
        tool_keywords = [
            "calculate",
            "compute",
            "math",
            "solve",
            "equation",
            "formula",
            "scrape",
            "fetch",
            "download",
            "search web",
            "browse",
            "tool",
            "api",
            "process",
            "convert",
            "transform",
            "sqrt",
            "square root",
        ]

        # Message history keywords
        history_keywords = [
            "previous",
            "history",
            "earlier",
            "before",
            "past",
            "find messages",
            "search messages",
            "what did we discuss",
            "conversation",
            "messages about",
            "show me",
            "recall",
            "yesterday",
            "last week",
            "talked about",
        ]

        # Check for tool agent patterns
        if any(keyword in query_lower for keyword in tool_keywords):
            return AgentType.TOOL_AGENT

        # Check for math expressions (numbers and operators)
        if any(
            char in query_lower
            for char in ["+", "-", "*", "/", "=", "√", "^", "²", "³"]
        ):
            return AgentType.TOOL_AGENT

        # Check for message history patterns
        if any(keyword in query_lower for keyword in history_keywords):
            return AgentType.MESSAGE_HISTORY_AGENT

        # Default to general agent
        return AgentType.GENERAL_AGENT

    async def get_routing_confidence(
        self, user_input: str, agent_type: AgentType
    ) -> Dict:
        """
        Get confidence score and reasoning for a routing decision.

        Args:
            user_input: The user's input message
            agent_type: The recommended agent type

        Returns:
            Dict: Confidence score and reasoning
        """
        if not self.model:
            return {
                "confidence": 0.6,  # Lower confidence for rule-based
                "reasoning": "Rule-based routing using keyword matching",
                "method": "rule-based",
            }

        try:
            confidence_prompt = router_prompts.get_confidence_prompt(
                user_input, agent_type.value
            )

            messages = [
                SystemMessage(
                    content="You are an expert at evaluating routing decisions."
                ),
                HumanMessage(content=confidence_prompt),
            ]

            response = self.model.invoke(messages)
            content = response.content.strip()

            # Parse confidence and reasoning
            confidence = 0.7  # default
            reasoning = "LLM-based routing analysis"

            if "CONFIDENCE:" in content:
                try:
                    conf_line = [
                        line for line in content.split("\n") if "CONFIDENCE:" in line
                    ][0]
                    confidence = float(conf_line.split("CONFIDENCE:")[1].strip())
                except:
                    pass

            if "REASONING:" in content:
                try:
                    reason_line = [
                        line for line in content.split("\n") if "REASONING:" in line
                    ][0]
                    reasoning = reason_line.split("REASONING:")[1].strip()
                except:
                    pass

            return {
                "confidence": confidence,
                "reasoning": reasoning,
                "method": "llm-based",
            }

        except Exception as e:
            return {
                "confidence": 0.6,
                "reasoning": f"Confidence analysis failed: {str(e)}",
                "method": "fallback",
            }

    def route_query(self, user_input: str, session_id: str = "default") -> AgentType:
        """
        Analyze and route a user query to the appropriate agent.

        Args:
            user_input: The user's input message
            session_id: Session identifier

        Returns:
            AgentType: The determined agent type
        """
        print(f"🔍 Analyzing query: '{user_input[:50]}...'")

        if self.model:
            agent_type = self._analyze_query_with_llm(user_input, enhanced=True)
        else:
            agent_type = self._analyze_query_with_rules(user_input)

        # Get routing explanation
        explanation = router_prompts.get_routing_explanation(agent_type.value)
        print(f"📍 Routed to: {agent_type.value}")
        print(f"💡 Reason: {explanation}")

        return agent_type

    async def process_with_tool_agent(self, user_input: str, session_id: str) -> str:
        """
        Process query with the tool agent.

        Args:
            user_input: User's input message
            session_id: Session identifier

        Returns:
            str: Agent response
        """
        try:
            async with httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT) as client:
                payload = {"message": user_input, "session_id": session_id}

                response = await client.post(
                    self.agent_endpoints[AgentType.TOOL_AGENT.value], json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "Tool agent processed the request")
                else:
                    return f"Tool agent error: {response.status_code} - {response.text}"

        except Exception as e:
            return f"Failed to connect to tool agent: {str(e)}"

    async def process_with_history_agent(self, user_input: str, session_id: str) -> str:
        """
        Process query with the message history agent.

        Args:
            user_input: User's input message
            session_id: Session identifier

        Returns:
            str: Agent response
        """
        try:
            async with httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT) as client:
                payload = {
                    "query": user_input,
                    "conversation_id": session_id,
                    "limit": 10,
                }

                response = await client.post(
                    self.agent_endpoints[AgentType.MESSAGE_HISTORY_AGENT.value],
                    json=payload,
                )

                if response.status_code == 200:
                    result = response.json()

                    # Format the search results
                    if result.get("results"):
                        messages = result["results"]
                        formatted_response = (
                            f"Found {len(messages)} relevant messages:\n\n"
                        )

                        for i, msg in enumerate(messages[:5], 1):  # Show top 5 results
                            content = msg.get("content", "")[:100]
                            sender = msg.get("sender_id", "Unknown")
                            timestamp = msg.get("timestamp", "")
                            formatted_response += f"{i}. [{sender}] {content}...\n"
                            if timestamp:
                                formatted_response += f"   📅 {timestamp}\n"
                            formatted_response += "\n"

                        return formatted_response.strip()
                    else:
                        return (
                            "No relevant messages found in your conversation history."
                        )
                else:
                    return f"Message history agent error: {response.status_code} - {response.text}"

        except Exception as e:
            return f"Failed to connect to message history agent: {str(e)}"

    async def process_with_general_agent(self, user_input: str, session_id: str) -> str:
        """
        Process query with the general agent.

        Args:
            user_input: User's input message
            session_id: Session identifier

        Returns:
            str: Agent response
        """
        try:
            async with httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT) as client:
                payload = {"message": user_input, "session_id": session_id}

                response = await client.post(
                    self.agent_endpoints[AgentType.GENERAL_AGENT.value], json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "General agent processed the request")
                else:
                    return (
                        f"General agent error: {response.status_code} - {response.text}"
                    )

        except Exception as e:
            return f"Failed to connect to general agent: {str(e)}"

    async def process_query(self, user_input: str, session_id: str = "default") -> Dict:
        """
        Main entry point for processing user queries.

        Args:
            user_input: User's input message
            session_id: Session identifier

        Returns:
            Dict: Response containing the result and routing information
        """
        # Determine which agent to use
        agent_type = self.route_query(user_input, session_id)

        # Get confidence information
        confidence_info = await self.get_routing_confidence(user_input, agent_type)

        # Process with the selected agent
        if agent_type == AgentType.TOOL_AGENT:
            response = await self.process_with_tool_agent(user_input, session_id)
        elif agent_type == AgentType.MESSAGE_HISTORY_AGENT:
            response = await self.process_with_history_agent(user_input, session_id)
        else:  # GENERAL_AGENT
            response = await self.process_with_general_agent(user_input, session_id)

        return {
            "response": response,
            "routed_to": agent_type.value,
            "session_id": session_id,
            "query": user_input,
            "routing_confidence": confidence_info["confidence"],
            "routing_reasoning": confidence_info["reasoning"],
            "routing_method": confidence_info["method"],
        }

    def get_available_agents(self) -> List[Dict]:
        """Get list of available agents and their capabilities."""
        return [
            {
                "type": AgentType.TOOL_AGENT.value,
                "description": "Handles queries requiring external tools (calculations, web scraping, data processing)",
                "endpoint": self.agent_endpoints[AgentType.TOOL_AGENT.value],
            },
            {
                "type": AgentType.MESSAGE_HISTORY_AGENT.value,
                "description": "Handles queries about conversation history and message search",
                "endpoint": self.agent_endpoints[AgentType.MESSAGE_HISTORY_AGENT.value],
            },
            {
                "type": AgentType.GENERAL_AGENT.value,
                "description": "Handles general conversation and queries",
                "endpoint": self.agent_endpoints[AgentType.GENERAL_AGENT.value],
            },
        ]


# Global instance
router_manager = RouterManager()
