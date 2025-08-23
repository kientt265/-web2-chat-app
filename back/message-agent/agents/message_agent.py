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
    from core.initialization import ensure_chromadb_initialized
    SERVICES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Services not available: {e}")
    chromadb_service = None
    message_service = None
    ensure_chromadb_initialized = None
    SERVICES_AVAILABLE = False

from core.logging import get_logger
from core.rate_limiter import gemini_rate_limiter

logger = get_logger(__name__)


class AgentState(TypedDict):
    """State for the message agent workflow"""
    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    search_term: str
    conversation_id: Optional[str]
    sender_id: Optional[str]
    search_results: Optional[List[Dict[str, Any]]]
    response: Optional[str]
    context: Optional[str]
    agent_action: Optional[str]
    search_terms: Optional[List[str]]  # New: extracted search terms from LLM
    search_filters: Optional[Dict[str, Any]]  # New: extracted filters from LLM
    user_intent: Optional[str]  # New: user intent description from LLM
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
                model="gemini-2.5-flash",
                temperature=0.1,
                convert_system_message_to_human=True,
                # Rate limiting configuration
                max_retries=3,
                request_timeout=30.0,
                # Reduce requests per minute to stay within limits
                max_tokens_per_minute=100000,
                max_requests_per_minute=10
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
    
    async def _parse_query(self, state: AgentState) -> AgentState:
        """Parse the user query using LLM to determine search parameters and actions"""
        try:
            query = state.get("query", "")
            conversation_id = state.get("conversation_id")
            
            if not query:
                state["error"] = "Empty query provided"
                return state
            
            logger.info(f"Parsing query with LLM: {query}")
            
            # Use LLM to parse query and extract parameters
            parsed_result = await self._llm_parse_query(query)
            
            # Update state with LLM-parsed information
            state["agent_action"] = parsed_result.get("action", "search")
            state["search_terms"] = parsed_result.get("search_terms", [])
            state["search_filters"] = parsed_result.get("filters", {})
            state["user_intent"] = parsed_result.get("intent", "")
            
            # Add system message to track the conversation
            system_msg = SystemMessage(
                content=f"Processing message query for conversation: {conversation_id}. Intent: {state['user_intent']}"
            )
            human_msg = HumanMessage(content=query)
            
            state["messages"] = [system_msg, human_msg]
            
            logger.info(f"Parsed action: {state['agent_action']}, terms: {state['search_terms']}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error parsing query: {e}")
            # Fallback to simple parsing
            state.update(self._simple_parse_fallback(query, conversation_id))
            return state

    async def _llm_parse_query(self, query: str) -> dict:
        """Use LLM to intelligently parse user query and extract parameters"""
        try:
            # If no LLM available, fall back immediately
            if not self.llm:
                logger.info("No LLM available, using simple parsing fallback")
                return self._simple_parse_fallback_dict(query)
            
            # Check rate limits before making LLM call
            if not await gemini_rate_limiter.can_make_request():
                logger.warning("Rate limit reached, falling back to simple parsing")
                return self._simple_parse_fallback_dict(query)
            
            # Structured prompt for query parsing
            parse_prompt = f"""
Analyze this user query and extract the following information in JSON format:

Query: "{query}"

Extract:
1. action: The primary action the user wants (search, recent, list, count, summary)
2. search_terms: Array of important keywords/phrases to search for
3. filters: Object with any filters like time, sender, etc.
4. intent: Brief description of what the user is trying to accomplish

Rules:
- If query is just a word/phrase like "hi" or "hello", treat it as search terms
- For "recent" or "latest" requests, set action to "recent"
- Extract meaningful keywords, ignore stop words
- Be liberal with search terms - include anything that might be relevant

Return ONLY valid JSON, no other text:
{{
    "action": "search|recent|list|count|summary",
    "search_terms": ["term1", "term2"],
    "filters": {{}},
    "intent": "brief description"
}}
"""

            # Make LLM call with rate limiting
            response = await self.llm.ainvoke([HumanMessage(content=parse_prompt)])
            result_text = response.content.strip()
            
            # Try to parse JSON response
            try:
                import json
                parsed_result = json.loads(result_text)
                
                # Validate required fields
                if not isinstance(parsed_result.get("action"), str):
                    parsed_result["action"] = "search"
                if not isinstance(parsed_result.get("search_terms"), list):
                    parsed_result["search_terms"] = [query]
                if not isinstance(parsed_result.get("filters"), dict):
                    parsed_result["filters"] = {}
                if not isinstance(parsed_result.get("intent"), str):
                    parsed_result["intent"] = "Search for messages"
                
                return parsed_result
                
            except json.JSONDecodeError as je:
                logger.warning(f"Failed to parse LLM JSON response: {je}")
                # Extract action and terms from text response as fallback
                return self._extract_from_text_response(result_text, query)
            
        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            return self._simple_parse_fallback_dict(query)

    def _extract_from_text_response(self, text: str, original_query: str) -> dict:
        """Extract information from non-JSON LLM response"""
        text_lower = text.lower()
        
        # Try to extract action
        if "recent" in text_lower or "latest" in text_lower:
            action = "recent"
        elif "search" in text_lower or "find" in text_lower:
            action = "search"
        else:
            action = "search"
        
        # Use original query as search term
        return {
            "action": action,
            "search_terms": [original_query],
            "filters": {},
            "intent": f"Process query: {original_query}"
        }

    def _simple_parse_fallback_dict(self, query: str) -> dict:
        """Simple parsing fallback when LLM is unavailable"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["recent", "latest", "last"]):
            action = "recent"
        else:
            action = "search"
        
        # Extract potential search terms (remove common stop words)
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        terms = [word for word in query.lower().split() if word not in stop_words and len(word) > 2]
        
        if not terms:  # If no meaningful terms found, use the whole query
            terms = [query]
        
        return {
            "action": action,
            "search_terms": terms,
            "filters": {},
            "intent": f"Simple parsing of: {query}"
        }

    def _simple_parse_fallback(self, query: str, conversation_id: str) -> dict:
        """Simple parsing fallback that returns state updates"""
        parsed = self._simple_parse_fallback_dict(query)
        
        system_msg = SystemMessage(
            content=f"Processing message query for conversation: {conversation_id}. Intent: {parsed['intent']}"
        )
        human_msg = HumanMessage(content=query)
        
        return {
            "agent_action": parsed["action"],
            "search_terms": parsed["search_terms"],
            "search_filters": parsed["filters"],
            "user_intent": parsed["intent"],
            "messages": [system_msg, human_msg]
        }

    async def _search_messages(self, state: AgentState) -> AgentState:
        """Search for relevant messages using semantic search"""
        try:
            query = state.get("query", "")
            conversation_id = state.get("conversation_id")
            sender_id = state.get("sender_id")
            action = state.get("agent_action", "search")
            search_terms = state.get("search_terms", [])
            search_filters = state.get("search_filters", {})
            
            logger.info(f"Searching messages - Action: {action}, Terms: {search_terms}")
            
            if not SERVICES_AVAILABLE:
                # Use mock data when services are not available
                state["search_results"] = self._generate_mock_results(query, action)
                return state
            
            # Try to ensure ChromaDB is initialized
            try:
                if ensure_chromadb_initialized:
                    await ensure_chromadb_initialized()
            except Exception as e:
                logger.warning(f"Failed to initialize ChromaDB: {e}")
            
            if action == "recent":
                # Get recent messages
                try:
                    messages = await chromadb_service.get_recent_messages(
                        conversation_id=conversation_id,
                        limit=search_filters.get("limit", 10)
                    )
                    state["search_results"] = [msg.__dict__ for msg in messages] if messages else []
                except Exception as e:
                    logger.warning(f"ChromaDB not available, using mock data: {e}")
                    state["search_results"] = self._generate_mock_results(query, action)
            else:
                # Semantic search using extracted search terms
                try:
                    # Use search_terms if available, otherwise fallback to original query
                    search_query = " ".join(search_terms) if search_terms else query
                    
                    messages = await message_service.search_messages(
                        query_texts=search_query,
                        conversation_id=conversation_id,
                        sender_id=sender_id,
                        limit=search_filters.get("limit", 10)
                    )
                    state["search_results"] = [msg.__dict__ for msg in messages] if messages else []
                    
                    logger.info(f"Search query: '{search_query}' found {len(state.get('search_results', []))} results")
                    
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
    
    async def _generate_response(self, state: AgentState) -> AgentState:
        """Generate a response using the LLM"""
        try:
            query = state.get("query", "")
            context = state.get("context", "")
            conversation_id = state.get("conversation_id", "")
            user_intent = state.get("user_intent", "")
            action = state.get("agent_action", "search")
            search_terms = state.get("search_terms", [])
            
            if not self.llm:
                # Fallback response without LLM
                response = self._generate_fallback_response(state)
                state["response"] = response
                return state
            
            # Create enhanced prompt template for Gemini with intent awareness
            prompt = ChatPromptTemplate.from_messages([
                ("human", """You are a helpful assistant that helps users find and understand messages from their conversation history.

