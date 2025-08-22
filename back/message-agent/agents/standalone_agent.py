"""
Standalone LangGraph-based Message Agent (without ChromaDB)

This agent handles message queries using LangGraph workflow orchestration
with mock data for demonstration purposes.
"""

import os
from typing import List, Dict, Any, Optional, TypedDict, Annotated
from datetime import datetime, timedelta
import logging

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Try to import OpenAI, but make it optional
try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    ChatOpenAI = None

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the message agent workflow"""
    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    conversation_id: Optional[str]
    sender_id: Optional[str]
    search_results: Optional[List[Dict[str, Any]]]
    response: Optional[str]
    context: Optional[str]
    agent_action: Optional[str]
    error: Optional[str]


class StandaloneMessageAgent:
    """Standalone LangGraph-based message agent"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the message agent with LangGraph workflow"""
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        if not OPENAI_AVAILABLE or not self.openai_api_key:
            logger.warning("OpenAI not available or no API key. Using fallback responses.")
            self.llm = None
        else:
            self.llm = ChatOpenAI(
                api_key=self.openai_api_key,
                model="gpt-4o-mini",
                temperature=0.1
            )
        
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for message processing"""
        workflow = StateGraph(AgentState)
        
        # Define the workflow nodes
        workflow.add_node("parse_query", self._parse_query)
        workflow.add_node("search_messages", self._search_messages)
        workflow.add_node("retrieve_context", self._retrieve_context)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("handle_error", self._handle_error)
        
        # Define the workflow edges
        workflow.add_edge(START, "parse_query")
        workflow.add_conditional_edges(
            "parse_query",
            self._route_after_parse,
            {
                "search": "search_messages",
                "error": "handle_error"
            }
        )
        workflow.add_edge("search_messages", "retrieve_context")
        workflow.add_edge("retrieve_context", "generate_response")
        workflow.add_edge("generate_response", END)
        workflow.add_edge("handle_error", END)
        
        return workflow
    
    def _parse_query(self, state: AgentState) -> AgentState:
        """Parse and analyze the incoming query"""
        try:
            query = state.get("query", "")
            conversation_id = state.get("conversation_id")
            
            logger.info(f"Parsing query: {query}")
            
            if not query.strip():
                state["error"] = "Empty query provided"
                return state
            
            # Simple intent classification
            query_lower = query.lower()
            if any(word in query_lower for word in ["recent", "latest", "last"]):
                state["agent_action"] = "recent"
            elif any(word in query_lower for word in ["search", "find", "look for"]):
                state["agent_action"] = "search"
            else:
                state["agent_action"] = "search"
            
            # Add messages to track conversation
            system_msg = SystemMessage(
                content=f"Processing query for conversation: {conversation_id or 'unknown'}"
            )
            human_msg = HumanMessage(content=query)
            state["messages"] = [system_msg, human_msg]
            
            return state
            
        except Exception as e:
            logger.error(f"Error parsing query: {e}")
            state["error"] = f"Query parsing failed: {str(e)}"
            return state
    
    def _search_messages(self, state: AgentState) -> AgentState:
        """Search for relevant messages using mock data"""
        try:
            query = state.get("query", "")
            conversation_id = state.get("conversation_id", "unknown")
            action = state.get("agent_action", "search")
            
            logger.info(f"Searching messages with action: {action}")
            
            # Generate mock results based on action
            if action == "recent":
                mock_results = [
                    {
                        "message_id": f"recent_{i}",
                        "content": f"Recent message {i}: Discussion about daily standup and project progress",
                        "sender_id": f"user_{i % 3 + 1}",
                        "sent_at": (datetime.now() - timedelta(hours=i)).isoformat(),
                        "similarity_score": None,
                        "conversation_id": conversation_id
                    }
                    for i in range(1, 6)
                ]
            else:
                # Generate search results based on query
                mock_results = [
                    {
                        "message_id": f"search_{i}",
                        "content": f"Message {i} containing '{query}': This is a relevant discussion about the topic you searched for",
                        "sender_id": f"user_{i % 3 + 1}",
                        "sent_at": (datetime.now() - timedelta(days=i)).isoformat(),
                        "similarity_score": round(0.95 - (i * 0.1), 2),
                        "conversation_id": conversation_id
                    }
                    for i in range(1, 4)
                ]
            
            state["search_results"] = mock_results
            logger.info(f"Found {len(mock_results)} mock messages")
            return state
            
        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            state["error"] = f"Message search failed: {str(e)}"
            return state
    
    def _retrieve_context(self, state: AgentState) -> AgentState:
        """Retrieve and format context from search results"""
        try:
            search_results = state.get("search_results", [])
            
            if not search_results:
                state["context"] = "No relevant messages found in the conversation history."
                return state
            
            # Format context
            context_parts = []
            for i, result in enumerate(search_results[:5], 1):
                message_id = result.get("message_id", f"msg_{i}")
                content = result.get("content", "")
                sender = result.get("sender_id", "unknown")
                timestamp = result.get("sent_at", "")
                similarity = result.get("similarity_score")
                
                context_part = f"Message {i} (ID: {message_id}):\n"
                context_part += f"Sender: {sender}\n"
                if timestamp:
                    context_part += f"Time: {timestamp}\n"
                if similarity:
                    context_part += f"Relevance: {similarity}\n"
                context_part += f"Content: {content}\n"
                
                context_parts.append(context_part)
            
            state["context"] = "\n---\n".join(context_parts)
            logger.info("Context retrieved and formatted")
            return state
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            state["error"] = f"Context retrieval failed: {str(e)}"
            return state
    
    def _generate_response(self, state: AgentState) -> AgentState:
        """Generate a response using LLM or fallback"""
        try:
            query = state.get("query", "")
            context = state.get("context", "")
            conversation_id = state.get("conversation_id", "")
            search_results = state.get("search_results", [])
            
            if not self.llm:
                # Fallback response
                response = self._generate_fallback_response(state)
            else:
                # Use LLM to generate response
                prompt = ChatPromptTemplate.from_messages([
                    ("system", """You are a helpful assistant that helps users find and understand messages from their conversation history.

