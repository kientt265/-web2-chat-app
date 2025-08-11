# Service Registry with Zookeeper

This implementation provides a centralized service registry using Zookeeper for service discovery and coordination in the microservices architecture.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Agent Service │    │ Service Registry │    │ External Tools  │
│                 │◄──►│    (Zookeeper)   │◄──►│    Service      │
│  - Tool Calls   │    │                  │    │  - Calculator   │
│  - Discovery    │    │  - Registration  │    │  - Web Scraper  │
│                 │    │  - Health Check  │    │  - Search       │
└─────────────────┘    │  - Load Balance  │    └─────────────────┘
                       └──────────────────┘
                                │
                       ┌──────────────────┐
                       │   Zookeeper      │
                       │  - Coordination  │
                       │  - Service Tree  │
                       │  - Health Watch  │
                       └──────────────────┘
```

## Features

### 🔍 Service Discovery
- **Automatic Discovery**: Services automatically discover each other through the registry
- **Dynamic Tool Loading**: Agent service dynamically loads available tools from registered services
- **Load Balancing**: Client-side load balancing with random selection from healthy instances
- **Health Monitoring**: Continuous health checks with automatic failover

### 📋 Service Registration
- **Auto-Registration**: Services automatically register themselves on startup
- **Heartbeat Mechanism**: Regular heartbeat to maintain service availability
- **Graceful Shutdown**: Proper unregistration on service shutdown
- **Metadata Support**: Rich service metadata including capabilities and tags

### 🛠 Integration
- **Zookeeper Backend**: Uses Zookeeper for reliable distributed coordination
- **REST API**: Simple REST API for service management
- **Async Support**: Full async/await support for high performance
- **Error Handling**: Robust error handling and retry mechanisms

## Service Components

### 1. Service Registry (`service-registry`)
- **Port**: 3003
- **Purpose**: Central registry for all services
- **Features**:
  - Service registration and discovery
  - Health monitoring
  - Statistics and metrics
  - REST API endpoints

### 2. Agent Service (`agent`)
- **Port**: 3004  
- **Purpose**: AI agent with dynamic tool capabilities
- **Features**:
  - Dynamic tool discovery and loading
  - Tool refresh capability
  - Session management

### 3. External Tools Service (`ext-tool`)
- **Port**: 3006
- **Purpose**: Provides various tools for AI agents
- **Features**:
  - Calculator tools
  - Web scraping tools
  - Message search tools
  - Auto-registration with service registry

## API Endpoints

### Service Registry API

#### Register a Service
```http
POST /api/v1/register
Content-Type: application/json

{
  "name": "my-service",
  "service_type": "tool",
  "host": "my-service",
  "port": 8080,
  "metadata": {
    "description": "My service description",
    "capabilities": ["feature1", "feature2"]
  }
}
```

#### Discover Services
```http
POST /api/v1/discover
Content-Type: application/json

{
  "service_type": "tool",
  "status": "healthy"
}
```

#### Send Heartbeat
```http
POST /api/v1/heartbeat/{service_id}
```

### Agent API

#### Get Available Tools
```http
GET /api/v1/tools
```

#### Refresh Tools
```http
POST /api/v1/tools/refresh
```

#### Process Message
```http
POST /api/v1/process
Content-Type: application/json

{
  "session_id": "user123",
  "user_input": "Calculate 10 + 5"
}
```

## Usage Examples

### Starting the Services

1. **Start Zookeeper** (already in docker-compose.yml):
```bash
docker-compose up zookeeper
```

2. **Start Service Registry**:
```bash
docker-compose up service-registry
```

3. **Start Tool Service**:
```bash
docker-compose up ext-tool
```

4. **Start Agent Service**:
```bash
docker-compose up agent
```

### Using the Agent with Dynamic Tools

1. **Check Available Tools**:
```bash
curl http://localhost:3004/api/v1/tools
```

2. **Send a Message to Agent**:
```bash
curl -X POST http://localhost:3004/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test123", 
    "user_input": "Calculate the square root of 16"
  }'
