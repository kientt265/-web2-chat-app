"""Data models for service registry."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class ServiceStatus(str, Enum):
    """Service status enumeration."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"
    UNKNOWN = "unknown"


class ServiceType(str, Enum):
    """Service type enumeration."""
    AGENT = "agent"
    TOOL = "tool"
    API = "api"
    DATABASE = "database"
    GATEWAY = "gateway"
    OTHER = "other"


class ServiceMetadata(BaseModel):
    """Service metadata model."""
    description: Optional[str] = None
    version: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)


class HealthCheck(BaseModel):
    """Health check configuration."""
    enabled: bool = True
    endpoint: str = "/health"
    interval_seconds: int = 30
    timeout_seconds: int = 5
    retries: int = 3


class ServiceInfo(BaseModel):
    """Service information model."""
    service_id: str
    name: str
    service_type: ServiceType
    host: str
    port: int
    status: ServiceStatus = ServiceStatus.UNKNOWN
    metadata: ServiceMetadata = Field(default_factory=ServiceMetadata)
    health_check: HealthCheck = Field(default_factory=HealthCheck)
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def base_url(self) -> str:
        """Get the base URL for the service."""
        return f"http://{self.host}:{self.port}"
    
    @property
    def health_url(self) -> str:
        """Get the health check URL for the service."""
        return f"{self.base_url}{self.health_check.endpoint}"


class ServiceRegistration(BaseModel):
    """Service registration request model."""
    name: str
    service_type: ServiceType
    host: str
    port: int
    metadata: Optional[ServiceMetadata] = None
    health_check: Optional[HealthCheck] = None


class ServiceUpdate(BaseModel):
    """Service update request model."""
    status: Optional[ServiceStatus] = None
    metadata: Optional[ServiceMetadata] = None
    health_check: Optional[HealthCheck] = None


class ServiceDiscoveryQuery(BaseModel):
    """Service discovery query model."""
    service_type: Optional[ServiceType] = None
    name: Optional[str] = None
    tags: Optional[List[str]] = None
    capabilities: Optional[List[str]] = None
    status: Optional[ServiceStatus] = ServiceStatus.HEALTHY


class ServiceDiscoveryResponse(BaseModel):
    """Service discovery response model."""
    services: List[ServiceInfo]
    total_count: int
    query: ServiceDiscoveryQuery


class RegistryStats(BaseModel):
    """Service registry statistics."""
    total_services: int
    services_by_type: Dict[ServiceType, int]
    services_by_status: Dict[ServiceStatus, int]
    healthy_services: int
    unhealthy_services: int
