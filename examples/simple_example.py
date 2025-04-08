"""
Simple example of using FastAPI-MCP to add an MCP server to a FastAPI app.
"""

from examples.apps import items

from fastapi_mcp import FastApiMCP


# Add MCP server to the FastAPI app
mcp = FastApiMCP(
    items.app,
    name="Item API MCP",
    description="MCP server for the Item API",
    base_url="http://localhost:8000",
)

mcp.mount()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(items.app, host="0.0.0.0", port=8000)
