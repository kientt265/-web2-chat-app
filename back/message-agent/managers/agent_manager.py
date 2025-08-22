"""
Agent Manager for coordinating different AI agents
"""

from typing import Dict, Any, Optional
from datetime import datetime

from agents.message_agent import message_agent
from core.logging import get_logger

logger = get_logger(__name__)


class AgentManager:
    """Manages and coordinates different AI agents"""
    
    def __init__(self):
        """Initialize the agent manager"""
        self.agents = {
            "message_agent": message_agent
        }
        self.active_conversations = {}
        logger.info("Agent Manager initialized")
    
    async def process_message_query(
        self, 
        query: str, 
        conversation_id: Optional[str] = None, 
        sender_id: Optional[str] = None,
        agent_type: str = "message_agent"
    ) -> Dict[str, Any]:
        """
        Process a message query using the specified agent
        
        Args:
            query: The user's query
            conversation_id: Optional conversation ID
            sender_id: Optional sender ID
            agent_type: Type of agent to use (default: message_agent)
            
        Returns:
            Dict containing the agent's response and metadata
        """
        try:
            if agent_type not in self.agents:
                raise ValueError(f"Agent type '{agent_type}' not found")
            
            agent = self.agents[agent_type]
            
            logger.info(f"Processing query with {agent_type}: {query[:50]}...")
            
            # Track conversation
            if conversation_id:
                self.active_conversations[conversation_id] = {
                    "last_activity": datetime.now(),
                    "agent_type": agent_type,
                    "query_count": self.active_conversations.get(conversation_id, {}).get("query_count", 0) + 1
                }
            
            # Process the query
            result = await agent.process_query(query, conversation_id, sender_id)
            
            # Add metadata
            result["agent_type"] = agent_type
            result["processed_by"] = "AgentManager"
            
            logger.info(f"Query processed successfully by {agent_type}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing query with {agent_type}: {e}")
            return {
                "response": f"I encountered an error processing your request: {str(e)}",
                "search_results": [],
                "message_count": 0,
                "conversation_id": conversation_id,
                "query": query,
                "success": False,
                "error": str(e),
                "agent_type": agent_type,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all managed agents"""
        return {
            "total_agents": len(self.agents),
            "available_agents": list(self.agents.keys()),
            "active_conversations": len(self.active_conversations),
            "conversation_details": {
                conv_id: {
                    "last_activity": details["last_activity"].isoformat(),
                    "agent_type": details["agent_type"],
                    "query_count": details["query_count"]
                }
                for conv_id, details in self.active_conversations.items()
            }
        }
    
    def cleanup_old_conversations(self, max_age_hours: int = 24):
        """Clean up old conversation tracking data"""
        cutoff_time = datetime.now() - datetime.timedelta(hours=max_age_hours)
        
        old_conversations = [
            conv_id for conv_id, details in self.active_conversations.items()
            if details["last_activity"] < cutoff_time
        ]
        
        for conv_id in old_conversations:
            del self.active_conversations[conv_id]
        
        if old_conversations:
            logger.info(f"Cleaned up {len(old_conversations)} old conversations")


# Global agent manager instance
agent_manager = AgentManager()
