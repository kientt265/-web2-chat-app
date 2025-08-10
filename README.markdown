# Chat Application

This is a comprehensive real-time chat application built using a modern microservice architecture with Node.js, TypeScript, React, Python, Kafka, PostgreSQL, and integrated AI capabilities. The application features real-time messaging, semantic search, AI agents, and external tool integrations, all orchestrated with Docker for easy deployment and scalability.

## Project Overview

The application is built on a microservice architecture with the following key components:

### Core Services
- **Frontend (React)**: Modern web interface built with React, TypeScript, and Vite
- **API Gateway (Nginx)**: Centralized routing and load balancing for all microservices
- **Chat Service**: Node.js/Express microservice handling real-time chat functionality
- **Auth Service**: Authentication and user management service
- **Agent Service**: AI-powered agent for conversation assistance and automation
- **Sync Service**: Real-time data synchronization with semantic search capabilities
- **External Tool Service**: Extensible service for integrating external tools and APIs

### Infrastructure Services
- **PostgreSQL Databases**: Separate databases for chat and authentication data
- **Kafka**: Message broker for real-time event streaming
- **Zookeeper**: Kafka coordination and metadata management
- **ChromaDB**: Vector database for semantic search and AI features
- **Debezium**: Change data capture (CDC) for real-time data synchronization

### Key Features
- 🚀 **Real-time messaging** with WebSocket support
- 🔍 **Semantic search** across conversation history
- 🤖 **AI agents** for intelligent conversation assistance
- 🔧 **External tool integration** for extended functionality
- 📊 **Change data capture** for real-time data synchronization
- 🌐 **API Gateway** for centralized routing
- 🔐 **Authentication system** with secure user management
- 🐳 **Containerized deployment** with Docker Compose

## Prerequisites

To run this project, ensure you have the following installed:

- **Docker**: Version 20.10 or later
- **Docker Compose**: Version 2.0 or later
- **Node.js**: Version 18+ (for local development)
- **Python**: Version 3.11+ (for AI services development)
- **Git**: For version control

**Optional for Development:**
- **npm**: Version 8+ (for Node.js development)
- **uv** or **pip**: For Python package management

Verify your installation:
```bash
docker --version
docker-compose --version
node --version
python --version
git --version
```

## Project Structure

```
web2-chat-app/
├── front/                        # React frontend application
│   ├── src/                      # React source code
│   │   ├── components/           # Reusable UI components
│   │   ├── pages/               # Page components
│   │   ├── services/            # API service layers
│   │   └── types/               # TypeScript type definitions
│   ├── package.json             # Frontend dependencies
│   ├── vite.config.ts          # Vite build configuration
│   └── tsconfig.json           # TypeScript configuration
├── back/                        # Backend microservices
│   ├── gateway/                 # Nginx API Gateway
│   │   └── conf.d/default.conf  # Nginx routing configuration
│   ├── chat-service/           # Real-time chat service
│   │   ├── src/                # TypeScript source code
│   │   ├── prisma/             # Database schema and migrations
│   │   ├── package.json        # Node.js dependencies
│   │   └── Dockerfile          # Container configuration
│   ├── auth-service/           # Authentication service
│   │   ├── src/                # Authentication logic
│   │   ├── prisma/             # Auth database schema
│   │   └── Dockerfile          # Container configuration
│   ├── agent/                  # AI agent service
│   │   ├── main.py             # FastAPI application
│   │   ├── core/               # Agent management logic
│   │   ├── prompts/            # AI conversation prompts
│   │   └── Dockerfile          # Container configuration
│   ├── sync-service/           # Data synchronization service
│   │   ├── main.py             # FastAPI application
│   │   ├── services/           # Sync and embedding services
│   │   ├── processors/         # CDC event processors
│   │   └── Dockerfile          # Container configuration
│   └── ext-tool/               # External tool integration service
│       ├── main.py             # Tool service entry point
│       ├── tools/              # Individual tool implementations
│       └── Dockerfile          # Container configuration
├── debezium/                   # Change Data Capture configuration
│   ├── postgres-connector.json # Debezium PostgreSQL connector config
│   └── setup-cdc.sh           # CDC setup script
├── docker-compose.yml         # Multi-service orchestration
├── pyproject.toml             # Python project configuration
├── uv.lock                    # Python dependency lock file
├── Makefile                   # Build and development commands
└── README.markdown            # Project documentation
```

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/kientt265/web2-chat-app.git
cd web2-chat-app
```

### 2. Environment Setup
Create a `.env` file in the root directory:
```bash
cp .env.example .env  # If example exists, or create manually
```

Required environment variables:
```env
POSTGRES_USER=admin
POSTGRES_PASSWORD=password
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
CHROMADB_HOST=chromadb
CHROMADB_PORT=8000
```

### 3. Start All Services
Build and start the entire application stack:
```bash
docker-compose up --build -d
```

This command will:
- Build all custom service images
- Start PostgreSQL databases (chat and auth)
- Launch Kafka and Zookeeper
- Initialize ChromaDB for vector storage
- Start Debezium for change data capture
- Launch all microservices with proper networking

### 4. Verify Deployment
Check that all services are running:
```bash
docker-compose ps
```

You should see the following services:
- `api-gateway` (Port 80)
- `chat-service` (Port 3002)
- `auth-service` (Port 3001) 
- `agent` (Port 3004)
- `sync-service` (Port 3005)
- `ext-tool` (Port 3006)
- `chat-db` (Port 5434)
- `auth-db` (Port 5433)
- `kafka` (Port 9092)
- `zookeeper` (Port 2181)
- `chromadb` (Port 8000)
- `connect` (Port 8083)

### 5. Access the Application
- **Frontend**: http://localhost:5173 (if running separately)
- **API Gateway**: http://localhost/api/
- **Chat Service**: http://localhost/api/chat/
- **Auth Service**: http://localhost/api/auth/
- **Sync Service**: http://localhost:3005
- **ChromaDB**: http://localhost:8000

## Development

### Frontend Development
To run the React frontend in development mode:
```bash
cd front
npm install
npm run dev
```
The frontend will be available at http://localhost:5173

### Individual Service Development
Each microservice can be developed independently:

**Chat Service:**
```bash
cd back/chat-service
npm install
npm run dev  # Runs on port 3002
```

**Auth Service:**
```bash
cd back/auth-service
npm install
npm run dev  # Runs on port 3001
```

**AI Agent Service:**
```bash
cd back/agent
pip install -r requirements.txt
uvicorn main:app --reload --port 3004
```

**Sync Service:**
```bash
cd back/sync-service
pip install -r requirements.txt
python main.py  # Runs on port 3005
```

**External Tool Service:**
```bash
cd back/ext-tool
pip install -r requirements.txt
uvicorn main:app --reload --port 3006
```

### Service Management
```bash
# Start specific services
docker-compose up chat-service sync-service -d

