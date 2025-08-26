"""
Configuration loader for MCP servers and tool-agent settings.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from services.mcp_client import MCPServerConfig

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for tool-agent."""

    def __init__(self, config_dir: str = "config"):
        """Initialize configuration manager.

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.mcp_servers: List[MCPServerConfig] = []
        self.settings: Dict[str, Any] = {}

        # Load configuration
        self._load_config()

    def _load_config(self):
        """Load configuration from files and environment variables."""
        # Load main settings
        self._load_settings()

        # Load MCP server configurations
        self._load_mcp_servers()

    def _load_settings(self):
        """Load main application settings."""
        # Default settings
        self.settings = {
            "service_registry_url": os.getenv(
                "SERVICE_REGISTRY_URL", "http://service-registry:3003"
            ),
            "mcp_timeout": int(os.getenv("MCP_TIMEOUT", "30")),
            "max_tools_per_server": int(os.getenv("MAX_TOOLS_PER_SERVER", "50")),
            "enable_mcp": os.getenv("ENABLE_MCP", "true").lower() == "true",
            "google_api_key": os.getenv("GOOGLE_API_KEY"),
        }

        # Load from config file if it exists
        settings_file = self.config_dir / "settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, "r") as f:
                    file_settings = json.load(f)
                    self.settings.update(file_settings)
                logger.info(f"Loaded settings from {settings_file}")
            except Exception as e:
                logger.error(f"Failed to load settings from {settings_file}: {e}")

    def _load_mcp_servers(self):
        """Load MCP server configurations."""
        if not self.settings.get("enable_mcp", True):
            logger.info("MCP is disabled")
            return

        # Load from config file
        mcp_config_file = self.config_dir / "mcp_servers.json"
        if mcp_config_file.exists():
            try:
                with open(mcp_config_file, "r") as f:
                    mcp_configs = json.load(f)

                for config_data in mcp_configs.get("servers", []):
                    server_config = MCPServerConfig(**config_data)
                    self.mcp_servers.append(server_config)

                logger.info(
                    f"Loaded {len(self.mcp_servers)} MCP server configs from {mcp_config_file}"
                )
            except Exception as e:
                logger.error(f"Failed to load MCP servers from {mcp_config_file}: {e}")
        else:
            # Create default MCP configuration
            self._create_default_mcp_config()

    def _create_default_mcp_config(self):
        """Create default MCP server configuration."""
        default_configs = [
            {
                "name": "filesystem",
                "command": ["npx", "@modelcontextprotocol/server-filesystem"],
                "args": ["/tmp"],
                "env": {},
            },
            {
                "name": "git",
                "command": ["npx", "@modelcontextprotocol/server-git"],
                "args": ["--repository", "."],
                "env": {},
            },
        ]

        # Only add if npx is available
        try:
            import subprocess

            subprocess.run(["npx", "--version"], capture_output=True, check=True)

            for config_data in default_configs:
                server_config = MCPServerConfig(**config_data)
                self.mcp_servers.append(server_config)

            logger.info(f"Created {len(self.mcp_servers)} default MCP server configs")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("npx not available, skipping default MCP servers")
            logger.info(
                "To enable MCP servers, install Node.js and configure mcp_servers.json"
            )

    def get_mcp_servers(self) -> List[MCPServerConfig]:
        """Get MCP server configurations.

        Returns:
            List of MCP server configurations
        """
        return self.mcp_servers

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting.

        Args:
            key: Setting key
            default: Default value if key not found

        Returns:
            Setting value
        """
        return self.settings.get(key, default)

    def add_mcp_server(self, server_config: MCPServerConfig):
        """Add MCP server configuration.

        Args:
            server_config: MCP server configuration to add
        """
        self.mcp_servers.append(server_config)
        self._save_mcp_config()

    def _save_mcp_config(self):
        """Save MCP server configurations to file."""
        try:
            self.config_dir.mkdir(exist_ok=True)
            mcp_config_file = self.config_dir / "mcp_servers.json"

            config_data = {
                "servers": [
                    {
                        "name": server.name,
                        "command": server.command,
                        "args": server.args,
                        "env": server.env,
                        "url": server.url,
                    }
                    for server in self.mcp_servers
                ]
            }

            with open(mcp_config_file, "w") as f:
                json.dump(config_data, f, indent=2)

            logger.info(f"Saved MCP configuration to {mcp_config_file}")
        except Exception as e:
            logger.error(f"Failed to save MCP configuration: {e}")


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance.

    Returns:
        Configuration instance
    """
    global _config

    if _config is None:
        _config = Config()

    return _config
