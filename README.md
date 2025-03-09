# FastAPI-MCP

A zero-configuration tool for integrating Model Context Protocol (MCP) servers with FastAPI applications.

[![PyPI version](https://badge.fury.io/py/fastapi-mcp.svg)](https://pypi.org/project/fastapi-mcp/)
[![Python Versions](https://img.shields.io/pypi/pyversions/fastapi-mcp.svg)](https://pypi.org/project/fastapi-mcp/)

## Features

- **Direct integration** - Mount an MCP server directly to your FastAPI app
- **Zero configuration** required - just point it at your FastAPI app and it works
- **Automatic discovery** of all FastAPI endpoints and conversion to MCP tools
- **Type-safe conversion** from FastAPI endpoints to MCP tools
- **Documentation preservation** from FastAPI to MCP
- **Custom tools** - Add custom MCP tools alongside your API endpoints

## Installation

You can install FastAPI-MCP directly from [PyPI](https://pypi.org/project/fastapi-mcp/):

```bash
pip install fastapi-mcp
```

For detailed installation instructions and alternative methods, see [INSTALL.md](INSTALL.md).

## Usage

### Direct integration (Recommended)

The simplest way to use FastAPI-MCP is to add an MCP server directly to your FastAPI application:

```python
from fastapi import FastAPI
from fastapi_mcp import add_mcp_server

# Create your FastAPI app
app = FastAPI()

# Define your endpoints...
@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    """Get details for a specific item"""
    return {"item_id": item_id, "q": q}

# Add an MCP server to your app
mcp_server = add_mcp_server(
    app,                    # Your FastAPI app
    mount_path="/mcp",      # Where to mount the MCP server
    name="My API MCP",      # Name for the MCP server
    base_url="http://localhost:8000"  # Base URL for API requests
)

# Optionally add custom MCP tools
@mcp_server.tool()
async def get_item_count() -> int:
    """Get the total number of items in the database."""
    return 42  # Your custom implementation
```

Your FastAPI app will now have an MCP server mounted at the specified path, with all your API endpoints available as MCP tools.

### Legacy CLI Usage

The CLI is still available for backward compatibility:

```bash
# Generate an MCP server from a FastAPI app
fastapi-mcp generate app.py

# Preview the generated server
fastapi-mcp preview

# Run the generated server
fastapi-mcp run

# Install the server for Claude
fastapi-mcp install
```

## How It Works

FastAPI-MCP:

1. Takes your FastAPI application
2. Creates an MCP server instance
3. Mounts the MCP server to your FastAPI app
4. Extracts endpoint information from your OpenAPI schema
5. Creates MCP tools that make HTTP requests to your API endpoints
6. Preserves documentation and type information
7. Registers the tools with the MCP server

## Examples

See the [examples](examples) directory for complete examples.

### Simple direct integration example:

```python
from fastapi import FastAPI
from fastapi_mcp import add_mcp_server

app = FastAPI(title="Simple API")

@app.get("/hello/{name}")
async def hello(name: str):
    """Say hello to someone"""
    return {"message": f"Hello, {name}!"}

# Add MCP server
mcp_server = add_mcp_server(app, mount_path="/mcp")

# Optionally add custom tools
@mcp_server.tool()
async def get_current_time():
    """Get the current server time"""
    from datetime import datetime
    return datetime.now().isoformat()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

## Connecting to the MCP Server

Once your FastAPI app with MCP integration is running, you can connect to it with any MCP client, such as Claude:

1. Run your application
2. In Claude, use the URL of your MCP server endpoint (e.g., `http://localhost:8000/mcp`)
3. Claude will discover all available tools and resources automatically

## Advanced Configuration

FastAPI-MCP provides several options for advanced configuration:

```python
mcp_server = add_mcp_server(
    app,
    mount_path="/mcp",
    name="My Custom MCP Server",
    description="Custom description for the MCP server",
    capabilities={"streaming": True},  # Set MCP capabilities
    serve_tools=True,  # Whether to serve API endpoints as MCP tools
    base_url="https://api.example.com"  # Base URL for API requests
)
```

You can also create and mount an MCP server separately:

```python
from fastapi_mcp import create_mcp_server, mount_mcp_server

# Create an MCP server
mcp_server = create_mcp_server(app, name="My MCP Server")

# Add custom tools
@mcp_server.tool()
async def custom_tool():
    return "Custom tool result"

# Mount the MCP server to the FastAPI app
mount_mcp_server(app, mcp_server, mount_path="/mcp")
```

## Requirements

- Python 3.10+
- FastAPI 0.100.0+
- Pydantic 2.0.0+
- MCP 1.3.0+

## Contributing

Contributions are welcome! Please feel free to submit a pull request. See [CONTRIBUTING.md](CONTRIBUTING.md) for more information.

## License

MIT License. Copyright (c) 2024 Tadata Inc.

## About

Developed and maintained by [Tadata Inc.](https://github.com/tadata-org)
