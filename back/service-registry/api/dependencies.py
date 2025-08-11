"""Dependency injection for API endpoints."""

from core.service_registry import ServiceRegistry
from core.zookeeper_client import ZookeeperClient
from config import settings

# Global instances
_zk_client: ZookeeperClient = None
_service_registry: ServiceRegistry = None


async def get_zookeeper_client() -> ZookeeperClient:
    """Get Zookeeper client instance."""
    global _zk_client
    if _zk_client is None:
        _zk_client = ZookeeperClient(
            hosts=settings.zookeeper_hosts, timeout=settings.zookeeper_timeout
        )
    return _zk_client


async def get_service_registry() -> ServiceRegistry:
    """Get service registry instance."""
    global _service_registry
    if _service_registry is None:
        zk_client = await get_zookeeper_client()
        _service_registry = ServiceRegistry(zk_client)
    return _service_registry
