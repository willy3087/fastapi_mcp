import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from .fixtures.types import *  # noqa: F403
from .fixtures.example_data import *  # noqa: F403
from .fixtures.simple_app import *  # noqa: F403
from .fixtures.complex_app import *  # noqa: F403

# Add specific fixtures for MCP testing
import pytest
from fastapi.testclient import TestClient

from fastapi_mcp import FastApiMCP


@pytest.fixture
def mcp_server(simple_fastapi_app):
    """
    Create a basic MCP server instance for the simple_fastapi_app.
    This is a utility fixture to be used by multiple tests.
    """
    return FastApiMCP(
        simple_fastapi_app,
        name="Test MCP Server",
        description="Test MCP server for unit testing",
        base_url="http://testserver",
    )


@pytest.fixture
def complex_mcp_server(complex_fastapi_app):
    """
    Create a MCP server instance for the complex_fastapi_app.
    This is a utility fixture to be used by multiple tests.
    """
    return FastApiMCP(
        complex_fastapi_app,
        name="Complex Test MCP Server",
        description="Complex test MCP server for unit testing",
        base_url="http://testserver",
        describe_all_responses=True,
        describe_full_response_schema=True,
    )


@pytest.fixture
def client(simple_fastapi_app):
    """
    Create a test client for the simple_fastapi_app.
    """
    return TestClient(simple_fastapi_app)


@pytest.fixture
def complex_client(complex_fastapi_app):
    """
    Create a test client for the complex_fastapi_app.
    """
    return TestClient(complex_fastapi_app)
