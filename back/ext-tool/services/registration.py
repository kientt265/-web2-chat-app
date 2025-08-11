"""Service registration client for ext-tool service."""

import os
import socket
from typing import Optional
import httpx
import asyncio

from core.logging import get_logger

logger = get_logger(__name__)


class ServiceRegistrationClient:
    """Client for registering with the service registry."""

    def __init__(self, registry_url: str):
        """Initialize service registration client.

        Args:
            registry_url: Base URL of the service registry
        """
        self.registry_url = registry_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
        self.service_id: Optional[str] = None
        self.heartbeat_task: Optional[asyncio.Task] = None

    async def register(
        self, service_name: str, service_port: int, service_host: Optional[str] = None
    ) -> str:
        """Register this service with the registry.

        Args:
            service_name: Name of the service
            service_port: Port the service is running on
            service_host: Host the service is running on (auto-detected if None)

        Returns:
            Service ID
        """
        if service_host is None:
            service_host = self._get_container_hostname()

        registration_data = {
            "name": service_name,
            "service_type": "tool",
            "host": service_host,
            "port": service_port,
            "metadata": {
                "description": "External tools service for AI agents",
                "version": "1.0.0",
                "tags": ["tools", "ai", "external"],
                "capabilities": ["search", "calculation", "scraping"],
                "extra": {
                    "available_tools": [
                        "/tools/search-messages",
                        "/tools/calculator",
                        "/tools/scraper",
                    ]
                },
            },
            "health_check": {
                "enabled": True,
                "endpoint": "/health",
                "interval_seconds": 30,
                "timeout_seconds": 5,
                "retries": 3,
            },
        }

        try:
            response = await self.client.post(
                f"{self.registry_url}/api/v1/register", json=registration_data
            )
            response.raise_for_status()

            result = response.json()
            self.service_id = result["service_id"]

            logger.info(
                f"Registered service '{service_name}' with ID: {self.service_id}"
            )

            # Start heartbeat
            self._start_heartbeat()

            return self.service_id

        except Exception as e:
            logger.error(f"Failed to register service: {e}")
            raise

    async def unregister(self) -> bool:
        """Unregister this service from the registry."""
        if not self.service_id:
            return False

        # Stop heartbeat
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass

        try:
            response = await self.client.delete(
                f"{self.registry_url}/api/v1/unregister/{self.service_id}"
            )
            response.raise_for_status()

            logger.info(f"Unregistered service with ID: {self.service_id}")
            self.service_id = None
            return True

        except Exception as e:
            logger.error(f"Failed to unregister service: {e}")
            return False

    def _get_container_hostname(self) -> str:
        """Get the hostname for service registration."""
        # Try to get hostname from environment (Docker container name)
        hostname = os.getenv("HOSTNAME")
        if hostname:
            return hostname

        # Fallback to system hostname
        return socket.gethostname()

    def _start_heartbeat(self):
        """Start the heartbeat task."""
        if self.service_id and not self.heartbeat_task:
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self):
        """Background heartbeat loop."""
        while True:
            try:
                await asyncio.sleep(25)  # Send heartbeat every 25 seconds
                await self._send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(5)  # Brief pause before retry

    async def _send_heartbeat(self) -> bool:
        """Send heartbeat to registry."""
        if not self.service_id:
            return False

        try:
            response = await self.client.post(
                f"{self.registry_url}/api/v1/heartbeat/{self.service_id}"
            )
            response.raise_for_status()
            logger.debug(f"Heartbeat sent for service ID: {self.service_id}")
            return True

        except Exception as e:
            logger.warning(f"Failed to send heartbeat: {e}")
            return False

    async def close(self):
        """Close the client and cleanup resources."""
        await self.unregister()
        await self.client.aclose()


# Global instance
_registration_client: Optional[ServiceRegistrationClient] = None


def get_registration_client() -> ServiceRegistrationClient:
    """Get the global service registration client."""
    global _registration_client

    if _registration_client is None:
        registry_url = os.getenv("SERVICE_REGISTRY_URL", "http://service-registry:3003")
        _registration_client = ServiceRegistrationClient(registry_url)

    return _registration_client
