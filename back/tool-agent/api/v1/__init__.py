"""
API v1 package for the agent module.

This package contains the FastAPI router and endpoint definitions for the agent module.
"""

from .endpoints import router as router_v1

if __name__ == "__main__":
    print("This is the API v1 package for the agent module.")
else:
    __all__ = ["router_v1"]
