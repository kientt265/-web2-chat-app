"""
Application configuration settings
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application
    app_name: str = "Chat Sync Service"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")

    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=3005, env="SYNC_PORT")

    # Kafka
    kafka_bootstrap_servers: str = Field(
        default="kafka:9092", env="KAFKA_BOOTSTRAP_SERVERS"
    )
    kafka_group_id: str = Field(default="chat-sync-service", env="KAFKA_GROUP_ID")
    kafka_auto_offset_reset: str = Field(
        default="latest", env="KAFKA_AUTO_OFFSET_RESET"
    )

    # ChromaDB
    chromadb_host: str = Field(default="chromadb", env="CHROMADB_HOST")
    chromadb_port: int = Field(default=8000, env="CHROMADB_PORT")
    chromadb_collection_name: str = Field(
        default="chat_messages", env="CHROMADB_COLLECTION_NAME"
    )

    # Embedding
    embedding_model_name: str = Field(
        default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL_NAME"
    )

    # CDC Topics
    cdc_topics: List[str] = [
        "chat.cdc.messages",
        "chat.cdc.conversations",
        "chat.cdc.conversation_members",
        "chat.cdc.message_deliveries",
    ]

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    model_config = {"env_file": ".env", "case_sensitive": False}


# Global settings instance
settings = Settings()
