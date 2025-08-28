# MCP Service - Restructured Architecture

## Overview

The MCP (Model Context Protocol) Service has been restructured with a clean, layered architecture that separates concerns between API handling and core business logic.

## Architecture

### Directory Structure

```
mcp-service/
├── main.py                    # FastAPI application entry point
├── config/                    # Configuration management
│   ├── __init__.py
│   └── settings.py
├── core/                      # Core service logic
│   ├── __init__.py
│   └── mcp_manager.py        # Manages multiple MCP servers
└── servers/                   # MCP servers with layered architecture
    ├── __init__.py
    ├── base/                  # Base classes for consistent architecture
    │   ├── __init__.py
    │   ├── api_base.py       # Base API handler class
    │   ├── core_base.py      # Base service class
    │   └── server_base.py    # Base MCP server class
    ├── calculator/            # Calculator server
    │   ├── __init__.py
    │   ├── server.py         # Main server class
    │   ├── api/              # API layer
    │   │   ├── __init__.py
    │   │   └── handler.py    # API request/response handling
    │   └── core/             # Core logic
    │       ├── __init__.py
    │       └── service.py    # Business logic implementation
    └── webscraper/            # Webscraper server
        ├── __init__.py
        ├── server.py         # Main server class
        ├── api/              # API layer
        │   ├── __init__.py
        │   └── handler.py    # API request/response handling
        └── core/             # Core logic
            ├── __init__.py
            └── service.py    # Business logic implementation
```

### Layer Responsibilities

#### 1. Server Layer (`server.py`)
- **Purpose**: Main server coordination and initialization
- **Responsibilities**:
  - Instantiate and coordinate API and Core layers
  - Handle server lifecycle (start/stop)
  - Provide server metadata

#### 2. API Layer (`api/handler.py`)
- **Purpose**: Handle HTTP requests and responses
- **Responsibilities**:
  - Define tool schemas and validation
  - Process incoming requests
  - Validate arguments
  - Format responses
  - Error handling and logging

#### 3. Core Layer (`core/service.py`)
- **Purpose**: Implement business logic
- **Responsibilities**:
  - Execute actual tool operations
  - Communicate with external services (ext-tool)
  - Process data and apply business rules
  - Return structured results

#### 4. Base Classes (`base/`)
- **Purpose**: Provide consistent interface and common functionality
- **Classes**:
  - `BaseMCPServer`: Common server functionality
  - `BaseAPIHandler`: Common API handling patterns
  - `BaseService`: Common service patterns (HTTP client, logging, etc.)

## Key Features

### 1. **Separation of Concerns**
- Clear boundaries between API handling and business logic
- Easier testing and maintenance
- Better code organization

### 2. **Consistent Architecture**
- All servers follow the same layered pattern
- Base classes provide common functionality
- Standardized error handling and logging

### 3. **Flexible Configuration**
- Server configurations managed centrally
- Easy to add new servers
- Environment-based configuration

### 4. **Enhanced Error Handling**
- Structured error responses
- Proper logging at each layer
- Graceful degradation

### 5. **Type Safety**
- Proper type hints throughout
- Structured data models
- Validation at API boundaries

## Usage

### Adding a New Server

1. **Create server directory structure**:
   ```bash
   mkdir -p servers/newserver/{api,core}
   ```

2. **Implement core service**:
   ```python
   # servers/newserver/core/service.py
   from base.core_base import BaseService
   
   class NewServerService(BaseService):
       async def some_operation(self, param: str) -> Dict[str, Any]:
           # Implement business logic
           pass
   ```

3. **Implement API handler**:
   ```python
   # servers/newserver/api/handler.py
   from base.api_base import BaseAPIHandler
   
   class NewServerAPIHandler(BaseAPIHandler):
       def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
           # Define tools and schemas
           pass
       
       async def handle_some_tool(self, arguments: Dict[str, Any]) -> str:
           # Handle tool calls
           pass
   ```

4. **Create main server class**:
   ```python
   # servers/newserver/server.py
   from base.server_base import BaseMCPServer
   
   class NewServer(BaseMCPServer):
       def create_service(self):
           return NewServerService(self.config)
       
       def create_api_handler(self):
           return NewServerAPIHandler(self.service)
   ```

5. **Update configuration**:
   ```python
   # config/settings.py
   "mcp_servers": [
       {
           "name": "newserver",
           "type": "layered",
           "port": 8003,
           "enabled": True,
           "config": {...}
       }
   ]
   ```

### Tool Development

Each tool should:

1. **Define schema** in API handler's `get_tool_definitions()`
2. **Implement handler** method `handle_{tool_name}()` in API handler
3. **Implement business logic** in core service
4. **Handle errors** appropriately at each layer

### Testing

The layered architecture makes testing easier:

- **Unit test core services** independently
- **Unit test API handlers** with mocked services
- **Integration test servers** end-to-end
- **Mock external dependencies** at service layer

## Benefits

1. **Maintainability**: Clear separation makes code easier to understand and modify
2. **Testability**: Each layer can be tested independently
3. **Extensibility**: Easy to add new servers and tools
4. **Reusability**: Base classes reduce code duplication
5. **Reliability**: Better error handling and logging
6. **Performance**: Efficient resource management with proper cleanup

## Migration from Old Architecture

The old monolithic server files (`calculator_server.py`, `webscraper_server.py`) have been backed up as `.bak` files. The new architecture provides the same functionality with improved organization and maintainability.
