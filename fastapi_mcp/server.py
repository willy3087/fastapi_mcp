"""
Server module for FastAPI-MCP.

This module provides functionality for creating and mounting MCP servers to FastAPI applications.
"""

from contextlib import asynccontextmanager
from typing import Dict, Optional, Any, Tuple, List, Union, AsyncIterator

from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from mcp.server.lowlevel.server import Server
from mcp.server.sse import SseServerTransport
import mcp.types as types

from fastapi_mcp.openapi.convert import convert_openapi_to_mcp_tools
from fastapi_mcp.execute import execute_api_tool


def create_mcp_server(
    app: FastAPI,
    name: Optional[str] = None,
    description: Optional[str] = None,
    base_url: Optional[str] = None,
    describe_all_responses: bool = False,
    describe_full_response_schema: bool = False,
) -> Tuple[Server, Dict[str, Dict[str, Any]]]:
    """
    Create an MCP server from a FastAPI app.

    Args:
        app: The FastAPI application
        name: Name for the MCP server (defaults to app.title)
        description: Description for the MCP server (defaults to app.description)
        base_url: Base URL for API requests (defaults to http://localhost:$PORT)
        describe_all_responses: Whether to include all possible response schemas in tool descriptions
        describe_full_response_schema: Whether to include full json schema for responses in tool descriptions

    Returns:
        A tuple containing:
        - The created MCP Server instance (NOT mounted to the app)
        - A mapping of operation IDs to operation details for HTTP execution
    """
    # Get OpenAPI schema from FastAPI app
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )

    # Get server name and description from app if not provided
    server_name = name or app.title or "FastAPI MCP"
    server_description = description or app.description

    # Convert OpenAPI schema to MCP tools
    tools, operation_map = convert_openapi_to_mcp_tools(
        openapi_schema,
        describe_all_responses=describe_all_responses,
        describe_full_response_schema=describe_full_response_schema,
    )

    # Determine base URL if not provided
    if not base_url:
        # Try to determine the base URL from FastAPI config
        if hasattr(app, "root_path") and app.root_path:
            base_url = app.root_path
        else:
            # Default to localhost with FastAPI default port
            port = 8000
            for route in app.routes:
                if hasattr(route, "app") and hasattr(route.app, "port"):
                    port = route.app.port
                    break
            base_url = f"http://localhost:{port}"

    # Normalize base URL
    if base_url.endswith("/"):
        base_url = base_url[:-1]

    # Create the MCP server
    mcp_server: Server = Server(server_name, server_description)

    # Create a lifespan context manager to store the base_url and operation_map
    @asynccontextmanager
    async def server_lifespan(server) -> AsyncIterator[Dict[str, Any]]:
        # Store context data that will be available to all server handlers
        context = {"base_url": base_url, "operation_map": operation_map}
        yield context

    # Use our custom lifespan
    mcp_server.lifespan = server_lifespan

    # Register handlers for tools
    @mcp_server.list_tools()
    async def handle_list_tools() -> List[types.Tool]:
        """Handler for the tools/list request"""
        return tools

    # Register the tool call handler
    @mcp_server.call_tool()
    async def handle_call_tool(
        name: str, arguments: Dict[str, Any]
    ) -> List[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]:
        """Handler for the tools/call request"""
        # Get context from server lifespan
        ctx = mcp_server.request_context
        base_url = ctx.lifespan_context["base_url"]
        operation_map = ctx.lifespan_context["operation_map"]

        # Execute the tool
        return await execute_api_tool(base_url, name, arguments, operation_map)

    return mcp_server, operation_map


def mount_mcp_server(
    app: FastAPI,
    mcp_server: Server,
    operation_map: Dict[str, Dict[str, Any]],
    mount_path: str = "/mcp",
    base_url: Optional[str] = None,
) -> None:
    """
    Mount an MCP server to a FastAPI app.

    Args:
        app: The FastAPI application
        mcp_server: The MCP server to mount
        operation_map: A mapping of operation IDs to operation details
        mount_path: Path where the MCP server will be mounted
        base_url: Base URL for API requests
    """
    # Normalize mount path
    if not mount_path.startswith("/"):
        mount_path = f"/{mount_path}"
    if mount_path.endswith("/"):
        mount_path = mount_path[:-1]

    # Create SSE transport for MCP messages
    sse_transport = SseServerTransport(f"{mount_path}/messages/")

    # Define MCP connection handler
    async def handle_mcp_connection(request: Request):
        async with sse_transport.connect_sse(request.scope, request.receive, request._send) as streams:
            await mcp_server.run(
                streams[0],
                streams[1],
                mcp_server.create_initialization_options(notification_options=None, experimental_capabilities={}),
            )

    # Mount the MCP connection handler
    app.get(mount_path)(handle_mcp_connection)
    app.mount(f"{mount_path}/messages/", app=sse_transport.handle_post_message)


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
        describe_all_responses: Whether to include all possible response schemas in tool descriptions
        describe_full_response_schema: Whether to include full json schema for responses in tool descriptions

    Returns:
        The MCP server instance that was created and mounted
    """
    # Create MCP server
    mcp_server, operation_map = create_mcp_server(
        app,
        name,
        description,
        base_url,
        describe_all_responses=describe_all_responses,
        describe_full_response_schema=describe_full_response_schema,
    )

    # Mount MCP server
    mount_mcp_server(app, mcp_server, operation_map, mount_path, base_url)

    return mcp_server
