"""Service discovery client for microservices."""

import asyncio
import random
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import httpx

from ..models import (
    ServiceInfo,
    ServiceRegistration,
    ServiceDiscoveryQuery,
    ServiceDiscoveryResponse,
    ServiceType,
    ServiceStatus
)


class ServiceDiscoveryClient:
    """Client for service discovery and registration."""
    
    def __init__(self, registry_url: str, service_id: Optional[str] = None):
        """Initialize service discovery client.
        
        Args:
            registry_url: Base URL of the service registry
            service_id: Service ID if this client represents a registered service
        """
        self.registry_url = registry_url.rstrip('/')
        self.service_id = service_id
        self._client = httpx.AsyncClient(timeout=30.0)
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = timedelta(seconds=60)
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._heartbeat_interval = 30  # seconds
    
    async def close(self):
        """Close the client and cleanup resources."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        await self._client.aclose()
    
    async def register_service(self, registration: ServiceRegistration) -> str:
        """Register this service with the registry.
        
        Args:
            registration: Service registration details
            
        Returns:
            Service ID
        """
        response = await self._client.post(
            f"{self.registry_url}/api/v1/register",
            json=registration.model_dump()
        )
        response.raise_for_status()
        
        result = response.json()
        self.service_id = result["service_id"]
        
        # Start heartbeat task
        self._start_heartbeat()
        
        return self.service_id
    
    async def unregister_service(self) -> bool:
        """Unregister this service from the registry."""
        if not self.service_id:
            return False
        
        # Stop heartbeat
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        try:
            response = await self._client.delete(
                f"{self.registry_url}/api/v1/unregister/{self.service_id}"
            )
            response.raise_for_status()
            return True
        except httpx.HTTPError:
            return False
    
    async def discover_services(
        self,
        service_type: Optional[ServiceType] = None,
        name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        capabilities: Optional[List[str]] = None,
        status: ServiceStatus = ServiceStatus.HEALTHY,
        use_cache: bool = True
    ) -> List[ServiceInfo]:
        """Discover services based on criteria.
        
        Args:
            service_type: Filter by service type
            name: Filter by service name (partial match)
            tags: Filter by tags (all must be present)
            capabilities: Filter by capabilities (all must be present)
            status: Filter by status
            use_cache: Whether to use cached results
            
        Returns:
            List of matching services
        """
        # Create cache key
        cache_key = f"discover_{service_type}_{name}_{tags}_{capabilities}_{status}"
        
        # Check cache
        if use_cache and cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if datetime.now() - timestamp < self._cache_ttl:
                return [ServiceInfo(**service) for service in cached_data]
        
        # Make discovery request
        query = ServiceDiscoveryQuery(
            service_type=service_type,
            name=name,
            tags=tags,
            capabilities=capabilities,
            status=status
        )
        
        response = await self._client.post(
            f"{self.registry_url}/api/v1/discover",
            json=query.model_dump()
        )
        response.raise_for_status()
        
        result = ServiceDiscoveryResponse(**response.json())
        
        # Update cache
        if use_cache:
            self._cache[cache_key] = (
                [service.model_dump() for service in result.services],
                datetime.now()
            )
        
        return result.services
    
    async def get_service_by_name(self, name: str) -> Optional[ServiceInfo]:
        """Get a specific service by name.
        
        Args:
            name: Service name
            
        Returns:
            Service information or None
        """
        try:
            response = await self._client.get(
                f"{self.registry_url}/api/v1/services/name/{name}"
            )
            response.raise_for_status()
            return ServiceInfo(**response.json())
        except httpx.HTTPError:
            return None
    
    async def get_healthy_service_url(
        self,
        service_type: Optional[ServiceType] = None,
        name: Optional[str] = None,
        load_balance: bool = True
    ) -> Optional[str]:
        """Get URL of a healthy service instance.
        
        Args:
            service_type: Filter by service type
            name: Filter by service name
            load_balance: Whether to randomly select from multiple instances
            
        Returns:
            Service base URL or None
        """
        services = await self.discover_services(
            service_type=service_type,
            name=name,
            status=ServiceStatus.HEALTHY
        )
        
        if not services:
            return None
        
        # Select service instance
        if load_balance and len(services) > 1:
            service = random.choice(services)
        else:
            service = services[0]
        
        return service.base_url
    
    async def call_service(
        self,
        service_name: str,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> httpx.Response:
        """Make a call to a discovered service.
        
        Args:
            service_name: Name of the target service
            endpoint: API endpoint path
            method: HTTP method
            data: Request body data
            params: Query parameters
            headers: Additional headers
            
        Returns:
            HTTP response
            
        Raises:
            ValueError: If service not found
            httpx.HTTPError: If request fails
        """
        service_url = await self.get_healthy_service_url(name=service_name)
        if not service_url:
            raise ValueError(f"Service '{service_name}' not found or unhealthy")
        
        url = f"{service_url}{endpoint}"
        
        response = await self._client.request(
            method=method,
            url=url,
            json=data,
            params=params,
            headers=headers
        )
        response.raise_for_status()
        
        return response
    
    async def heartbeat(self) -> bool:
        """Send heartbeat for this service."""
        if not self.service_id:
            return False
        
        try:
            response = await self._client.post(
                f"{self.registry_url}/api/v1/heartbeat/{self.service_id}"
            )
            response.raise_for_status()
            return True
        except httpx.HTTPError:
            return False
    
    def _start_heartbeat(self):
        """Start the heartbeat task."""
        if self.service_id and not self._heartbeat_task:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def _heartbeat_loop(self):
        """Background heartbeat loop."""
        while True:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                await self.heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue heartbeat
                print(f"Heartbeat error: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
    
    def clear_cache(self):
        """Clear the discovery cache."""
        self._cache.clear()
