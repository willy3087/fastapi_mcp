"""
Direct OpenAPI to MCP Tools Conversion Module.

This module provides functionality for directly converting OpenAPI schema to MCP tool specifications
without the intermediate step of dynamically generating Python functions.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union, Tuple, AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

import mcp.types as types
from mcp.server.lowlevel.server import Server

from .openapi_utils import (
    clean_schema_for_display,
    generate_example_from_schema,
    resolve_schema_references,
    get_single_param_type_from_schema,
)

logger = logging.getLogger("fastapi_mcp")


def convert_openapi_to_mcp_tools(
    openapi_schema: Dict[str, Any],
    describe_all_responses: bool = False,
    describe_full_response_schema: bool = False,
) -> Tuple[List[types.Tool], Dict[str, Dict[str, Any]]]:
    """
    Convert OpenAPI operations to MCP tools.

    Args:
        openapi_schema: The OpenAPI schema
        describe_all_responses: Whether to include all possible response schemas in tool descriptions
        describe_full_response_schema: Whether to include full response schema in tool descriptions

    Returns:
        A tuple containing:
        - A list of MCP tools
        - A mapping of operation IDs to operation details for HTTP execution
    """
    # Resolve all references in the schema at once
    resolved_openapi_schema = resolve_schema_references(openapi_schema, openapi_schema)

    tools = []
    operation_map = {}

    # Process each path in the OpenAPI schema
    for path, path_item in resolved_openapi_schema.get("paths", {}).items():
        for method, operation in path_item.items():
            # Skip non-HTTP methods
            if method not in ["get", "post", "put", "delete", "patch"]:
                continue

            # Get operation metadata
            operation_id = operation.get("operationId")
            if not operation_id:
                continue

            # Save operation details for later HTTP calls
            operation_map[operation_id] = {
                "path": path,
                "method": method,
                "parameters": operation.get("parameters", []),
                "request_body": operation.get("requestBody", {}),
            }

            summary = operation.get("summary", "")
            description = operation.get("description", "")

            # Build tool description
            tool_description = f"{summary}" if summary else f"{method.upper()} {path}"
            if description:
                tool_description += f"\n\n{description}"

            # Add response information to the description
            responses = operation.get("responses", {})
            if responses:
                response_info = "\n\n### Responses:\n"

                # Find the success response (usually 200 or 201)
                success_codes = ["200", "201", "202", 200, 201, 202]
                success_response = None
                for status_code in success_codes:
                    if str(status_code) in responses:
                        success_response = responses[str(status_code)]
                        break

                # Get the list of responses to include
                responses_to_include = responses
                if not describe_all_responses and success_response:
                    # If we're not describing all responses, only include the success response
                    success_code = next((code for code in success_codes if str(code) in responses), None)
                    if success_code:
                        responses_to_include = {str(success_code): success_response}

                # Process all selected responses
                for status_code, response_data in responses_to_include.items():
                    response_desc = response_data.get("description", "")
                    response_info += f"\n**{status_code}**: {response_desc}"

                    # Highlight if this is the main success response
                    if response_data == success_response:
                        response_info += " (Success Response)"

                    # Add schema information if available
                    if "content" in response_data:
                        for content_type, content_data in response_data["content"].items():
                            if "schema" in content_data:
                                schema = content_data["schema"]
                                response_info += f"\nContent-Type: {content_type}"

                                # Clean the schema for display
                                display_schema = clean_schema_for_display(schema)

                                # Try to get example response
                                example_response = None

                                # Check if content has examples
                                if "examples" in content_data:
                                    for example_key, example_data in content_data["examples"].items():
                                        if "value" in example_data:
                                            example_response = example_data["value"]
                                            break
                                # If content has example
                                elif "example" in content_data:
                                    example_response = content_data["example"]

                                # If we have an example response, add it to the docs
                                if example_response:
                                    response_info += "\n\n**Example Response:**\n```json\n"
                                    response_info += json.dumps(example_response, indent=2)
                                    response_info += "\n```"
                                # Otherwise generate an example from the schema
                                else:
                                    generated_example = generate_example_from_schema(display_schema)
                                    if generated_example:
                                        response_info += "\n\n**Example Response:**\n```json\n"
                                        response_info += json.dumps(generated_example, indent=2)
                                        response_info += "\n```"

                                # Only include full schema information if requested
                                if describe_full_response_schema:
                                    # Format schema information based on its type
                                    if display_schema.get("type") == "array" and "items" in display_schema:
                                        items_schema = display_schema["items"]

                                        response_info += "\n\n**Output Schema:** Array of items with the following structure:\n```json\n"
                                        response_info += json.dumps(items_schema, indent=2)
                                        response_info += "\n```"
                                    elif "properties" in display_schema:
                                        response_info += "\n\n**Output Schema:**\n```json\n"
                                        response_info += json.dumps(display_schema, indent=2)
                                        response_info += "\n```"
                                    else:
                                        response_info += "\n\n**Output Schema:**\n```json\n"
                                        response_info += json.dumps(display_schema, indent=2)
                                        response_info += "\n```"

                tool_description += response_info

            # Organize parameters by type
            path_params = []
            query_params = []
            header_params = []
            body_params = []

            for param in operation.get("parameters", []):
                param_name = param.get("name")
                param_in = param.get("in")
                required = param.get("required", False)

                if param_in == "path":
                    path_params.append((param_name, param))
                elif param_in == "query":
                    query_params.append((param_name, param))
                elif param_in == "header":
                    header_params.append((param_name, param))

            # Process request body if present
            request_body = operation.get("requestBody", {})
            if request_body and "content" in request_body:
                content_type = next(iter(request_body["content"]), None)
                if content_type and "schema" in request_body["content"][content_type]:
                    schema = request_body["content"][content_type]["schema"]
                    if "properties" in schema:
                        for prop_name, prop_schema in schema["properties"].items():
                            required = prop_name in schema.get("required", [])
                            body_params.append(
                                (
                                    prop_name,
                                    {
                                        "name": prop_name,
                                        "schema": prop_schema,
                                        "required": required,
                                    },
                                )
                            )

            # Create input schema properties for all parameters
            properties = {}
            required_props = []

            # Add path parameters to properties
            for param_name, param in path_params:
                param_schema = param.get("schema", {})
                param_desc = param.get("description", "")
                param_required = param.get("required", True)  # Path params are usually required

                properties[param_name] = {
                    "type": param_schema.get("type", "string"),
                    "title": param_name,
                    "description": param_desc,
                }

                if param_required:
                    required_props.append(param_name)

            # Add query parameters to properties
            for param_name, param in query_params:
                param_schema = param.get("schema", {})
                param_desc = param.get("description", "")
                param_required = param.get("required", False)

                properties[param_name] = {
                    "type": get_single_param_type_from_schema(param_schema),
                    "title": param_name,
                    "description": param_desc,
                }
                if "default" in param_schema:
                    properties[param_name]["default"] = param_schema["default"]

                if param_required:
                    required_props.append(param_name)

            # Add body parameters to properties
            for param_name, param in body_params:
                param_schema = param.get("schema", {})
                param_required = param.get("required", False)

                properties[param_name] = {
                    "type": get_single_param_type_from_schema(param_schema),
                    "title": param_name,
                }
                if "default" in param_schema:
                    properties[param_name]["default"] = param_schema["default"]

                if param_required:
                    required_props.append(param_name)

            # Create a proper input schema for the tool
            input_schema = {"type": "object", "properties": properties, "title": f"{operation_id}Arguments"}

            if required_props:
                input_schema["required"] = required_props

            # Create the MCP tool definition
            tool = types.Tool(name=operation_id, description=tool_description, inputSchema=input_schema)

            tools.append(tool)

    return tools, operation_map


async def execute_http_tool(
    base_url: str, tool_name: str, arguments: Dict[str, Any], operation_map: Dict[str, Dict[str, Any]]
) -> List[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]:
    """
    Execute an MCP tool by making an HTTP request to the corresponding API endpoint.

    Args:
        base_url: The base URL for the API
        tool_name: The name of the tool to execute
        arguments: The arguments for the tool
        operation_map: A mapping from tool names to operation details

    Returns:
        The result as MCP content types
    """
    if tool_name not in operation_map:
        return [types.TextContent(type="text", text=f"Unknown tool: {tool_name}")]

    operation = operation_map[tool_name]
    path = operation["path"]
    method = operation["method"]
    parameters = operation.get("parameters", [])

    # Deep copy arguments to avoid modifying the original
    kwargs = arguments.copy() if arguments else {}

    # Prepare URL with path parameters
    url = f"{base_url}{path}"
    for param in parameters:
        if param.get("in") == "path" and param.get("name") in kwargs:
            param_name = param.get("name")
            url = url.replace(f"{{{param_name}}}", str(kwargs.pop(param_name)))

    # Prepare query parameters
    query = {}
    for param in parameters:
        if param.get("in") == "query" and param.get("name") in kwargs:
            param_name = param.get("name")
            query[param_name] = kwargs.pop(param_name)

    # Prepare headers
    headers = {}
    for param in parameters:
        if param.get("in") == "header" and param.get("name") in kwargs:
            param_name = param.get("name")
            headers[param_name] = kwargs.pop(param_name)

    # Prepare request body (remaining kwargs)
    body = kwargs if kwargs else None

    try:
        # Make the request
        logger.debug(f"Making {method.upper()} request to {url}")
        async with httpx.AsyncClient() as client:
            if method.lower() == "get":
                response = await client.get(url, params=query, headers=headers)
            elif method.lower() == "post":
                response = await client.post(url, params=query, headers=headers, json=body)
            elif method.lower() == "put":
                response = await client.put(url, params=query, headers=headers, json=body)
            elif method.lower() == "delete":
                response = await client.delete(url, params=query, headers=headers)
            elif method.lower() == "patch":
                response = await client.patch(url, params=query, headers=headers, json=body)
            else:
                return [types.TextContent(type="text", text=f"Unsupported HTTP method: {method}")]

        # Process the response
        try:
            result = response.json()
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        except ValueError:
            return [types.TextContent(type="text", text=response.text)]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error calling {tool_name}: {str(e)}")]


def create_mcp_server(
    app: FastAPI,
    name: Optional[str] = None,
    description: Optional[str] = None,
    base_url: Optional[str] = None,
    describe_all_responses: bool = False,
    describe_full_response_schema: bool = False,
) -> tuple[Server, Dict[str, Dict[str, Any]]]:
    """
    Create a low-level MCP server from a FastAPI app using direct OpenAPI to MCP conversion.

    Args:
        app: The FastAPI application
        name: Name for the MCP server (defaults to app.title)
        description: Description for the MCP server (defaults to app.description)
        base_url: Base URL for API requests (defaults to http://localhost:$PORT)
        describe_all_responses: Whether to include all possible response schemas in tool descriptions
        describe_full_response_schema: Whether to include full response schema in tool descriptions

    Returns:
        A tuple containing:
        - The MCP Server instance (NOT mounted to the app)
        - A mapping of operation IDs to operation details for HTTP execution
    """
    # Use app details if not provided
    server_name = name or app.title or "FastAPI MCP"
    server_description = description or app.description

    # Get OpenAPI schema from FastAPI app
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )

    # Convert OpenAPI operations to MCP tools
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
        return await execute_http_tool(base_url, name, arguments, operation_map)

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
        base_url: Base URL for API requests (defaults to http://localhost:$PORT)
    """
    # Normalize mount path
    if not mount_path.startswith("/"):
        mount_path = f"/{mount_path}"
    if mount_path.endswith("/"):
        mount_path = mount_path[:-1]

    # Create SSE transport for MCP messages
    from mcp.server.sse import SseServerTransport
    from fastapi import Request

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
        name: Name for the MCP server
        description: Description for the MCP server
        base_url: Base URL for API requests
        describe_all_responses: Whether to include all possible response schemas in tool descriptions
        describe_full_response_schema: Whether to include full response schema in tool descriptions

    Returns:
        The MCP server instance
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

    # Mount MCP server to FastAPI app
    mount_mcp_server(
        app,
        mcp_server,
        operation_map,
        mount_path,
        base_url,
    )

    return mcp_server