```

3. **Refresh Tools** (after adding new services):
```bash
curl -X POST http://localhost:3004/api/v1/tools/refresh
```

### Monitoring Services

1. **Check Registry Health**:
```bash
curl http://localhost:3003/health
```

2. **View Registry Statistics**:
```bash
curl http://localhost:3003/api/v1/stats
```

3. **List All Services**:
```bash
curl http://localhost:3003/api/v1/discover
```

## Environment Variables

### Service Registry
- `SERVICE_REGISTRY_PORT`: Port for service registry (default: 3003)
- `ZOOKEEPER_HOSTS`: Zookeeper connection string (default: zookeeper:2181)
- `LOG_LEVEL`: Logging level (default: INFO)

### Agent Service  
- `AGENT_PORT`: Port for agent service (default: 3004)
- `SERVICE_REGISTRY_URL`: URL of service registry (default: http://service-registry:3003)

### External Tools Service
- `EXT_TOOL_PORT`: Port for tools service (default: 3006)
- `SERVICE_REGISTRY_URL`: URL of service registry (default: http://service-registry:3003)

## Adding New Tool Services

To add a new tool service:

1. **Create Service Registration**:
```python
from services.registration import get_registration_client

async def startup():
    client = get_registration_client()
    await client.register(
        service_name="my-new-tool",
        service_port=8080,
        service_host="my-new-tool"
    )
```

2. **Implement Tool Endpoints**:
```python
@app.get("/tools")
async def list_tools():
    return {
        "tools": [
            {
                "name": "my-tool",
                "path": "/tools/my-tool",
                "description": "My tool description"
            }
        ]
    }

@app.post("/tools/my-tool")
async def my_tool(data: dict):
    # Tool implementation
    return {"result": "tool output"}
```

3. **Add Health Check**:
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

4. **Update docker-compose.yml**:
```yaml
my-new-tool:
  build:
    context: ./my-new-tool
  environment:
    - SERVICE_REGISTRY_URL=http://service-registry:3003
  depends_on:
    - service-registry
```

## Development and Testing

### Local Development
```bash
# Start dependencies
docker-compose up zookeeper

# Start service registry locally
cd back/service-registry
python main.py

# In another terminal, start tools service
cd back/ext-tool  
python main.py

# In another terminal, start agent service
cd back/agent
python main.py
```

### Testing Service Discovery
```bash
# Test service registration
curl -X POST http://localhost:3003/api/v1/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-service",
    "service_type": "tool", 
    "host": "localhost",
    "port": 9999
  }'

# Test service discovery
curl -X POST http://localhost:3003/api/v1/discover \
  -H "Content-Type: application/json" \
  -d '{"service_type": "tool"}'
```

## Troubleshooting

### Common Issues

1. **Zookeeper Connection Failed**:
   - Check if Zookeeper is running
   - Verify `ZOOKEEPER_HOSTS` environment variable
   - Check network connectivity

2. **Service Registration Failed**:
   - Verify service registry is running
   - Check `SERVICE_REGISTRY_URL` environment variable
   - Review service registry logs

3. **Tools Not Loading**:
   - Check if tool services are registered
   - Verify tool service health endpoints
   - Try refreshing tools: `POST /api/v1/tools/refresh`

4. **Health Check Failures**:
   - Ensure `/health` endpoint returns 200 status
   - Check service logs for errors
   - Verify network connectivity

### Logs and Monitoring

- Service Registry logs: `docker-compose logs service-registry`
- Agent logs: `docker-compose logs agent`
- Tool service logs: `docker-compose logs ext-tool`
- Zookeeper logs: `docker-compose logs zookeeper`

## Production Considerations

1. **Zookeeper Cluster**: Use a Zookeeper cluster (3-5 nodes) for production
2. **Health Check Tuning**: Adjust health check intervals based on requirements
3. **Resource Limits**: Set appropriate CPU and memory limits
4. **Security**: Implement authentication and authorization for service registry
5. **Monitoring**: Add metrics collection and alerting
6. **Backup**: Regular backup of Zookeeper data

This service registry implementation provides a robust foundation for microservices coordination and enables dynamic, scalable agent-tool communication in your architecture.
