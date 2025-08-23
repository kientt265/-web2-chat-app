"""
Message Agent Models

This module contains the data models used by the Message Agent service.
"""

from .api import (
    MessageResponse, 
    MessageResult, 
    HealthResponse,
    SemanticSearchRequest,
)

__all__ = [
    "MessageResponse",
    "MessageResult",
    "HealthResponse",
    "SemanticSearchRequest"
]