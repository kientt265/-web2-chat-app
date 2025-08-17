"""
Application settings and configuration
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings"""

    # Application
    app_name: str = "Message Agent Service"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 3008

    # Logging
    log_level: str = "INFO"

    # ChromaDB
    chromadb_host: str = "chromadb"
    chromadb_port: int = 8000
    chromadb_collection_name: str = "chat_messages"

    # Embedding model
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

    # CORS
    cors_origins: List[str] = ["*"]

    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()
