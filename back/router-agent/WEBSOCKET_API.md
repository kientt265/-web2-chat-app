# Router Agent WebSocket API

The Router Agent service provides WebSocket support for real-time communication with intelligent query routing capabilities.

## WebSocket Endpoint

```
ws://localhost:3007/api/v1/ws
```

## Connection

Connect to the WebSocket endpoint using any WebSocket client. Upon connection, you'll receive a welcome message:

```json
{
  "type": "connection",
  "data": {
    "status": "connected",
    "connection_id": "uuid-here",
    "message": "Welcome to Router Agent WebSocket"
  },
  "timestamp": "2025-08-17T10:30:00.000Z"
}
```

## Message Format

All messages sent to and received from the WebSocket follow this format:

```json
{
  "type": "message_type",
  "data": { ... },
  "message_id": "optional-message-id",
  "session_id": "optional-session-id",
  "timestamp": "2025-08-17T10:30:00.000Z"
}
```

## Supported Message Types

### 1. Ping (`ping`)

Health check message.

**Request:**
```json
{
  "type": "ping",
  "data": {},
  "message_id": "ping-123"
}
```

**Response:**
```json
{
  "type": "pong",
  "data": { "message": "pong" },
  "message_id": "ping-123",
  "timestamp": "2025-08-17T10:30:00.000Z"
}
```

### 2. Query Processing (`query`)

Route and process a user query through the intelligent routing system.

**Request:**
```json
{
  "type": "query",
  "data": {
    "message": "Calculate the square root of 144",
    "force_agent": "tool-agent"  // Optional: force specific agent
  },
  "session_id": "session-123"
}
```

**Response:**
```json
{
  "type": "response",
  "data": {
    "response": "The square root of 144 is 12.",
    "routed_to": "tool-agent",
    "session_id": "session-123",
    "query": "Calculate the square root of 144",
    "routing_confidence": 0.95,
    "routing_reasoning": "Query contains mathematical calculation",
    "routing_method": "llm-based"
  },
  "processing_time_ms": 245.7,
  "timestamp": "2025-08-17T10:30:00.000Z"
}
```

### 3. Query Analysis (`analyze`)

Analyze a query to understand routing decisions without processing it.

**Request:**
```json
{
  "type": "analyze",
  "data": {
    "message": "What did we discuss yesterday about the project?"
  }
}
```

**Response:**
```json
{
  "type": "analysis",
  "data": {
    "query": "What did we discuss yesterday about the project?",
    "recommended_agent": "message-history-agent",
    "confidence": 0.88,
    "reasoning": "Query asks about past conversation history",
    "method": "llm-based",
    "alternative_agents": ["tool-agent", "general-agent"]
  },
  "timestamp": "2025-08-17T10:30:00.000Z"
}
```

### 4. Status Check (`status`)

Get current router status and available agents.

**Request:**
```json
{
  "type": "status",
  "data": {}
}
```

**Response:**
```json
{
  "type": "status",
  "data": {
    "status": "healthy",
    "available_agents": [
      {
        "type": "tool-agent",
        "description": "Handles queries requiring external tools",
        "endpoint": "http://localhost:3004/api/v1/process"
      }
    ],
    "llm_available": true,
    "routing_method": "llm-based",
    "active_connections": 3,
    "active_sessions": 2
  },
  "timestamp": "2025-08-17T10:30:00.000Z"
}
```

### 5. Direct Agent Call (`direct`)

Call a specific agent directly, bypassing the routing logic.

**Request:**
```json
{
  "type": "direct",
  "data": {
    "agent_type": "tool-agent",
    "message": "Calculate 25 * 4"
  }
}
```

**Response:**
```json
{
  "type": "response",
  "data": {
    "response": "25 * 4 = 100",
    "routed_to": "tool-agent",
    "session_id": "session-123",
    "query": "Calculate 25 * 4",
    "direct_call": true
  },
  "timestamp": "2025-08-17T10:30:00.000Z"
}
```

## Available Agents

- **tool-agent**: Handles calculations, web scraping, external tools
- **message-history-agent**: Handles conversation history and message search
- **general-agent**: Handles general conversation and other queries

## Error Handling

Errors are returned with type `error`:

```json
{
  "type": "error",
  "data": {
    "error": "Invalid message format",
    "details": "Missing required field: message",
    "code": "VALIDATION_ERROR"
  },
  "timestamp": "2025-08-17T10:30:00.000Z"
}
```

## Error Codes

- `VALIDATION_ERROR`: Invalid message format or missing required fields
- `JSON_ERROR`: Invalid JSON format
- `UNKNOWN_MESSAGE_TYPE`: Unsupported message type
- `INVALID_AGENT`: Invalid agent type specified
- `MISSING_MESSAGE`: Required message field is empty
- `QUERY_ERROR`: Error processing query
- `ANALYSIS_ERROR`: Error analyzing query
- `STATUS_ERROR`: Error getting status
- `DIRECT_CALL_ERROR`: Error in direct agent call
- `INTERNAL_ERROR`: Unexpected server error

## Testing

### Python Test Client

Run the included Python test client:

```bash
# Interactive mode
python websocket_test_client.py

# Automated tests
python websocket_test_client.py auto
```

### HTML Test Client

Open `websocket_test.html` in a web browser for a GUI test interface.

### WebSocket Stats

Get WebSocket connection statistics via HTTP:

```bash
curl http://localhost:3007/api/v1/ws/stats
```

## Session Management

- Each connection can optionally specify a `session_id`
- Multiple connections can share the same session
- Session-based message broadcasting is supported
- Sessions are automatically cleaned up when all connections disconnect

## Connection Management

- Automatic connection cleanup on disconnect
- Heartbeat support via ping/pong
- Connection statistics and monitoring
- Graceful error handling and reconnection support
