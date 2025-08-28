"""
Configuration settings for MCP service.
"""

import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for MCP service."""
    
    def __init__(self):
        """Initialize configuration."""
        self.settings = self._load_settings()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load configuration settings."""
        return {
            # Server settings
            "host": os.getenv("MCP_SERVICE_HOST", "0.0.0.0"),
            "port": int(os.getenv("MCP_SERVICE_PORT", "3005")),
            "debug": os.getenv("DEBUG", "false").lower() == "true",
            
            # MCP server configurations
            "mcp_servers": [
                {
                    "name": "calculator",
                    "type": "layered",
                    "port": 8001,
                    "enabled": True,
                    "config": {}
                },
                {
                    "name": "webscraper",
                    "type": "layered",
                    "port": 8002,
                    "enabled": True,
                    "config": {}
                }
            ],
            
            # Logging
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            
            # Service registry
            "service_registry_url": os.getenv("SERVICE_REGISTRY_URL", "http://service-registry:3003"),
            "register_with_service_registry": os.getenv("REGISTER_WITH_SERVICE_REGISTRY", "true").lower() == "true",
        }
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting.
        
        Args:
            key: Setting key
            default: Default value if key not found
            
        Returns:
            Setting value
        """
        return self.settings.get(key, default)
    
    def get_mcp_servers(self) -> List[Dict[str, Any]]:
        """Get MCP server configurations.
        
        Returns:
            List of MCP server configurations
        """
        return [
            server for server in self.settings["mcp_servers"]
            if server.get("enabled", True)
        ]


# Global configuration instance
_config: Config = None


def get_config() -> Config:
    """Get global configuration instance.
    
    Returns:
        Configuration instance
    """
    global _config
    
    if _config is None:
        _config = Config()
    
    return _config
