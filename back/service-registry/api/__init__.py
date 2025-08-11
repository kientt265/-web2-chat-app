"""API package initialization."""

from .endpoints import router
from .dependencies import get_service_registry, get_zookeeper_client

__all__ = ["router", "get_service_registry", "get_zookeeper_client"]