# View logs
docker-compose logs -f chat-service

# Restart a service
docker-compose restart sync-service

# Stop all services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

## Database Schema

The application uses two PostgreSQL databases:

### Chat Database (`chat_db`)
- **users**: User information and profiles
- **conversations**: Chat sessions (private and group)
- **conversation_members**: User-conversation relationships
- **messages**: Chat messages with content and metadata
- **message_deliveries**: Message delivery and read status tracking

### Auth Database (`auth_db`)
- **users**: Authentication credentials and user management
- **sessions**: Active user sessions
- **permissions**: Role-based access control

### Database Management
```bash
# Connect to chat database
docker exec -it web2-chat-app-chat-db-1 psql -U admin -d chat_db

# Connect to auth database
docker exec -it web2-chat-app-auth-db-1 psql -U admin -d auth_db

# Run Prisma migrations
cd back/chat-service
npx prisma migrate dev

cd back/auth-service
npx prisma migrate dev
```

## Message Streaming & Real-time Features

### Kafka Topics
The application uses multiple Kafka topics for different message types:
- `private-chat-messages`: Direct messages between users
- `group-chat-messages`: Group conversation messages  
- `chat.cdc.messages`: Change data capture events from database
- `chat.cdc.conversations`: Conversation changes
- `chat.cdc.conversation_members`: Membership changes

### Setting Up Change Data Capture
Initialize Debezium CDC for real-time data synchronization:
```bash
# Run the CDC setup script
cd debezium
chmod +x setup-cdc.sh
./setup-cdc.sh
```

### Kafka Management
```bash
# Access Kafka container
docker exec -it web2-chat-app-kafka-1 bash

# List topics
kafka-topics.sh --list --bootstrap-server localhost:9092

# Create a new topic
kafka-topics.sh --create --topic new-topic --bootstrap-server localhost:9092 \
  --partitions 1 --replication-factor 1

# Monitor messages
kafka-console-consumer.sh --topic private-chat-messages \
  --bootstrap-server localhost:9092 --from-beginning
```

### WebSocket Connection
The frontend connects to the chat service via Socket.IO:
- **Endpoint**: `ws://localhost/socket.io/`
- **Events**: `new_message`, `user_joined`, `user_left`, `typing`
- **Rooms**: Users join conversation-specific rooms for targeted messaging

## AI Features & External Tools

### Semantic Search
The sync service provides intelligent message search:
```bash
# Search across conversations
curl -X POST http://localhost:3005/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "search terms",
    "conversation_id": "optional-uuid",
    "limit": 10
  }'
```

### AI Agent Capabilities
The agent service offers:
- **Conversation assistance**: Intelligent responses and suggestions
- **Tool integration**: Access to external APIs and services
- **Automated workflows**: Custom automation for repetitive tasks

### External Tool Integration
The ext-tool service supports:
- **Calculator**: Mathematical computations
- **Web scraper**: Content extraction from websites
- **Message search**: Historical message retrieval
- **Custom tools**: Extensible architecture for new integrations

