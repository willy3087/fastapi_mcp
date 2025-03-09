"""
Tests for the fastapi_mcp server module.
This tests the creation and mounting of MCP servers to FastAPI applications.
"""

from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

from fastapi_mcp import create_mcp_server, add_mcp_server


def test_create_mcp_server():
    """Test creating an MCP server from a FastAPI app."""
    app = FastAPI(title="Test App", description="Test Description")

    # Test with default parameters
    mcp_server = create_mcp_server(app)
    assert isinstance(mcp_server, FastMCP), "Should return a FastMCP instance"
    assert mcp_server.name == "Test App", "Server name should match app title"
    assert mcp_server.instructions == "Test Description", "Server description should match app description"

    # Test with custom parameters
    custom_mcp_server = create_mcp_server(app, name="Custom Name", description="Custom Description")
    assert custom_mcp_server.name == "Custom Name", "Server name should match provided name"
    assert custom_mcp_server.instructions == "Custom Description", (
        "Server description should match provided description"
    )


def test_server_configuration():
    """Test that server configuration options are properly set."""
    app = FastAPI(title="Test API")

    # Test default configuration
    mcp_server = create_mcp_server(app)
    assert mcp_server._tool_manager is not None, "Tool manager should be created"
    assert mcp_server._resource_manager is not None, "Resource manager should be created"
    assert mcp_server._prompt_manager is not None, "Prompt manager should be created"

    # Test custom tool registration
    @mcp_server.tool()
    async def test_tool():
        """Test tool"""
        return "Test result"

    tools = mcp_server._tool_manager.list_tools()
    test_tool = next((t for t in tools if t.name == "test_tool"), None)  # noqa: F811
    assert test_tool is not None, "Custom tool should be registered"
    assert test_tool.description == "Test tool", "Tool description should be preserved"
    assert test_tool.is_async is True, "Async tools should be detected correctly"


def test_add_mcp_server_components():
    """Test that add_mcp_server correctly adds all components."""
    app = FastAPI()

    # Test with default parameters
    mcp_server = add_mcp_server(app, serve_tools=False)  # Don't actually serve tools to avoid server setup
    assert isinstance(mcp_server, FastMCP), "Should return a FastMCP instance"
    assert mcp_server._mcp_server is not None, "MCP server should be created"

    # Test custom tool addition
    @mcp_server.tool()
    async def test_tool():
        """Test tool"""
        return "Test result"

    tools = [t.name for t in mcp_server._tool_manager.list_tools()]
    assert "test_tool" in tools, "Custom tool should be registered"
