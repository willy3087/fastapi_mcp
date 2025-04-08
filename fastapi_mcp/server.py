from contextlib import asynccontextmanager
from typing import Dict, Optional, Any, List, Union, AsyncIterator

from fastapi import FastAPI, Request, APIRouter
from fastapi.openapi.utils import get_openapi
from mcp.server.lowlevel.server import Server
import mcp.types as types

from fastapi_mcp.openapi.convert import convert_openapi_to_mcp_tools
from fastapi_mcp.execute import execute_api_tool
from fastapi_mcp.transport.sse import FastApiSseTransport

from logging import getLogger


logger = getLogger(__name__)


class FastApiMCP:
    def __init__(
        self,
        fastapi: FastAPI,
        name: Optional[str] = None,
        description: Optional[str] = None,
        base_url: Optional[str] = None,
        describe_all_responses: bool = False,
        describe_full_response_schema: bool = False,
    ):
        self.operation_map: Dict[str, Dict[str, Any]]
        self.tools: List[types.Tool]

        self.fastapi = fastapi
        self.name = name
        self.description = description

        self._base_url = base_url
        self._describe_all_responses = describe_all_responses
        self._describe_full_response_schema = describe_full_response_schema

        self.mcp_server = self.create_server()

    def create_server(self) -> Server:
        """
        Create an MCP server from the FastAPI app.

        Args:
            fastapi: The FastAPI application
            name: Name for the MCP server (defaults to app.title)
            description: Description for the MCP server (defaults to app.description)
            base_url: Base URL for API requests. If not provided, the base URL will be determined from the
                FastAPI app's root path. Although optional, it is highly recommended to provide a base URL,
                as the root path would be different when the app is deployed.
            describe_all_responses: Whether to include all possible response schemas in tool descriptions
            describe_full_response_schema: Whether to include full json schema for responses in tool descriptions

        Returns:
            A tuple containing:
            - The created MCP Server instance (NOT mounted to the app)
            - A mapping of operation IDs to operation details for HTTP execution
        """
        # Get OpenAPI schema from FastAPI app
        openapi_schema = get_openapi(
            title=self.fastapi.title,
            version=self.fastapi.version,
            openapi_version=self.fastapi.openapi_version,
            description=self.fastapi.description,
            routes=self.fastapi.routes,
        )

        # Get server name and description from app if not provided
        server_name = self.name or self.fastapi.title or "FastAPI MCP"
        server_description = self.description or self.fastapi.description

        # Convert OpenAPI schema to MCP tools
        self.tools, self.operation_map = convert_openapi_to_mcp_tools(
            openapi_schema,
            describe_all_responses=self._describe_all_responses,
            describe_full_response_schema=self._describe_full_response_schema,
        )

        # Determine base URL if not provided
        if not self._base_url:
            # Try to determine the base URL from FastAPI config
            if hasattr(self.fastapi, "root_path") and self.fastapi.root_path:
                self._base_url = self.fastapi.root_path
            else:
                # Default to localhost with FastAPI default port
                port = 8000
                for route in self.fastapi.routes:
                    if hasattr(route, "app") and hasattr(route.app, "port"):
                        port = route.app.port
                        break
                self._base_url = f"http://localhost:{port}"

        # Normalize base URL
        if self._base_url.endswith("/"):
            self._base_url = self._base_url[:-1]

        # Create the MCP server
        mcp_server: Server = Server(server_name, server_description)

        # Create a lifespan context manager to store the base_url and operation_map
        @asynccontextmanager
        async def server_lifespan(server) -> AsyncIterator[Dict[str, Any]]:
            # Store context data that will be available to all server handlers
            context = {"base_url": self._base_url, "operation_map": self.operation_map}
            yield context

        # Use our custom lifespan
        mcp_server.lifespan = server_lifespan

        # Register handlers for tools
        @mcp_server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """Handler for the tools/list request"""
            return self.tools

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

        return mcp_server

    def mount(self, router: Optional[FastAPI | APIRouter] = None, mount_path: str = "/mcp") -> None:
        """
        Mount the MCP server to the FastAPI app.

        Args:
            router: The FastAPI app or APIRouter to mount the MCP server to. If not provided, the MCP
                    server will be mounted to the FastAPI app.
            mount_path: Path where the MCP server will be mounted
        """
        # Normalize mount path
        if not mount_path.startswith("/"):
            mount_path = f"/{mount_path}"
        if mount_path.endswith("/"):
            mount_path = mount_path[:-1]

        if not router:
            router = self.fastapi

        # Create SSE transport for MCP messages
        sse_transport = FastApiSseTransport(f"{mount_path}/messages/")

        # Route for MCP connection
        @router.get(mount_path)
        async def handle_mcp_connection(request: Request):
            async with sse_transport.connect_sse(request.scope, request.receive, request._send) as (reader, writer):
                await self.mcp_server.run(
                    reader,
                    writer,
                    self.mcp_server.create_initialization_options(
                        notification_options=None, experimental_capabilities={}
                    ),
                )

        # Route for MCP messages
        @router.post(f"{mount_path}/messages/")
        async def handle_post_message(request: Request):
            return await sse_transport.handle_fastapi_post_message(request)

        logger.info(f"MCP server listening at {mount_path}")
