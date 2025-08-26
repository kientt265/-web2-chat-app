# Model Context Protocol (MCP) Integration

This document describes how the tool-agent integrates with Model Context Protocol (MCP) servers to provide additional tools and capabilities.

## What is MCP?

Model Context Protocol (MCP) is an open standard for connecting AI assistants to external systems and data sources. It enables secure, controlled access to resources like files, databases, APIs, and services.

## Architecture

The tool-agent now exclusively uses MCP servers for all tool functionality:

1. **Static Tools**: Built-in tools defined in the codebase (if any)
2. **MCP Tools**: All tools loaded from MCP servers using the Model Context Protocol

The previous dynamic tool discovery system has been replaced with a comprehensive MCP-based architecture.

```
┌─────────────────┐    ┌─────────────────┐
│   Tool Agent    │    │  MCP Servers    │
│                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │Agent        │ │    │ │ Calculator  │ │
│ │Manager      │ │◄──►│ │ Server      │ │
│ │             │ │    │ └─────────────┘ │
│ │┌───────────┐│ │    │ ┌─────────────┐ │
│ ││Static     ││ │    │ │ Web Scraper │ │
│ ││Tools      ││ │    │ │ Server      │ │
│ │└───────────┘│ │    │ └─────────────┘ │
│ │┌───────────┐│ │    │ ┌─────────────┐ │
│ ││MCP Tools  ││ │    │ │ Filesystem  │ │
│ │└───────────┘│ │    │ │ Server      │ │
│ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    │ ┌─────────────┐ │
                       │ │ Git Server  │ │
                       │ └─────────────┘ │
                       │ ┌─────────────┐ │
                       │ │ Custom      │ │
                       │ │ MCP Server  │ │
                       │ └─────────────┘ │
                       └─────────────────┘
```

## Features

### MCP Client Capabilities
- **Protocol Support**: Implements MCP specification for tool discovery and execution
- **Transport Methods**: Supports both stdio and HTTP transport for MCP servers
- **Error Handling**: Robust error handling with fallback mechanisms
- **Async Operations**: Fully asynchronous MCP operations for better performance

### Tool Integration
- **Automatic Discovery**: MCP tools are automatically discovered and loaded at startup
- **LangChain Compatibility**: MCP tools are converted to LangChain tools for agent use
- **Dynamic Refresh**: Tools can be refreshed without restarting the service
- **Configuration Management**: Server configurations stored in JSON files

## Configuration

### MCP Server Configuration

MCP servers are configured in `config/mcp_servers.json`:

```json
{
  "servers": [
    {
      "name": "calculator",
      "command": ["bash", "./mcp_servers/run_calculator.sh"],
      "args": [],
      "env": {
        "CALCULATOR_SERVICE_URL": "http://ext-tool:3005/tools/calculator"
      },
      "url": null
    },
    {
      "name": "webscraper", 
      "command": ["bash", "./mcp_servers/run_webscraper.sh"],
      "args": [],
      "env": {
        "SCRAPER_SERVICE_URL": "http://ext-tool:3005/tools/scraper"
      },
      "url": null
    },
  ]
}
```

### Settings Configuration

General settings in `config/settings.json`:

```json
{
  "service_registry_url": "http://service-registry:3003",
  "mcp_timeout": 30,
  "max_tools_per_server": 50,
  "enable_mcp": true,
  "google_api_key": null
}
```

### Environment Variables

- `ENABLE_MCP`: Enable/disable MCP integration (default: true)
- `MCP_TIMEOUT`: Timeout for MCP operations in seconds (default: 30)
- `MAX_TOOLS_PER_SERVER`: Maximum tools to load per MCP server (default: 50)

## Available MCP Servers

### Built-in MCP Servers

The system now includes custom MCP servers for the previously dynamic tools:

1. **Calculator Server** (`mcp_servers/calculator_server.py`)
   - **Purpose**: Mathematical calculations, statistics, unit conversions
   - **Tools**: calculate, calculate_statistics, convert_units, list_math_functions
   - **Configuration**: Connects to ext-tool service for calculations

