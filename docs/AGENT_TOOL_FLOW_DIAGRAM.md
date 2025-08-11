# Agent Tool Calling Flow Diagram

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            AGENT TOOL ECOSYSTEM                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐  │
│  │   USER CHAT     │    │ SERVICE REGISTRY│    │    EXTERNAL TOOLS       │  │
│  │                 │    │  (Zookeeper)    │    │                         │  │
│  │ ┌─────────────┐ │    │                 │    │ ┌─────────────────────┐ │  │
│  │ │"Calculate   │ │    │ ┌─────────────┐ │    │ │ ┌─────────────────┐ │ │  │
│  │ │ 2+2*3"      │ │    │ │Service      │ │    │ │ │   Calculator    │ │ │  │
│  │ └─────────────┘ │    │ │Discovery    │ │    │ │ │   API           │ │ │  │
│  │       │         │    │ │             │ │    │ │ └─────────────────┘ │ │  │
│  │       v         │    │ │Health       │ │    │ │ ┌─────────────────┐ │ │  │
│  │ ┌─────────────┐ │    │ │Monitoring   │ │    │ │ │   Web Scraper   │ │ │  │
│  │ │Agent        │◄┼────┤ │             │◄┼────┤ │ │   API           │ │ │  │
│  │ │Response     │ │    │ │Registration │ │    │ │ └─────────────────┘ │ │  │
│  │ │"Result: 8"  │ │    │ │Management   │ │    │ │ ┌─────────────────┐ │ │  │
│  │ └─────────────┘ │    │ └─────────────┘ │    │ │ │   Search        │ │ │  │
│  └─────────────────┘    └─────────────────┘    │ │ │   Messages API  │ │ │  │
│           │                       ▲            │ │ └─────────────────┘ │ │  │
│           v                       │            │ └─────────────────────┘ │  │
│  ┌─────────────────┐              │            └─────────────────────────┘  │
│  │  AGENT SERVICE  │              │                         ▲              │
│  │  (Port 3004)    │              │                         │              │
│  │                 │              │            Auto-Registration           │
│  │ ┌─────────────┐ │              │                         │              │
│  │ │Agent Manager│ │              │                         │              │
│  │ │             │ │     Discovery & Tool Loading           │              │
│  │ │┌───────────┐│ │              │                         │              │
│  │ ││LangGraph  ││ │              │            ┌─────────────────────────┐  │
│  │ ││Agent      ││ │              │            │    TOOL EXECUTION       │  │
│  │ ││           ││ │              │            │                         │  │
│  │ ││┌─────────┐││ │              │            │ 1. Agent decides to     │  │
│  │ │││Dynamic  │││ │              │            │    use calculator       │  │
│  │ │││Tools    │││ │              │            │                         │  │
│  │ │││         │││ │              │            │ 2. HTTP call to         │  │
│  │ │││Calculator│││◄┼──────────────┘            │    /tools/calculator/   │  │
│  │ │││Scraper   │││ │                           │    calculate            │  │
│  │ │││Search    │││ │                           │                         │  │
│  │ │└─────────┘││ │                           │ 3. Tool processes        │  │
│  │ │└───────────┘│ │                           │    "2+2*3" = 8          │  │
│  │ └─────────────┘ │                           │                         │  │
│  └─────────────────┘                           │ 4. Return result to     │  │
│                                                 │    agent                │  │
│                                                 └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Detailed Tool Discovery Process

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TOOL DISCOVERY SEQUENCE                              │
└─────────────────────────────────────────────────────────────────────────────┘

 EXT-TOOL SERVICE           SERVICE REGISTRY          AGENT SERVICE
       │                          │                         │
       │ 1. POST /api/v1/register │                         │
       ├─────────────────────────►│                         │
       │                          │                         │
       │ 2. Registration OK       │                         │
       │◄─────────────────────────┤                         │
       │                          │                         │
       │ 3. Periodic Heartbeat    │                         │
       ├─────────────────────────►│                         │
       │                          │                         │
       │                          │ 4. GET /api/v1/discover │
       │                          │◄────────────────────────┤
       │                          │                         │
       │                          │ 5. List of tool services│
       │                          ├────────────────────────►│
       │                          │                         │
       │ 6. GET /tools/*/spec     │                         │
       │◄─────────────────────────┼─────────────────────────┤
       │                          │                         │
       │ 7. Tool specifications   │                         │
       ├─────────────────────────►┼────────────────────────►│
       │                          │                         │
       │                          │ 8. Creates LangChain    │
       │                          │    Tool objects         │
       │                          │                         │
```

## Agent Tool Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TOOL EXECUTION FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┘

    USER INPUT               AGENT PROCESSING            TOOL EXECUTION
        │                          │                          │
        │ "Calculate 2+2*3"        │                          │
        ├─────────────────────────►│                          │
        │                          │                          │
        │                          │ 1. Parse intent          │
        │                          │    Need: calculation     │
        │                          │                          │
        │                          │ 2. Select tool:         │
        │                          │    "calculator"          │
        │                          │                          │
        │                          │ 3. Call tool function   │
        │                          ├─────────────────────────►│
        │                          │    {"expression":"2+2*3"}│
        │                          │                          │
        │                          │                          │ 4. HTTP POST
        │                          │                          │    /calculate
        │                          │                          │    
        │                          │                          │ 5. Process math
        │                          │                          │    2+2*3 = 8
        │                          │                          │
        │                          │ 6. Return result         │
        │                          │◄─────────────────────────┤
        │                          │    {"result": 8}         │
        │                          │                          │
        │                          │ 7. Generate response     │
        │                          │    "The result is 8"     │
        │                          │                          │
        │ "The result is 8"        │                          │
        │◄─────────────────────────┤                          │
        │                          │                          │
```

## Dynamic Tool Loading Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DYNAMIC TOOL LOADING                                   │
└─────────────────────────────────────────────────────────────────────────────┘

  AGENT STARTUP                RUNTIME REFRESH               NEW TOOL ADDED
       │                           │                             │
       │ 1. Initialize             │ 1. /tools/refresh           │ 1. New tool service
       │    AgentManager           │    endpoint called          │    deployed
       │                           │                             │
       │ 2. Load dynamic           │ 2. Query service            │ 2. Auto-registers
       │    tools                  │    registry                 │    with registry
       │                           │                             │
       │ 3. Create LangChain       │ 3. Discover new/            │ 3. Agent refresh
       │    Tool objects           │    updated tools            │    discovers it
       │                           │                             │
       │ 4. Create ReAct           │ 4. Recreate all            │ 4. Available for
       │    agents with tools      │    agents with new tools    │    immediate use
       │                           │                             │
       v                           v                             v
   Ready for use              Ready with updates           New capability
```

## Tool Registration Data Flow

```json
{
  "service_registration": {
    "name": "ext-tool",
    "service_type": "tool", 
    "host": "ext-tool-container",
    "port": 3006,
    "metadata": {
      "description": "External tools service",
      "capabilities": ["calculation", "scraping", "search"],
      "available_tools": [
        "/tools/calculator",
        "/tools/scraper", 
        "/tools/search-messages"
      ]
    },
    "health_check": {
      "endpoint": "/health",
      "interval_seconds": 30
    }
  }
}
```

## LangChain Tool Creation

```python
# How external HTTP tools become LangChain tools

# 1. Service Discovery
services = await discovery_client.discover_tool_services()

# 2. For each tool service, create HTTP wrapper
for service in services:
    for tool_path in service.available_tools:
        
        # 3. Create async HTTP function
        async def http_tool_call(input_data):
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{service.base_url}{tool_path}/process",
                    json={"input": input_data}
                )
                return response.json()
        
        # 4. Wrap in LangChain Tool
        tool = Tool(
            name=tool_name,
            description=tool_description, 
            func=http_tool_call
        )
        
        # 5. Add to agent's tool list
        agent_tools.append(tool)

# 6. Create ReAct agent with all tools
agent = create_react_agent(tools=agent_tools, model=llm)
```

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ERROR HANDLING                                     │
└─────────────────────────────────────────────────────────────────────────────┘

 SCENARIO 1: Tool Service Down       SCENARIO 2: Invalid Input
        │                                   │
        │ 1. Agent calls tool               │ 1. Agent calls tool with
        │                                   │    invalid parameters
        │ 2. HTTP connection fails          │
        │                                   │ 2. Tool validates input
        │ 3. Tool wrapper catches           │
        │    connection error               │ 3. Returns error response
        │                                   │    {"success": false, 
        │ 4. Returns error to agent         │     "error": "Invalid input"}
        │    "Tool unavailable"             │
        │                                   │ 4. Agent receives error
        │ 5. Agent continues without        │
        │    tool or tries alternative      │ 5. Agent explains issue
        │                                   │    to user or retries
        │ 6. Graceful degradation           │
        │                                   │ 6. User gets helpful
        │                                   │    error message
```

This architecture enables:
- **Dynamic Discovery**: Tools are discovered at runtime
- **Fault Tolerance**: System continues if tools fail  
- **Scalability**: Easy to add new tools and instances
- **Flexibility**: Tools can be updated independently
- **Monitoring**: Health checks and service registry provide visibility
