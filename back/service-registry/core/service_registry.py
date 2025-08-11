"""Service Registry implementation using Zookeeper."""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import httpx

from .zookeeper_client import ZookeeperClient
from .logging import get_logger
from models import (
    ServiceInfo,
    ServiceRegistration,
    ServiceUpdate,
    ServiceStatus,
    ServiceDiscoveryQuery,
    ServiceDiscoveryResponse,
    RegistryStats,
)
from config import settings

logger = get_logger(__name__)


class ServiceRegistry:
    """Service registry using Zookeeper for coordination."""

    def __init__(self, zk_client: ZookeeperClient):
        """Initialize service registry.

        Args:
            zk_client: Zookeeper client instance
        """
        self.zk_client = zk_client
        self.services: Dict[str, ServiceInfo] = {}
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start the service registry."""
        logger.info("Starting Service Registry...")

        # Connect to Zookeeper
        await self.zk_client.connect()

        # Ensure base paths exist
        self.zk_client.ensure_path(settings.services_root_path)

        # Load existing services from Zookeeper
        await self._load_services_from_zk()

        # Start health check task
        self._running = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())

        # Watch for service changes
        self.zk_client.watch_children(
            settings.services_root_path, self._on_services_changed
        )

        logger.info("Service Registry started successfully")

    async def stop(self) -> None:
        """Stop the service registry."""
        logger.info("Stopping Service Registry...")

        self._running = False

        # Cancel health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # Disconnect from Zookeeper
        await self.zk_client.disconnect()

        logger.info("Service Registry stopped")

    async def register_service(self, registration: ServiceRegistration) -> str:
        """Register a new service.

        Args:
            registration: Service registration details

        Returns:
            Service ID
        """
        service_id = str(uuid.uuid4())

        # Create service info
        service_info = ServiceInfo(
            service_id=service_id,
            name=registration.name,
            service_type=registration.service_type,
            host=registration.host,
            port=registration.port,
            status=ServiceStatus.STARTING,
            metadata=registration.metadata or {},
            health_check=registration.health_check or {},
        )

        # Store in local cache
        self.services[service_id] = service_info

        # Store in Zookeeper
        zk_path = f"{settings.services_root_path}/{service_id}"
        self.zk_client.create_node(zk_path, service_info.model_dump(), ephemeral=True)

        logger.info(f"Registered service: {registration.name} ({service_id})")

        # Perform initial health check
        await self._check_service_health(service_info)

        return service_id

    async def unregister_service(self, service_id: str) -> bool:
        """Unregister a service.

        Args:
            service_id: Service ID to unregister

        Returns:
            True if successfully unregistered
        """
        if service_id not in self.services:
            logger.warning(f"Service not found for unregistration: {service_id}")
            return False

        # Remove from local cache
        service_info = self.services.pop(service_id)

        # Remove from Zookeeper
        zk_path = f"{settings.services_root_path}/{service_id}"
        self.zk_client.delete_node(zk_path)

        logger.info(f"Unregistered service: {service_info.name} ({service_id})")
        return True

    async def update_service(self, service_id: str, update: ServiceUpdate) -> bool:
        """Update service information.

        Args:
            service_id: Service ID to update
            update: Update information

        Returns:
            True if successfully updated
        """
        if service_id not in self.services:
            logger.warning(f"Service not found for update: {service_id}")
            return False

        service_info = self.services[service_id]

        # Update fields
        if update.status is not None:
            service_info.status = update.status
        if update.metadata is not None:
            service_info.metadata = update.metadata
        if update.health_check is not None:
            service_info.health_check = update.health_check

        service_info.last_heartbeat = datetime.utcnow()

        # Update in Zookeeper
        zk_path = f"{settings.services_root_path}/{service_id}"
        self.zk_client.update_node_data(zk_path, service_info.model_dump())

        logger.debug(f"Updated service: {service_info.name} ({service_id})")
        return True

    async def discover_services(
        self, query: ServiceDiscoveryQuery
    ) -> ServiceDiscoveryResponse:
        """Discover services based on query criteria.

        Args:
            query: Discovery query parameters

        Returns:
            List of matching services
        """
        matching_services = []

        for service_info in self.services.values():
            if self._matches_query(service_info, query):
                matching_services.append(service_info)

        return ServiceDiscoveryResponse(
            services=matching_services, total_count=len(matching_services), query=query
        )

    def _matches_query(
        self, service: ServiceInfo, query: ServiceDiscoveryQuery
    ) -> bool:
        """Check if service matches discovery query."""

        # Check service type
        if query.service_type and service.service_type != query.service_type:
            return False

        # Check name (partial match)
        if query.name and query.name.lower() not in service.name.lower():
            return False

        # Check status
        if query.status and service.status != query.status:
            return False

        # Check tags
        if query.tags:
            service_tags = set(service.metadata.tags)
            query_tags = set(query.tags)
            if not query_tags.issubset(service_tags):
                return False

        # Check capabilities
        if query.capabilities:
            service_capabilities = set(service.metadata.capabilities)
            query_capabilities = set(query.capabilities)
            if not query_capabilities.issubset(service_capabilities):
                return False

        return True

    async def get_service(self, service_id: str) -> Optional[ServiceInfo]:
        """Get service information by ID.

        Args:
            service_id: Service ID

        Returns:
            Service information or None if not found
        """
        return self.services.get(service_id)

    async def get_service_by_name(self, name: str) -> Optional[ServiceInfo]:
        """Get service information by name.

        Args:
            name: Service name

        Returns:
            Service information or None if not found
        """
        for service in self.services.values():
            if service.name == name:
                return service
        return None

    async def heartbeat(self, service_id: str) -> bool:
        """Update service heartbeat.

        Args:
            service_id: Service ID

        Returns:
            True if heartbeat recorded
        """
        if service_id not in self.services:
            return False

        self.services[service_id].last_heartbeat = datetime.utcnow()

        # Update in Zookeeper
        zk_path = f"{settings.services_root_path}/{service_id}"
        self.zk_client.update_node_data(zk_path, self.services[service_id].model_dump())

        return True

    def get_registry_stats(self) -> RegistryStats:
        """Get registry statistics."""
        services_by_type = {}
        services_by_status = {}

        for service in self.services.values():
            # Count by type
            if service.service_type not in services_by_type:
                services_by_type[service.service_type] = 0
            services_by_type[service.service_type] += 1

            # Count by status
            if service.status not in services_by_status:
                services_by_status[service.status] = 0
            services_by_status[service.status] += 1

        healthy_count = services_by_status.get(ServiceStatus.HEALTHY, 0)
        total_count = len(self.services)
        unhealthy_count = total_count - healthy_count

        return RegistryStats(
            total_services=total_count,
            services_by_type=services_by_type,
            services_by_status=services_by_status,
            healthy_services=healthy_count,
            unhealthy_services=unhealthy_count,
        )

    async def _load_services_from_zk(self) -> None:
        """Load existing services from Zookeeper."""
        try:
            service_ids = self.zk_client.get_children(settings.services_root_path)

            for service_id in service_ids:
                zk_path = f"{settings.services_root_path}/{service_id}"
                service_data = self.zk_client.get_node_data(zk_path)

                if service_data:
                    service_info = ServiceInfo(**service_data)
                    self.services[service_id] = service_info
                    logger.debug(f"Loaded service from ZK: {service_info.name}")

            logger.info(f"Loaded {len(self.services)} services from Zookeeper")

        except Exception as e:
            logger.error(f"Failed to load services from Zookeeper: {e}")

    def _on_services_changed(self, children: List[str]) -> None:
        """Handle changes in service nodes."""
        current_ids = set(self.services.keys())
        zk_ids = set(children)

        # Handle removed services
        removed_ids = current_ids - zk_ids
        for service_id in removed_ids:
            if service_id in self.services:
                service_info = self.services.pop(service_id)
                logger.info(f"Service removed: {service_info.name} ({service_id})")

        # Handle new services
        new_ids = zk_ids - current_ids
        for service_id in new_ids:
            zk_path = f"{settings.services_root_path}/{service_id}"
            service_data = self.zk_client.get_node_data(zk_path)

            if service_data:
                service_info = ServiceInfo(**service_data)
                self.services[service_id] = service_info
                logger.info(f"New service detected: {service_info.name} ({service_id})")

    async def _health_check_loop(self) -> None:
        """Background task for health checking services."""
        logger.info("Starting health check loop")

        while self._running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(settings.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying

        logger.info("Health check loop stopped")

    async def _perform_health_checks(self) -> None:
        """Perform health checks on all registered services."""
        if not self.services:
            return

        # Create health check tasks
        tasks = []
        for service_info in self.services.values():
            if service_info.health_check.enabled:
                task = asyncio.create_task(self._check_service_health(service_info))
                tasks.append(task)

        if tasks:
            # Wait for all health checks to complete
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_service_health(self, service_info: ServiceInfo) -> None:
        """Check health of a single service."""
        if not service_info.health_check.enabled:
            return

        try:
            async with httpx.AsyncClient(
                timeout=service_info.health_check.timeout_seconds
            ) as client:
                response = await client.get(service_info.health_url)

                if response.status_code == 200:
                    if service_info.status != ServiceStatus.HEALTHY:
                        service_info.status = ServiceStatus.HEALTHY
                        service_info.last_heartbeat = datetime.utcnow()
                        await self._update_service_in_zk(service_info)
                        logger.info(f"Service health restored: {service_info.name}")
                else:
                    if service_info.status != ServiceStatus.UNHEALTHY:
                        service_info.status = ServiceStatus.UNHEALTHY
                        await self._update_service_in_zk(service_info)
                        logger.warning(
                            f"Service unhealthy (HTTP {response.status_code}): {service_info.name}"
                        )

        except Exception as e:
            if service_info.status != ServiceStatus.UNHEALTHY:
                service_info.status = ServiceStatus.UNHEALTHY
                await self._update_service_in_zk(service_info)
                logger.warning(
                    f"Service health check failed: {service_info.name} - {e}"
                )

    async def _update_service_in_zk(self, service_info: ServiceInfo) -> None:
        """Update service information in Zookeeper."""
        try:
            zk_path = f"{settings.services_root_path}/{service_info.service_id}"
            self.zk_client.update_node_data(zk_path, service_info.model_dump())
        except Exception as e:
            logger.error(f"Failed to update service in ZK: {e}")

    async def cleanup_stale_services(self) -> int:
        """Remove stale services that haven't sent heartbeat recently."""
        cutoff_time = datetime.utcnow() - timedelta(seconds=settings.service_ttl)
        stale_services = []

        for service_id, service_info in self.services.items():
            if service_info.last_heartbeat < cutoff_time:
                stale_services.append(service_id)

        # Remove stale services
        for service_id in stale_services:
            await self.unregister_service(service_id)

        if stale_services:
            logger.info(f"Cleaned up {len(stale_services)} stale services")

        return len(stale_services)