2. **Web Scraper Server** (`mcp_servers/webscraper_server.py`)
   - **Purpose**: Web scraping and content extraction
   - **Tools**: scrape_webpage, extract_text
   - **Configuration**: Connects to ext-tool service for scraping operations

3. **Filesystem Server**
   - **Purpose**: File system operations (read, write, list files)
   - **Installation**: `npm install @modelcontextprotocol/server-filesystem`
   - **Configuration**: Set root directory in args

4. **Git Server**
   - **Purpose**: Git repository operations
   - **Installation**: `npm install @modelcontextprotocol/server-git`
   - **Configuration**: Set repository path in args

### Third-party Servers

Popular MCP servers you can integrate:

- **Database Servers**: PostgreSQL, MySQL, SQLite
- **Cloud Providers**: AWS, Google Cloud, Azure
- **APIs**: REST API client, GraphQL client
- **Development Tools**: Docker, Kubernetes

## API Endpoints

### Get MCP Status
```
GET /api/v1/mcp/status
```

Returns status of all configured MCP servers.

### Add MCP Server
```
POST /api/v1/mcp/add-server
```

Add a new MCP server configuration dynamically.

Request body:
```json
{
  "name": "my-server",
  "command": ["node", "server.js"],
  "args": ["--port", "8080"],
  "env": {"API_KEY": "secret"},
  "url": null
}
```

### Refresh Tools
```
POST /api/v1/tools/refresh
```

Refresh all tools including MCP tools.

## Usage Examples

### Using MCP Tools via Agent

Once MCP servers are configured, their tools become available to the agent:

```
User: "List files in the /tmp directory"
Agent: Uses filesystem MCP tool to list files

User: "What's the latest commit in this repository?"
Agent: Uses git MCP tool to get commit information

User: "Create a new file with some content"
Agent: Uses filesystem MCP tool to create the file
```

### Adding Custom MCP Server

1. Create your MCP server following the MCP specification
2. Add configuration to `mcp_servers.json`
3. Restart the tool-agent or call the refresh endpoint
4. Tools from your server are now available to the agent

## Installation Requirements

### Installation Requirements

### For Process-based MCP Servers
```bash
# Install Node.js (required for npm packages)
# On macOS:
brew install node

# Install external MCP servers
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @modelcontextprotocol/server-git

# Python MCP package is installed automatically via requirements.txt
```

### For HTTP-based MCP Servers
No additional installation required, just configure the URL.

## Troubleshooting

### Common Issues

1. **MCP Server Not Found**
   - Ensure the command is in PATH
   - Check if required packages are installed
   - Verify command syntax in configuration

2. **Permission Errors**
   - Check file system permissions for filesystem server
   - Ensure proper access rights for git repositories

3. **Connection Timeouts**
   - Increase MCP_TIMEOUT setting
   - Check if server process is hanging

### Debug Mode

Enable debug logging to see MCP communication:
```bash
export LOG_LEVEL=DEBUG
```

### Health Checks

Check MCP server status:
```bash
curl http://localhost:3004/api/v1/mcp/status
```

## Security Considerations

1. **Sandboxing**: MCP servers should run in sandboxed environments
2. **Access Control**: Limit filesystem access to specific directories
3. **Authentication**: Use secure authentication for external MCP servers
4. **Input Validation**: MCP tools validate all input parameters
5. **Network Security**: Use HTTPS for HTTP-based MCP servers

## Best Practices

1. **Error Handling**: Always implement graceful error handling
2. **Resource Management**: Set reasonable limits on tool usage
3. **Monitoring**: Monitor MCP server health and performance
4. **Documentation**: Document custom MCP tools clearly
5. **Testing**: Test MCP integration thoroughly before deployment

## Contributing

When adding new MCP server support:

1. Add configuration schema if needed
2. Update documentation
3. Add integration tests
4. Consider security implications
5. Update API documentation
