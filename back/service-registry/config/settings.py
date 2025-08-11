"""Configuration settings for the Service Registry."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Service Registry configuration settings."""

    # Application settings
    app_name: str = "Service Registry"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server settings
    host: str = "0.0.0.0"
    port: int = int(os.getenv("SERVICE_REGISTRY_PORT", 3003))

    # Zookeeper settings
    zookeeper_hosts: str = os.getenv("ZOOKEEPER_HOSTS", "zookeeper:2181")
    zookeeper_timeout: int = int(os.getenv("ZOOKEEPER_TIMEOUT", 10))

    # Service registry settings
    services_root_path: str = "/services"
    health_check_interval: int = 30  # seconds
    service_ttl: int = 60  # seconds

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
