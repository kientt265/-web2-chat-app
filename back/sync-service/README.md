# Chat Sync Service

A production-ready microservice for syncing chat data from PostgreSQL to ChromaDB using Change Data Capture (CDC) via Debezium.

## 🏗️ Architecture

```
sync-service/
├── config/          # Configuration management
├── core/            # Core utilities (logging, etc.)
├── services/        # Business logic services
├── models/          # Data models (Pydantic)
├── api/             # API routes and endpoints
├── processors/      # CDC event processors
└── main.py          # FastAPI application entry point
```

## 🚀 Features

- **Real-time CDC**: Captures database changes via Debezium
- **Vector Search**: Semantic search using ChromaDB and sentence transformers
- **Microservice Architecture**: Clean separation of concerns
- **Production Ready**: Comprehensive logging, error handling, health checks
- **Async Processing**: Non-blocking Kafka consumption and API endpoints

## 📦 Installation

### Using Virtual Environment

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

### Using Docker

```bash
# Build and run with docker-compose
docker-compose up sync-service -d
```

## 🔧 Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Key configuration options:

- `CHROMADB_HOST`: ChromaDB server host
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker addresses
- `EMBEDDING_MODEL_NAME`: HuggingFace model for embeddings
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## 🏃‍♂️ Running

### Development

```bash
# From project root
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 3005
```

### Production

```bash
# Using gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:3005
```

## 📚 API Endpoints

### Health Check
```bash
GET /health
```

### Service Statistics
```bash
GET /stats
```

### Semantic Search
```bash
POST /search
{
    "query": "search text",
    "conversation_id": "optional-uuid",
    "sender_id": "optional-uuid", 
    "limit": 10
}
```

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=. tests/

# Run specific test
pytest tests/test_services/test_chromadb_service.py
```

## 🐛 Debugging

### Check Service Health
```bash
curl http://localhost:3005/health
```

### Monitor Logs
```bash
# In Docker
docker logs sync-service -f

# Local development
# Logs go to stdout with structured format
```

### Verify ChromaDB Connection
```bash
curl http://localhost:8000/api/v1/heartbeat
```

### Check Kafka Topics
```bash
docker exec kafka-container kafka-topics --list --bootstrap-server localhost:9092
```

## 🔄 Development Workflow

1. **Make changes** to the code
2. **Run tests** to ensure functionality
3. **Check logs** for any issues
4. **Test API endpoints** manually or with automated tests
5. **Monitor CDC events** in Kafka

## 📊 Monitoring

The service provides several monitoring endpoints:

- `/health` - Basic health check
- `/stats` - Service statistics including document counts
- Structured logging with correlation IDs
- Kafka consumer metrics

## 🤝 Contributing

1. Follow the existing code structure
2. Add tests for new functionality
3. Use type hints throughout
4. Follow PEP 8 style guidelines
5. Update documentation as needed

## 📄 License

[Your License Here]
