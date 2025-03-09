# FastAPI-MCP Examples

This directory contains examples of using FastAPI-MCP to integrate Model Context Protocol (MCP) servers with FastAPI applications.

## Examples

### `simple_integration.py`

Demonstrates the direct integration approach, where an MCP server is mounted directly to a FastAPI application.

Features:
- FastAPI app with CRUD operations for items
- MCP server mounted at `/mcp`
- Automatic conversion of API endpoints to MCP tools
- Custom MCP tool not based on an API endpoint

To run this example:

```bash
# From the examples directory
python run_example.py

# Or directly
uvicorn simple_integration:app --reload
```

Then visit:
- API documentation: http://localhost:8000/docs
- MCP server endpoint: http://localhost:8000/mcp

### `sample_app.py`

Original example app to demonstrate the legacy code generation approach.

To use with the CLI:

```bash
# Generate MCP server
fastapi-mcp generate sample_app.py

# Preview the generated server
fastapi-mcp preview

# Run the sample app
uvicorn sample_app:app --reload

# In another terminal, run the MCP server
fastapi-mcp run
```

## Using with Claude

To connect Claude to your MCP server:

1. Run any of the examples above
2. In Claude, use the URL of your MCP server (e.g., `http://localhost:8000/mcp`)
3. Claude will discover the available tools and resources automatically

## What's Next?

These examples demonstrate the basic functionality of FastAPI-MCP. For more advanced use cases, you can:

- Add authentication to your API endpoints
- Customize the MCP server with additional capabilities
- Add custom MCP tools that go beyond your API functionality
- Deploy your integrated app to a production environment 