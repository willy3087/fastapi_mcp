import pytest
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from fastapi_mcp import add_mcp_server


class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    tags: List[str] = []


@pytest.fixture
def sample_app():
    """Create a sample FastAPI app for testing."""
    app = FastAPI(
        title="Test API",
        description="A test API for unit testing",
        version="0.1.0",
    )

    @app.get("/items/", response_model=List[Item], tags=["items"])
    async def list_items(skip: int = 0, limit: int = 10):
        """
        List all items.

        Returns a list of items, with pagination support.
        """
        return []

    @app.get("/items/{item_id}", response_model=Item, tags=["items"])
    async def read_item(item_id: int):
        """
        Get a specific item by ID.

        Returns the item with the specified ID.
        """
        return {"id": item_id, "name": "Test Item", "price": 0.0}

    @app.post("/items/", response_model=Item, tags=["items"])
    async def create_item(item: Item):
        """
        Create a new item.

        Returns the created item.
        """
        return item

    return app


def test_tool_generation_basic(sample_app):
    """Test that MCP tools are properly generated with default settings."""
    # Create MCP server and register tools
    mcp_server = add_mcp_server(sample_app, serve_tools=True, base_url="http://localhost:8000")

    # Extract tools for inspection
    tools = mcp_server._tool_manager.list_tools()

    # Tool count may include the MCP endpoint itself, so check for at least the API endpoints
    assert len(tools) >= 3, f"Expected at least 3 tools, got {len(tools)}"

    # Check each tool has required properties
    for tool in tools:
        assert hasattr(tool, "name"), "Tool missing 'name' property"
        assert hasattr(tool, "description"), "Tool missing 'description' property"
        assert hasattr(tool, "parameters"), "Tool missing 'parameters' property"
        assert hasattr(tool, "fn_metadata"), "Tool missing 'fn_metadata' property"

    # Verify specific properties of the list_items tool
    list_items_tool = next((t for t in tools if t.name == "list_items_items__get"), None)
    assert list_items_tool is not None, "list_items tool not found"
    assert "skip" in list_items_tool.parameters["properties"], "Expected 'skip' parameter"
    assert "limit" in list_items_tool.parameters["properties"], "Expected 'limit' parameter"


def test_tool_generation_with_full_schema(sample_app):
    """Test that MCP tools include full response schema when requested."""
    # Create MCP server with full schema for all operations
    mcp_server = add_mcp_server(
        sample_app, serve_tools=True, base_url="http://localhost:8000", describe_full_response_schema=True
    )

    # Extract tools for inspection
    tools = mcp_server._tool_manager.list_tools()

    # Verify specific properties of the list_items tool
    list_items_tool = next((t for t in tools if t.name == "list_items_items__get"), None)
    assert list_items_tool is not None, "list_items tool not found"

    # In the full schema mode, the item schema should be included somewhere in the tool
    # This might be in the description rather than the parameters
    description = list_items_tool.description

    # Check that the tool includes information about the Item schema
    assert "Item" in description, "Item schema should be included in the description"
    assert "price" in description, "Item properties should be included in the description"


def test_tool_generation_with_all_responses(sample_app):
    """Test that MCP tools include all possible responses when requested."""
    # Create MCP server with all response status codes
    mcp_server = add_mcp_server(
        sample_app, serve_tools=True, base_url="http://localhost:8000", describe_all_responses=True
    )

    # Extract tools for inspection
    tools = mcp_server._tool_manager.list_tools()

    # Find the read_item tool
    read_item_tool = next((t for t in tools if t.name == "read_item_items__item_id__get"), None)
    assert read_item_tool is not None, "read_item tool not found"

    # With describe_all_responses=True, description should include response status codes
    assert "200" in read_item_tool.description, "Expected success response code in description"


def test_custom_tool_addition(sample_app):
    """Test that custom tools can be added alongside API tools."""
    # Create MCP server with API tools
    mcp_server = add_mcp_server(sample_app, serve_tools=True, base_url="http://localhost:8000")

    # Get initial tool count
    initial_tool_count = len(mcp_server._tool_manager.list_tools())

    # Add a custom tool
    @mcp_server.tool()
    async def custom_tool() -> str:
        """A custom tool for testing."""
        return "Test result"

    # Extract tools for inspection
    tools = mcp_server._tool_manager.list_tools()

    # Verify we have one more tool than before
    assert len(tools) == initial_tool_count + 1, f"Expected {initial_tool_count + 1} tools, got {len(tools)}"

    # Find both API tools and custom tools
    list_items_tool = next((t for t in tools if t.name == "list_items_items__get"), None)
    assert list_items_tool is not None, "API tool (list_items) not found"

    custom_tool_def = next((t for t in tools if t.name == "custom_tool"), None)
    assert custom_tool_def is not None, "Custom tool not found"
    assert custom_tool_def.description == "A custom tool for testing.", "Custom tool description not preserved"
