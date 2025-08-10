"""
Application configuration settings for ext-tool service
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "External Tools Service"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=3006, env="EXT_TOOL_PORT")
    
    # External Services
    sync_service_url: str = Field(default="http://localhost:3005", env="SYNC_SERVICE_URL")
    chat_service_url: str = Field(default="http://localhost:3002", env="CHAT_SERVICE_URL")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }


# Global settings instance
settings = Settings()