### ChromaDB Vector Storage
Semantic search is powered by ChromaDB:
```bash
# Check ChromaDB health
curl http://localhost:8000/api/v1/heartbeat

# View collections
curl http://localhost:8000/api/v1/collections
```

## API Endpoints

### Authentication Service (Port 3001)
```bash
POST /api/auth/register    # User registration
POST /api/auth/login       # User authentication
POST /api/auth/logout      # User logout
GET  /api/auth/profile     # Get user profile
```

### Chat Service (Port 3002)
```bash
GET  /api/chat/conversations           # List user conversations
POST /api/chat/conversations           # Create new conversation
GET  /api/chat/conversations/:id       # Get conversation details
POST /api/chat/conversations/:id/messages  # Send message
GET  /api/chat/messages/:id            # Get message details
```

### Sync Service (Port 3005)
```bash
GET  /health              # Service health check
GET  /stats               # Service statistics
POST /search              # Semantic message search
```

### Agent Service (Port 3004)
```bash
POST /api/agent/chat      # Chat with AI agent
POST /api/agent/tools     # Execute tools
GET  /api/agent/health    # Agent health status
```

### External Tool Service (Port 3006)
```bash
GET  /health                    # Service health
POST /tools/calculator          # Mathematical operations
POST /tools/web-scraper         # Web content extraction
POST /tools/message-search      # Message search functionality
```

## Code Quality & Development Tools

### Makefile Commands
```bash
make lint      # Run linting across all services
make format    # Format code using Prettier/Black
make test      # Run test suites
make clean     # Clean build artifacts
```

### Testing
```bash
# Frontend tests
cd front && npm test

# Node.js service tests
cd back/chat-service && npm test

# Python service tests
cd back/sync-service && pytest
```

## Troubleshooting

### Common Issues

**Services not starting:**
```bash
# Check service logs
docker-compose logs <service-name>

# Restart specific service
docker-compose restart <service-name>

# Rebuild service
docker-compose up --build <service-name>
```

**Database connection errors:**
```bash
# Verify databases are running
docker-compose ps | grep db

# Check database logs
docker-compose logs chat-db
docker-compose logs auth-db

# Reset databases (⚠️ This will delete all data)
docker-compose down -v
docker-compose up -d
```

**Kafka/Message streaming issues:**
```bash
# Check Kafka status
docker-compose logs kafka
docker-compose logs zookeeper

# Verify topics exist
docker exec web2-chat-app-kafka-1 kafka-topics.sh --list --bootstrap-server localhost:9092

# Reset Kafka (⚠️ This will delete all messages)
docker-compose stop kafka zookeeper
docker-compose rm -f kafka zookeeper
docker-compose up -d kafka zookeeper
```

**ChromaDB/Search issues:**
```bash
# Check ChromaDB health
curl http://localhost:8000/api/v1/heartbeat

# View ChromaDB logs
docker-compose logs chromadb

# Reset ChromaDB
docker-compose stop chromadb
docker volume rm web2-chat-app_chromadb-data
docker-compose up -d chromadb
```

**Port conflicts:**
```bash
# Check what's using a port
lsof -i :PORT_NUMBER

# Kill process using port
sudo kill -9 $(lsof -t -i:PORT_NUMBER)
```

**Frontend connection issues:**
- Ensure the API Gateway is running on port 80
- Check CORS settings in service configurations
- Verify WebSocket connections to `/socket.io/`

### Performance Optimization

**Database Performance:**
- Monitor connection pools in Prisma
- Consider database indexing for frequently queried fields
- Use read replicas for analytics queries

**Kafka Performance:**
- Adjust partition counts for high-throughput topics
- Monitor consumer lag
- Configure appropriate retention policies

**ChromaDB Performance:**
- Optimize embedding model selection
- Consider batch processing for large document sets
- Monitor vector search performance

### Monitoring & Logging

**Service Health Checks:**
```bash
curl http://localhost/api/chat/health
curl http://localhost/api/auth/health  
curl http://localhost:3005/health
curl http://localhost:3004/health
curl http://localhost:3006/health
```

**Log Aggregation:**
```bash
# View all service logs
docker-compose logs -f

# Filter specific service logs
docker-compose logs -f chat-service | grep ERROR
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on:
- Adding new microservices
- Updating the API Gateway
- Database schema changes
- Testing requirements
- Code style guidelines

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

## Architecture Decisions

This project implements several architectural patterns:

- **Microservices**: Independent, scalable services
- **Event-driven**: Kafka for asynchronous communication
- **CQRS**: Separate read/write operations via CDC
- **API Gateway**: Centralized routing and load balancing
- **Containerization**: Docker for consistent deployments
- **Vector Search**: Semantic search capabilities with ChromaDB

## Support

For questions, issues, or contributions:
- **Issues**: [GitHub Issues](https://github.com/kientt265/web2-chat-app/issues)
- **Discussions**: [GitHub Discussions](https://github.com/kientt265/web2-chat-app/discussions)
- **Documentation**: See individual service README files in respective directories

---

Built with ❤️ using modern web technologies and microservice architecture.
