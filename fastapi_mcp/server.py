"""
Server module for FastAPI-MCP.

This module provides functionality for creating and mounting MCP servers to FastAPI applications.
"""

from typing import Dict, Optional, Any

from fastapi import FastAPI
from mcp.server.lowlevel.server import Server

from .mcp_tools import create_mcp_server as direct_create_mcp_server
from .mcp_tools import mount_mcp_server as direct_mount_mcp_server
from .mcp_tools import add_mcp_server as direct_add_mcp_server


def create_mcp_server(
    app: FastAPI,
    name: Optional[str] = None,
    description: Optional[str] = None,
    capabilities: Optional[Dict[str, Any]] = None,
    describe_all_responses: bool = False,
    describe_full_response_schema: bool = False,
) -> Server:
    """
    Create an MCP server from a FastAPI app using direct OpenAPI to MCP conversion.

    Args:
        app: The FastAPI application
        name: Name for the MCP server (defaults to app.title)
        description: Description for the MCP server (defaults to app.description)
        capabilities: Optional capabilities for the MCP server (ignored in direct conversion)
        describe_all_responses: Whether to include all possible response schemas in tool descriptions. Recommended to keep False, as the LLM will probably derive if there is an error.
        describe_full_response_schema: Whether to include full json schema for responses in tool descriptions. Recommended to keep False, as examples are more LLM friendly, and save tokens.

    Returns:
        The created MCP Server instance (NOT mounted to the app)
    """
    # Use direct conversion (returns a tuple of server and operation_map)
    server_tuple = direct_create_mcp_server(
        app,
        name,
        description,
        describe_all_responses=describe_all_responses,
        describe_full_response_schema=describe_full_response_schema,
    )
    # Extract just the server from the tuple
    return server_tuple[0]


def mount_mcp_server(
    app: FastAPI,
    mcp_server: Server,
    mount_path: str = "/mcp",
    base_url: Optional[str] = None,
    describe_all_responses: bool = False,
    describe_full_response_schema: bool = False,
) -> None:
    """
    Mount an MCP server to a FastAPI app.

    Args:
        app: The FastAPI application
        mcp_server: The MCP server to mount
        mount_path: Path where the MCP server will be mounted
        base_url: Base URL for API requests
        describe_all_responses: Whether to include all possible response schemas in tool descriptions. Recommended to keep False, as the LLM will probably derive if there is an error.
        describe_full_response_schema: Whether to include full json schema for responses in tool descriptions. Recommended to keep False, as examples are more LLM friendly, and save tokens.
    """
    # Get OpenAPI schema from FastAPI app for operation mapping
    from fastapi.openapi.utils import get_openapi
    from .mcp_tools import convert_openapi_to_mcp_tools

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )

    # Extract operation map for HTTP calls
    # The function returns a tuple (tools, operation_map)
    result = convert_openapi_to_mcp_tools(
        openapi_schema,
        describe_all_responses=describe_all_responses,
        describe_full_response_schema=describe_full_response_schema,
    )
    operation_map = result[1]

    # Mount using the direct approach
    direct_mount_mcp_server(app, mcp_server, operation_map, mount_path, base_url)


def add_mcp_server(
    app: FastAPI,
    mount_path: str = "/mcp",
    name: Optional[str] = None,
    description: Optional[str] = None,
    base_url: Optional[str] = None,
    describe_all_responses: bool = False,
    describe_full_response_schema: bool = False,
) -> Server:
    """
    Add an MCP server to a FastAPI app.

    Args:
        app: The FastAPI application
        mount_path: Path where the MCP server will be mounted
        name: Name for the MCP server (defaults to app.title)
        description: Description for the MCP server (defaults to app.description)
        base_url: Base URL for API requests (defaults to http://localhost:$PORT)
        describe_all_responses: Whether to include all possible response schemas in tool descriptions. Recommended to keep False, as the LLM will probably derive if there is an error.
        describe_full_response_schema: Whether to include full json schema for responses in tool descriptions. Recommended to keep False, as examples are more LLM friendly, and save tokens.

    Returns:
        The MCP server instance that was created and mounted
    """
    # Use direct conversion approach
    return direct_add_mcp_server(
        app,
        mount_path,
        name,
        description,
        base_url,
        describe_all_responses=describe_all_responses,
        describe_full_response_schema=describe_full_response_schema,
    )
