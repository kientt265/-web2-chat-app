"""
AI Agents module for message processing and conversation management
"""

# Import standalone agent that doesn't depend on ChromaDB
try:
    from .standalone_agent import standalone_message_agent
    STANDALONE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Standalone agent not available: {e}")
    standalone_message_agent = None
    STANDALONE_AVAILABLE = False

# Note: Full agent with ChromaDB support is disabled due to NumPy compatibility issues
# TODO: Fix ChromaDB NumPy compatibility and re-enable full agent
message_agent = None
FULL_AGENT_AVAILABLE = False

__all__ = ["standalone_message_agent", "message_agent", "STANDALONE_AVAILABLE", "FULL_AGENT_AVAILABLE"]
