"""
AI Agents module for message processing and conversation management
"""

# Import the main message agent
try:
    from .message_agent import message_agent
    MESSAGE_AGENT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Message agent not available: {e}")
    message_agent = None
    MESSAGE_AGENT_AVAILABLE = False

__all__ = ["message_agent", "MESSAGE_AGENT_AVAILABLE"]
