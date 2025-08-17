"""
Main entry point for the Router Agent Service.

This module sets up a FastAPI application that provides intelligent routing
of user queries to specialized agents including tool-agent and message-history-agent.
Supports both HTTP API and WebSocket connections for real-time communication.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.endpoints import router as router_v1

app = FastAPI(
    title="Router Agent Service",
    description="Intelligent routing service for directing queries to specialized agents. Supports HTTP API and WebSocket connections. See /docs for Swagger UI.",
    version="1.0.0",
    contact={"name": "KieZu Team", "email": "your@email.com"},
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["info"])
def root():
    """Root endpoint that provides basic information about the Router Agent Service."""
    return {
        "message": "Welcome to the Router Agent Service - Intelligent Query Routing",
        "description": "Routes user queries to specialized agents (tool-agent, message-history-agent, general-agent)",
        "docs": "/docs",
        "status_endpoint": "/api/v1/status",
        "websocket_endpoint": "/api/v1/ws",
        "websocket_stats": "/api/v1/ws/stats",
    }


@app.get("/health", tags=["info"])
def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Router Agent Service"}


app.include_router(router_v1, prefix="/api/v1", tags=["router"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3007)