Context from conversation history:
{context}

Instructions:
1. Use the provided context to answer the user's query
2. Be concise and helpful
3. If no relevant messages are found, say so clearly
4. Include specific details from messages when relevant
5. Summarize key findings

Conversation ID: {conversation_id}"""),
                    ("human", "{query}")
                ])
                
                chain = prompt | self.llm | StrOutputParser()
                response = chain.invoke({
                    "query": query,
                    "context": context,
                    "conversation_id": conversation_id
                })
            
            state["response"] = response
            
            # Add AI message
            ai_msg = AIMessage(content=response)
            current_messages = state.get("messages", [])
            state["messages"] = current_messages + [ai_msg]
            
            logger.info("Response generated successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            state["error"] = f"Response generation failed: {str(e)}"
            return state
    
    def _generate_fallback_response(self, state: AgentState) -> str:
        """Generate fallback response without LLM"""
        search_results = state.get("search_results", [])
        query = state.get("query", "")
        action = state.get("agent_action", "search")
        
        if not search_results:
            return f"I searched for '{query}' but couldn't find any relevant messages in the conversation history."
        
        count = len(search_results)
        
        if action == "recent":
            return f"I found {count} recent messages in the conversation. The latest activity includes discussions about daily standups and project progress."
        else:
            # Create a summary of search results
            summary_parts = []
            for i, result in enumerate(search_results[:3], 1):
                sender = result.get("sender_id", "unknown")
                content_preview = result.get("content", "")[:100] + "..."
                summary_parts.append(f"{i}. {sender}: {content_preview}")
            
            summary = "\n".join(summary_parts)
            
            return f"I found {count} messages related to '{query}'. Here are the most relevant results:\n\n{summary}"
    
    def _handle_error(self, state: AgentState) -> AgentState:
        """Handle errors in the workflow"""
        error = state.get("error", "Unknown error occurred")
        logger.error(f"Workflow error: {error}")
        
        state["response"] = f"I encountered an error while processing your request: {error}"
        
        error_msg = AIMessage(content=state["response"])
        current_messages = state.get("messages", [])
        state["messages"] = current_messages + [error_msg]
        
        return state
    
    def _route_after_parse(self, state: AgentState) -> str:
        """Route after parsing query"""
        return "error" if state.get("error") else "search"
    
    async def process_query(
        self, 
        query: str, 
        conversation_id: Optional[str] = None, 
        sender_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a query through the LangGraph workflow"""
        try:
            initial_state = AgentState(
                messages=[],
                query=query,
                conversation_id=conversation_id,
                sender_id=sender_id,
                search_results=None,
                response=None,
                context=None,
                agent_action=None,
                error=None
            )
            
            # Run the workflow
            final_state = await self.app.ainvoke(initial_state)
            
            # Extract results
            response = final_state.get("response", "I couldn't process your request.")
            search_results = final_state.get("search_results", [])
            error = final_state.get("error")
            
            return {
                "response": response,
                "search_results": search_results,
                "message_count": len(search_results),
                "conversation_id": conversation_id,
                "query": query,
                "success": error is None,
                "error": error,
                "timestamp": datetime.now().isoformat(),
                "agent_type": "standalone_langgraph_agent"
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "response": f"I encountered an error: {str(e)}",
                "search_results": [],
                "message_count": 0,
                "conversation_id": conversation_id,
                "query": query,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "agent_type": "standalone_langgraph_agent"
            }


# Global agent instance
standalone_message_agent = StandaloneMessageAgent()