User Intent: {user_intent}
Action Taken: {action}
Search Terms Used: {search_terms}

Context from conversation history:
{context}

Instructions:
1. Use the provided context to answer the user's query based on their intent
2. Be concise and helpful
3. If no relevant messages are found, explain what was searched for and suggest alternatives
4. Include specific details from the messages when relevant
5. If asked about recent messages, summarize the latest activity
6. Reference the search terms if they were important to the query

Current conversation ID: {conversation_id}

User Query: {query}""")
            ])
            
            # Create chain
            chain = prompt | self.llm | StrOutputParser()
            
            # Generate response with rate limiting
            if self.llm:
                # Check rate limits before making API call
                can_proceed = await gemini_rate_limiter.wait_and_record_request()
                
                if not can_proceed:
                    logger.warning("Gemini daily quota exceeded, using fallback response")
                    response = self._generate_fallback_response(state)
                else:
                    try:
                        response = chain.invoke({
                            "query": query,
                            "context": context,
                            "conversation_id": conversation_id,
                            "user_intent": user_intent,
                            "action": action,
                            "search_terms": ", ".join(search_terms) if search_terms else "None"
                        })
                        logger.info("✅ Gemini API response generated successfully")
                    except Exception as llm_error:
                        # Check if it's a rate limit error
                        error_str = str(llm_error).lower()
                        if "rate_limit" in error_str or "quota" in error_str or "429" in error_str:
                            logger.warning(f"⚠️ Rate limit hit despite precautions, falling back: {llm_error}")
                            response = self._generate_fallback_response(state)
                        else:
                            # Re-raise other LLM errors
                            raise llm_error
            else:
                response = self._generate_fallback_response(state)
            
            state["response"] = response
            
            # Add AI message to conversation
            ai_msg = AIMessage(content=response)
            state["messages"] = state.get("messages", []) + [ai_msg]
            
            logger.info("Response generated successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # For any error, fall back to a basic response
            fallback_response = self._generate_fallback_response(state)
            state["response"] = fallback_response
            
            # Add fallback message to conversation
            ai_msg = AIMessage(content=fallback_response)
            state["messages"] = state.get("messages", []) + [ai_msg]
            
            logger.info("Used fallback response due to error")
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
            # Initialize state with new fields
            initial_state = AgentState(
                messages=[],
                query=query,
                search_term=query,  # Legacy field for compatibility
                conversation_id=conversation_id,
                sender_id=sender_id,
                search_results=None,
                response=None,
                context=None,
                agent_action=None,
                search_terms=None,  # Will be populated by LLM parsing
                search_filters=None,  # Will be populated by LLM parsing  
                user_intent=None,  # Will be populated by LLM parsing
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
