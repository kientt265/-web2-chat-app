# Message Agent Service

A FastAPI-based microservice for retrieving messages from ChromaDB with semantic search capabilities.

## Features

- **Message Retrieval**: Get messages by conversation ID, sender ID, with pagination support
- **Semantic Search**: Find similar messages using sentence embeddings
- **Recent Messages**: Get the most recent messages from conversations
- **Health Monitoring**: Health checks and service statistics
- **ChromaDB Integration**: Connects to ChromaDB vector database for fast retrieval

## API Endpoints

### Health & Info
- `GET /` - Service information
- `GET /health` - Health check
- `GET /stats` - Service statistics

### Message Operations
- `GET /api/v1/messages/` - Get messages with optional filters
- `POST /api/v1/messages/search` - Semantic search for messages
- `GET /api/v1/messages/recent` - Get recent messages
- `GET /api/v1/messages/{message_id}` - Get specific message by ID
- `GET /api/v1/messages/conversation/{conversation_id}` - Get all messages from a conversation

## Configuration

Environment variables:
- `MESSAGE_AGENT_PORT`: Service port (default: 3008)
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
