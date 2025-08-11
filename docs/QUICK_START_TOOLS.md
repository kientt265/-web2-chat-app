# Quick Start: Adding Tools to Agent System

## TL;DR - Add a New Tool in 5 Minutes

### 1. Create Tool Structure
```bash
mkdir -p back/ext-tool/tools/my_tool
cd back/ext-tool/tools/my_tool
```

### 2. Create `service.py`
```python
from pydantic import BaseModel
from typing import Optional

class MyToolRequest(BaseModel):
    text: str

class MyToolResult(BaseModel):
    result: str
    success: bool = True
    error: Optional[str] = None

class MyToolService:
    async def process(self, request: MyToolRequest) -> MyToolResult:
        try:
            # Your logic here
            result = f"Processed: {request.text.upper()}"
            return MyToolResult(result=result)
        except Exception as e:
            return MyToolResult(result="", success=False, error=str(e))
```

### 3. Create `api.py`
```python
from fastapi import APIRouter
from .service import MyToolService, MyToolRequest, MyToolResult

router = APIRouter()
service = MyToolService()

@router.post("/process", response_model=MyToolResult)
async def process(request: MyToolRequest):
    return await service.process(request)

@router.get("/health")
async def health():
    return {"status": "healthy", "tool": "my_tool"}
```

### 4. Create `__init__.py`
```python
from .api import router
__all__ = ["router"]
```

### 5. Register in Main App
```python
# In back/ext-tool/main.py
from tools.my_tool.api import router as my_tool_router

app.include_router(my_tool_router, prefix="/tools/my-tool", tags=["my-tool"])
```

### 6. Deploy and Test
```bash
# Rebuild and restart
docker-compose build ext-tool && docker-compose up ext-tool -d

# Test tool
curl -X POST "http://localhost:3006/tools/my-tool/process" \
     -H "Content-Type: application/json" \
     -d '{"text": "hello world"}'

# Refresh agent tools
curl -X POST "http://localhost:3004/api/v1/tools/refresh"

# Verify agent has the tool
curl "http://localhost:3004/api/v1/tools"
```

## Tool Usage by Agent

Once added, the agent will automatically:
1. **Discover** your tool through service registry
2. **Create** a LangChain tool wrapper
3. **Use** the tool when relevant to user queries

Example conversation:
```
User: "Convert 'hello world' to uppercase"
Agent: [Uses my-tool] → "HELLO WORLD"
```

## Tool Template Generator

Use this script to generate a new tool quickly:

```bash
#!/bin/bash
# create_tool.sh
TOOL_NAME=$1
TOOL_DIR="back/ext-tool/tools/${TOOL_NAME}"

mkdir -p "${TOOL_DIR}"

cat > "${TOOL_DIR}/__init__.py" << EOF
from .api import router
__all__ = ["router"]
EOF

cat > "${TOOL_DIR}/service.py" << EOF
from pydantic import BaseModel
from typing import Optional, Dict, Any

class ${TOOL_NAME^}Request(BaseModel):
    input_data: str
    options: Optional[Dict[str, Any]] = {}

class ${TOOL_NAME^}Result(BaseModel):
    output: str
    success: bool = True
    error: Optional[str] = None

class ${TOOL_NAME^}Service:
    async def process(self, request: ${TOOL_NAME^}Request) -> ${TOOL_NAME^}Result:
        try:
            # TODO: Implement your tool logic here
            result = f"Processed by ${TOOL_NAME}: {request.input_data}"
            return ${TOOL_NAME^}Result(output=result)
        except Exception as e:
            return ${TOOL_NAME^}Result(output="", success=False, error=str(e))
EOF

cat > "${TOOL_DIR}/api.py" << EOF
from fastapi import APIRouter
from core.logging import get_logger
from .service import ${TOOL_NAME^}Service, ${TOOL_NAME^}Request, ${TOOL_NAME^}Result

router = APIRouter()
logger = get_logger(__name__)
service = ${TOOL_NAME^}Service()

@router.post("/process", response_model=${TOOL_NAME^}Result)
async def process(request: ${TOOL_NAME^}Request):
    return await service.process(request)

@router.get("/health")
async def health():
    return {"status": "healthy", "tool": "${TOOL_NAME}"}
EOF

echo "Tool '${TOOL_NAME}' created in ${TOOL_DIR}"
echo "Don't forget to register it in main.py!"
```

Usage:
```bash
chmod +x create_tool.sh
./create_tool.sh weather_checker
```

## Common Tool Patterns

### 1. Data Processing Tool
```python
# For text/data transformation
@router.post("/transform")
async def transform_data(data: str, operation: str):
    # Apply transformation
    return {"result": transformed_data}
```

### 2. API Client Tool
```python
# For calling external APIs
@router.get("/fetch")
async def fetch_data(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return {"data": response.json()}
```

### 3. Database Tool
```python
# For database operations
@router.get("/query")
async def query_database(sql: str):
    # Execute safe query
    return {"results": query_results}
```

### 4. File Processing Tool
```python
# For file operations
@router.post("/analyze")
async def analyze_file(file_content: str, file_type: str):
    # Process file content
    return {"analysis": analysis_results}
```

## Testing Your Tools

### Unit Tests
```python
# test_my_tool.py
import pytest
from tools.my_tool.service import MyToolService, MyToolRequest

@pytest.mark.asyncio
async def test_my_tool():
    service = MyToolService()
    request = MyToolRequest(text="test")
    result = await service.process(request)
    assert result.success
    assert "TEST" in result.result
```

### Integration Tests
```bash
# Test tool endpoint
curl -X POST "http://localhost:3006/tools/my-tool/process" \
     -H "Content-Type: application/json" \
     -d '{"text": "test input"}'

# Test agent discovery
curl "http://localhost:3004/api/v1/tools" | jq '.tools[] | select(.name=="my-tool")'
```

## Monitoring Tools

### Health Checks
All tools should implement health endpoints:
```python
@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "tool": "my_tool",
        "version": "1.0.0",
        "uptime": get_uptime()
    }
```

### Metrics
Add basic metrics to your tools:
```python
from time import time

start_time = time()
request_count = 0

@router.post("/process")
async def process(request: MyToolRequest):
    global request_count
    request_count += 1
    
    start = time()
    result = await service.process(request)
    duration = time() - start
    
    logger.info(f"Tool request completed in {duration:.2f}s")
    return result
```

## Need Help?

1. **Check logs**: `docker-compose logs ext-tool`
2. **Test service registry**: `curl http://localhost:3003/health`
3. **Verify tool registration**: `curl http://localhost:3003/api/v1/discover`
4. **Test agent tools**: `curl http://localhost:3004/api/v1/tools`

For detailed documentation, see [AGENT_TOOL_SYSTEM.md](./AGENT_TOOL_SYSTEM.md)
