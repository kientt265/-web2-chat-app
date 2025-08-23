"""
LangGraph-based Message Agent

This agent handles message retrieval, semantic search, and conversation management
using LangGraph for workflow orchestration.
"""

import os
from typing import List, Dict, Any, Optional, TypedDict, Annotated
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

# Import services with fallback
try:
    from services.chromadb_service import chromadb_service
    from services.message_service import message_service
    SERVICES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Services not available: {e}")
    chromadb_service = None
    message_service = None
    SERVICES_AVAILABLE = False

from core.logging import get_logger

logger = get_logger(__name__)


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


class MessageAgent:
    """LangGraph-based message agent for handling conversation queries"""
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """Initialize the message agent with LangGraph workflow"""
        self.gemini_api_key = gemini_api_key or os.getenv("GOOGLE_API_KEY")
        if not self.gemini_api_key:
            logger.warning("No Gemini API key provided. Agent will work with limited functionality.")
            self.llm = None
        else:
            self.llm = ChatGoogleGenerativeAI(
                google_api_key=self.gemini_api_key,
                model="gemini-1.5-flash",
                temperature=0.1,
                convert_system_message_to_human=True
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
            sender_id = state.get("sender_id")
            
            logger.info(f"Parsing query: {query}")
            
            # Determine the type of query and required action
            if not query.strip():
                state["error"] = "Empty query provided"
                return state
            
            # Simple intent classification (can be enhanced with LLM)
            query_lower = query.lower()
            if any(word in query_lower for word in ["search", "find", "look for", "retrieve"]):
                state["agent_action"] = "search"
            elif any(word in query_lower for word in ["recent", "latest", "last"]):
                state["agent_action"] = "recent"
            else:
                state["agent_action"] = "search"  # Default action
            
            # Add system message to track the conversation
            system_msg = SystemMessage(
                content=f"Processing message query for conversation: {conversation_id}"
            )
            human_msg = HumanMessage(content=query)
            
            state["messages"] = [system_msg, human_msg]
            
            return state
            
        except Exception as e:
            logger.error(f"Error parsing query: {e}")
            state["error"] = f"Query parsing failed: {str(e)}"
            return state

    async def _search_messages(self, state: AgentState) -> AgentState:
        """Search for relevant messages using semantic search"""
        try:
            query = state.get("query", "")
            conversation_id = state.get("conversation_id")
            sender_id = state.get("sender_id")
            action = state.get("agent_action", "search")
            
            logger.info(f"Searching messages with action: {action}")
            
            if not SERVICES_AVAILABLE:
                # Use mock data when services are not available
                state["search_results"] = self._generate_mock_results(query, action)
                return state
            
            if action == "recent":
                # Get recent messages
                try:
                    messages = chromadb_service.get_recent_messages(
                        conversation_id=conversation_id,
                        limit=10
                    )
                    state["search_results"] = [msg.__dict__ for msg in messages] if messages else []
                except Exception as e:
                    logger.warning(f"ChromaDB not available, using mock data: {e}")
                    state["search_results"] = self._generate_mock_results(query, action)
            else:
                # Semantic search
                try:
                    messages = await message_service.search_messages(
                        query_texts=query,
                        conversation_id=conversation_id,
                        sender_id=sender_id,
                        limit=10
                    )
                    state["search_results"] = [msg.__dict__ for msg in messages] if messages else []
                except Exception as e:
                    logger.warning(f"Search service not available, using mock data: {e}")
                    state["search_results"] = self._generate_mock_results(query, action)
            
            logger.info(f"Found {len(state.get('search_results', []))} messages")
            return state
            
        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            state["error"] = f"Message search failed: {str(e)}"
            return state
    
    def _generate_mock_results(self, query: str, action: str) -> List[Dict[str, Any]]:
        """Generate mock search results for testing"""
        mock_results = []
        
        if action == "recent":
            mock_results = [
                {
                    "message_id": f"msg_{i}",
                    "content": f"Recent message {i}: This is a mock recent message",
                    "sender_id": f"user_{i % 3}",
                    "sent_at": datetime.now().isoformat(),
                    "similarity_score": None,
                    "conversation_id": "mock-conv"
                }
                for i in range(1, 6)
            ]
        else:
            mock_results = [
                {
                    "message_id": f"search_{i}",
                    "content": f"Mock result {i} for query '{query}': This message contains relevant information",
                    "sender_id": f"user_{i % 3}",
                    "sent_at": datetime.now().isoformat(),
                    "similarity_score": 0.9 - (i * 0.1),
                    "conversation_id": "mock-conv"
                }
                for i in range(1, 4)
            ]
        
        return mock_results
    
    def _retrieve_context(self, state: AgentState) -> AgentState:
        """Retrieve and format context from search results"""
        try:
            search_results = state.get("search_results", [])
            
            if not search_results:
                state["context"] = "No relevant messages found in the conversation history."
                return state
            
            # Format the context from search results
            context_parts = []
            for i, result in enumerate(search_results[:5], 1):  # Limit to top 5 results
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
                    context_part += f"Relevance: {similarity:.3f}\n"
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
        """Generate a response using the LLM"""
        try:
            query = state.get("query", "")
            context = state.get("context", "")
            conversation_id = state.get("conversation_id", "")
            
            if not self.llm:
                # Fallback response without LLM
                response = self._generate_fallback_response(state)
                state["response"] = response
                return state
            
            # Create prompt template for Gemini
            prompt = ChatPromptTemplate.from_messages([
                ("human", """You are a helpful assistant that helps users find and understand messages from their conversation history.

Context from conversation history:
{context}

Instructions:
1. Use the provided context to answer the user's query
2. Be concise and helpful
3. If no relevant messages are found, say so clearly
4. Include specific details from the messages when relevant
5. If asked about recent messages, summarize the latest activity

Current conversation ID: {conversation_id}

User Query: {query}""")
            ])
            
            # Create chain
            chain = prompt | self.llm | StrOutputParser()
            
            # Generate response
            response = chain.invoke({
                "query": query,
                "context": context,
                "conversation_id": conversation_id
            })
            
            state["response"] = response
            
            # Add AI message to conversation
            ai_msg = AIMessage(content=response)
            state["messages"] = state.get("messages", []) + [ai_msg]
            
            logger.info("Response generated successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            state["error"] = f"Response generation failed: {str(e)}"
            return state
    
    def _generate_fallback_response(self, state: AgentState) -> str:
        """Generate a fallback response when LLM is not available"""
        search_results = state.get("search_results", [])
        query = state.get("query", "")
        action = state.get("agent_action", "search")
        
        if not search_results:
            return f"I searched for '{query}' but couldn't find any relevant messages in your conversation history."
        
        if action == "recent":
            count = len(search_results)
            return f"I found {count} recent messages in your conversation. The most recent activity includes various messages from different participants."
        else:
            count = len(search_results)
            return f"I found {count} messages related to '{query}'. Here are the most relevant results from your conversation history."
    
    def _handle_error(self, state: AgentState) -> AgentState:
        """Handle errors in the workflow"""
        error = state.get("error", "Unknown error occurred")
        logger.error(f"Workflow error: {error}")
        
        state["response"] = f"I encountered an error while processing your request: {error}"
        
        # Add error message to conversation
        error_msg = AIMessage(content=state["response"])
        state["messages"] = state.get("messages", []) + [error_msg]
        
        return state
    
    def _route_after_parse(self, state: AgentState) -> str:
        """Route the workflow after parsing the query"""
        if state.get("error"):
            return "error"
        return "search"
    
    async def process_query(
        self, 
        query: str, 
        conversation_id: Optional[str] = None, 
        sender_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a query through the LangGraph workflow
        
        Args:
            query: The user's query
            conversation_id: Optional conversation ID for filtering
            sender_id: Optional sender ID for filtering
            
        Returns:
            Dict containing the response and metadata
        """
        try:
            # Initialize state
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
                "timestamp": datetime.now().isoformat()
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
                "timestamp": datetime.now().isoformat()
            }


# Global agent instance
message_agent = MessageAgent()
