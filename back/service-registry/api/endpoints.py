"""API endpoints for the service registry."""

from fastapi import APIRouter, HTTPException, Depends

from models import (
    ServiceInfo,
    ServiceRegistration,
    ServiceUpdate,
    ServiceDiscoveryQuery,
    ServiceDiscoveryResponse,
    RegistryStats,
)
from core.service_registry import ServiceRegistry
from .dependencies import get_service_registry

router = APIRouter()


@router.post("/register", response_model=dict)
async def register_service(
    registration: ServiceRegistration,
    registry: ServiceRegistry = Depends(get_service_registry),
) -> dict:
    """Register a new service with the registry."""
    try:
        service_id = await registry.register_service(registration)
        return {
            "service_id": service_id,
            "message": f"Service '{registration.name}' registered successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.delete("/unregister/{service_id}")
async def unregister_service(
    service_id: str, registry: ServiceRegistry = Depends(get_service_registry)
) -> dict:
    """Unregister a service from the registry."""
    success = await registry.unregister_service(service_id)
    if not success:
        raise HTTPException(status_code=404, detail="Service not found")

    return {"message": f"Service '{service_id}' unregistered successfully"}


@router.put("/update/{service_id}")
async def update_service(
    service_id: str,
    update: ServiceUpdate,
    registry: ServiceRegistry = Depends(get_service_registry),
) -> dict:
    """Update service information."""
    success = await registry.update_service(service_id, update)
    if not success:
        raise HTTPException(status_code=404, detail="Service not found")

    return {"message": f"Service '{service_id}' updated successfully"}


@router.get("/services/{service_id}", response_model=ServiceInfo)
async def get_service(
    service_id: str, registry: ServiceRegistry = Depends(get_service_registry)
) -> ServiceInfo:
    """Get service information by ID."""
    service = await registry.get_service(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    return service


@router.get("/services/name/{service_name}", response_model=ServiceInfo)
async def get_service_by_name(
    service_name: str, registry: ServiceRegistry = Depends(get_service_registry)
) -> ServiceInfo:
    """Get service information by name."""
    service = await registry.get_service_by_name(service_name)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    return service


@router.post("/discover", response_model=ServiceDiscoveryResponse)
async def discover_services(
    query: ServiceDiscoveryQuery,
    registry: ServiceRegistry = Depends(get_service_registry),
) -> ServiceDiscoveryResponse:
    """Discover services based on query criteria."""
    return await registry.discover_services(query)


@router.get("/discover", response_model=ServiceDiscoveryResponse)
async def discover_services_get(
    service_type: str = None,
    name: str = None,
    status: str = None,
    registry: ServiceRegistry = Depends(get_service_registry),
) -> ServiceDiscoveryResponse:
    """Discover services using GET parameters."""
    query = ServiceDiscoveryQuery(service_type=service_type, name=name, status=status)
    return await registry.discover_services(query)


@router.post("/heartbeat/{service_id}")
async def heartbeat(
    service_id: str, registry: ServiceRegistry = Depends(get_service_registry)
) -> dict:
    """Record a heartbeat for a service."""
    success = await registry.heartbeat(service_id)
    if not success:
        raise HTTPException(status_code=404, detail="Service not found")

    return {"message": "Heartbeat recorded"}


@router.get("/stats", response_model=RegistryStats)
async def get_registry_stats(
    registry: ServiceRegistry = Depends(get_service_registry),
) -> RegistryStats:
    """Get registry statistics."""
    return registry.get_registry_stats()


@router.post("/cleanup")
async def cleanup_stale_services(
    registry: ServiceRegistry = Depends(get_service_registry),
) -> dict:
    """Manually trigger cleanup of stale services."""
    cleaned_count = await registry.cleanup_stale_services()
    return {
        "message": f"Cleaned up {cleaned_count} stale services",
        "cleaned_count": cleaned_count,
    }


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint for the service registry itself."""
    return {"status": "healthy", "service": "service-registry"}
