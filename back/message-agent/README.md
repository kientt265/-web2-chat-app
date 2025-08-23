# Message Agent Service

A FastAPI-based microservice for intelligent message retrieval and conversation analysis using LangGraph workflows and Google Gemini AI.

## 🚀 Features

- **Intelligent Message Retrieval**: LangGraph-powered workflows for complex message processing
- **Semantic Search**: Find similar messages using sentence embeddings and ChromaDB
- **AI-Powered Responses**: Google Gemini AI integration for intelligent conversation analysis
- **Recent Messages**: Get the most recent messages from conversations
- **Workflow Orchestration**: LangGraph state management for complex query processing
- **Health Monitoring**: Health checks and service statistics
- **ChromaDB Integration**: Vector database for fast message retrieval
- **Graceful Fallbacks**: Works with or without AI API keys

## 🤖 AI Agent Capabilities

### LangGraph Workflow
- **Parse Query**: Intelligent intent classification and query analysis
- **Search Messages**: Semantic search and recent message retrieval  
- **Retrieve Context**: Format and structure conversation context
- **Generate Response**: AI-powered response generation with Gemini

### Supported Query Types
- "Find messages about project updates"
- "Show me recent messages"
- "What did John say about the meeting?"
- "Search for messages containing 'deadline'"
- "Tell me about the latest discussions"

## 🔌 API Endpoints

### Health & Info
- `GET /` - Service information
- `GET /health` - Health check
- `GET /stats` - Service statistics

### AI Agent Operations
- `POST /api/v1/agent/query` - Process natural language queries with AI
- `GET /api/v1/agent/status/{session_id}` - Get agent processing status
- `DELETE /api/v1/agent/cleanup/{session_id}` - Cleanup agent session

### Message Operations (Direct Access)
- `GET /api/v1/messages/` - Get messages with optional filters
- `POST /api/v1/messages/search` - Semantic search for messages
- `GET /api/v1/messages/recent` - Get recent messages
- `GET /api/v1/messages/{message_id}` - Get specific message by ID
- `GET /api/v1/messages/conversation/{conversation_id}` - Get all messages from a conversation

## ⚙️ Configuration

Environment variables:
- `MESSAGE_AGENT_PORT`: Service port (default: 3008)
- `GOOGLE_API_KEY`: Google Gemini API key (optional, enables AI responses)
- `CHROMADB_HOST`: ChromaDB host (default: chromadb)
- `CHROMADB_PORT`: ChromaDB port (default: 8000)
- `LOG_LEVEL`: Logging level (default: INFO)

## Usage

### Basic Message Retrieval
```bash
curl http://localhost:3008/api/v1/messages/?limit=10&offset=0
```

### Semantic Search
```bash
curl -X POST http://localhost:3008/api/v1/messages/search \
  -H "Content-Type: application/json" \
  -d '{"query": "hello world", "limit": 5}'
```

### Get Conversation Messages
```bash
curl http://localhost:3008/api/v1/messages/conversation/conv-123?limit=50
```

### Get Recent Messages
```bash
curl http://localhost:3008/api/v1/messages/recent?limit=20
```

## Docker

The service runs on port 3008 externally and connects to ChromaDB for message storage.

## Dependencies

- FastAPI for web framework
- ChromaDB for vector database operations
- Sentence Transformers for text embeddings
- Pydantic for data validation

## Development

1. Install dependencies: `pip install -r requirements.txt`
2. Run the service: `python main.py`
3. Access API docs at: `http://localhost:3008/docs`
