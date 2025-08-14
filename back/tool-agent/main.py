"""
Main entry point for the Agent API Service.

This module sets up a FastAPI application that provides AI agent capabilities
for conversation management, tool calling, and message processing using LangChain.
"""

import uvicorn
from fastapi import FastAPI
from api.v1.endpoints import router as router_v1

app = FastAPI(
    title="Tool Agent API Service",
    description="API for tool agent microservice. See /docs for Swagger UI.",
    version="1.0.0",
    contact={"name": "KieZu Team", "email": "your@email.com"},
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/", tags=["info"])
def root():
    """Root endpoint that provides basic information about the Agent API Service."""
    return {"message": "Welcome to the Agent API Service. See /docs for Swagger UI."}


@app.get("/health", tags=["info"])
def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Agent API Service"}


app.include_router(router_v1, prefix="/api/v1", tags=["tool-agent"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3004)
