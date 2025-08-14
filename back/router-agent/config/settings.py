"""
Configuration settings for Router Agent Service.

This module handles environment variables and service configuration
for the router agent including agent endpoint URLs and LLM settings.
"""

import os
from typing import Dict


class RouterConfig:
    """Configuration class for Router Agent Service."""

    # Service settings
    HOST: str = os.getenv("ROUTER_AGENT_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("ROUTER_AGENT_PORT", "3007"))

    # LLM settings
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

    # Agent service URLs
    TOOL_AGENT_URL: str = os.getenv("TOOL_AGENT_URL", "http://localhost:3004")
    HISTORY_AGENT_URL: str = os.getenv("HISTORY_AGENT_URL", "http://localhost:3005")
    GENERAL_AGENT_URL: str = os.getenv("GENERAL_AGENT_URL", "http://localhost:3004")

    # Timeouts and limits
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def get_agent_endpoints(cls) -> Dict[str, str]:
        """Get all agent endpoint URLs."""
        return {
            "tool-agent": f"{cls.TOOL_AGENT_URL}/api/v1/process",
            "message-history-agent": f"{cls.HISTORY_AGENT_URL}/search/messages",
            "general-agent": f"{cls.GENERAL_AGENT_URL}/api/v1/process",
        }

    @classmethod
    def is_llm_available(cls) -> bool:
        """Check if LLM is available (has API key)."""
        return bool(cls.GOOGLE_API_KEY.strip())


# Global configuration instance
config = RouterConfig()
