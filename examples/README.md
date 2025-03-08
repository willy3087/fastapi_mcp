# FastAPI-MCP Examples

This directory contains examples of using FastAPI-MCP to generate MCP servers from FastAPI applications.

## Sample App

The `sample_app.py` file contains a simple FastAPI application with CRUD operations for an "Item" resource.

To run the FastAPI application:

```bash
python sample_app.py
```

To generate an MCP server from the sample app:

```bash
cd ..  # Go to the root directory
python -m fastapi_mcp generate examples/sample_app.py
```

This will create a `mcp_server` directory with the generated MCP server.

To preview the generated MCP server:

```bash
python -m fastapi_mcp preview
```

To run the generated MCP server:

```bash
python -m fastapi_mcp run
```

## How It Works

1. FastAPI-MCP discovers all endpoints in the FastAPI application
2. It converts the endpoints to MCP tools
3. It generates a standalone MCP server
4. It preserves documentation and type information

The generated MCP server can be used with any MCP client, such as Claude. 