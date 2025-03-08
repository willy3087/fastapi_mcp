"""
Test the discovery and generator modules with a sample FastAPI application.
"""

import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import pytest
from fastapi import FastAPI
from pydantic import BaseModel

from fastapi_mcp.discovery import discover_fastapi_app
from fastapi_mcp.generator import generate_mcp_server


# Sample FastAPI application for testing
app = FastAPI(title="Test API", description="A test API for FastAPI-MCP")

class Item(BaseModel):
    name: str
    price: float
    is_offer: Optional[bool] = None

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    """Get details for a specific item"""
    return {"item_id": item_id, "q": q}

@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    """Update an item with new information"""
    return {"item_id": item_id, "item": item}

@app.post("/items/")
def create_item(item: Item):
    """Create a new item"""
    return {"item": item}

@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    """Delete an item"""
    return {"item_id": item_id}


@pytest.fixture
def output_dir():
    """Provide a temporary directory for test output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_discover_endpoints():
    """Test discovering endpoints from a FastAPI application."""
    endpoints = discover_fastapi_app(app)
    
    assert len(endpoints) == 4  # 4 endpoints in our sample app
    
    # Check that we found all our endpoints
    endpoint_names = {endpoint.name for endpoint in endpoints}
    assert endpoint_names == {"read_item", "update_item", "create_item", "delete_item"}
    
    # Check endpoint properties
    read_item_endpoint = next(e for e in endpoints if e.name == "read_item")
    assert read_item_endpoint.method == "GET"
    assert read_item_endpoint.path == "/items/{item_id}"
    assert read_item_endpoint.description == "Get details for a specific item"
    
    # Check parameters
    assert "item_id" in read_item_endpoint.path_params
    assert "q" in read_item_endpoint.query_params
    assert not read_item_endpoint.body_params


def test_generate_mcp_server(output_dir):
    """Test generating an MCP server from a FastAPI application."""
    endpoints = discover_fastapi_app(app)
    server_path = generate_mcp_server(app, endpoints, output_dir)
    
    assert server_path.exists()
    assert (output_dir / "requirements.txt").exists()
    assert (output_dir / "README.md").exists()
    
    # Check the server file content
    with open(server_path) as f:
        content = f.read()
        
    # Check that our endpoints were generated
    assert "@mcp.tool()" in content
    assert "async def read_item" in content
    assert "async def update_item" in content
    assert "async def create_item" in content
    assert "async def delete_item" in content
    
    # Check the FastAPI app information
    assert 'mcp = FastMCP("Test API")' in content
    
    # Check that it can be imported (basic syntax check)
    sys.path.insert(0, str(output_dir))
    try:
        import server  # noqa
    except Exception as e:
        pytest.fail(f"Failed to import generated server: {e}") 