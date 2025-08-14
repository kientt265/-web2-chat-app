"""
API package for the agent module.

This package contains the FastAPI router and endpoint definitions for the agent module.
"""

from .v1.endpoints import router as router_v1

if __name__ == "__main__":
    print("This is the API package for the agent module.")
else:
    __all__ = ["router_v1"]
