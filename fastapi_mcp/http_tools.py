"""
HTTP tools for FastAPI-MCP.

This module provides functionality for creating MCP tools from FastAPI endpoints.
"""

import inspect
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Type, get_type_hints

import httpx
from fastapi import FastAPI, params
from fastapi.openapi.utils import get_openapi
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

logger = logging.getLogger("fastapi_mcp")


def create_mcp_tools_from_openapi(app: FastAPI, mcp_server: FastMCP, base_url: str = None) -> None:
    """
    Create MCP tools from a FastAPI app's OpenAPI schema.

    Args:
        app: The FastAPI application
        mcp_server: The MCP server to add tools to
        base_url: Base URL for API requests (defaults to http://localhost:$PORT)
    """
    # Get OpenAPI schema from FastAPI app
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )

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

    # Process each path in the OpenAPI schema
    for path, path_item in openapi_schema.get("paths", {}).items():
        for method, operation in path_item.items():
            # Skip non-HTTP methods
            if method not in ["get", "post", "put", "delete", "patch"]:
                continue

            # Get operation metadata
            operation_id = operation.get("operationId")
            if not operation_id:
                continue

            # Create MCP tool for this operation
            create_http_tool(
                mcp_server=mcp_server,
                base_url=base_url,
                path=path,
                method=method,
                operation_id=operation_id,
                summary=operation.get("summary", ""),
                description=operation.get("description", ""),
                parameters=operation.get("parameters", []),
                request_body=operation.get("requestBody", {}),
                responses=operation.get("responses", {}),
            )


def create_http_tool(
    mcp_server: FastMCP,
    base_url: str,
    path: str,
    method: str,
    operation_id: str,
    summary: str,
    description: str,
    parameters: List[Dict[str, Any]],
    request_body: Dict[str, Any],
    responses: Dict[str, Any],
) -> None:
    """
    Create an MCP tool that makes an HTTP request to a FastAPI endpoint.

    Args:
        mcp_server: The MCP server to add the tool to
        base_url: Base URL for API requests
        path: API endpoint path
        method: HTTP method
        operation_id: Operation ID
        summary: Operation summary
        description: Operation description
        parameters: OpenAPI parameters
        request_body: OpenAPI request body
        responses: OpenAPI responses
    """
    # Build tool description
    tool_description = f"{summary}" if summary else f"{method.upper()} {path}"
    if description:
        tool_description += f"\n\n{description}"

    # Organize parameters by type
    path_params = []
    query_params = []
    header_params = []
    body_params = []

    for param in parameters:
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

    # Function to dynamically call the API endpoint
    async def http_tool_function(**kwargs):
        # Prepare URL with path parameters
        url = f"{base_url}{path}"
        for param_name, _ in path_params:
            if param_name in kwargs:
                url = url.replace(f"{{{param_name}}}", str(kwargs.pop(param_name)))

        # Prepare query parameters
        query = {}
        for param_name, _ in query_params:
            if param_name in kwargs:
                query[param_name] = kwargs.pop(param_name)

        # Prepare headers
        headers = {}
        for param_name, _ in header_params:
            if param_name in kwargs:
                headers[param_name] = kwargs.pop(param_name)

        # Prepare request body (remaining kwargs)
        body = kwargs if kwargs else None

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
                response = await client.delete(url, params=query, headers=headers, json=body)
            elif method.lower() == "patch":
                response = await client.patch(url, params=query, headers=headers, json=body)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

        # Process the response
        try:
            return response.json()
        except ValueError:
            return response.text

    # Set the function name and docstring
    http_tool_function.__name__ = operation_id
    http_tool_function.__doc__ = tool_description

    # Add tool to the MCP server
    mcp_server.add_tool(http_tool_function, name=operation_id, description=tool_description)
