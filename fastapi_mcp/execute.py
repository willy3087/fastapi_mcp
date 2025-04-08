"""
Direct OpenAPI to MCP Tools Conversion Module.

This module provides functionality for directly converting OpenAPI schema to MCP tool specifications
and for executing HTTP tools.
"""

import json
import logging
from typing import Any, Dict, List, Union

import httpx

import mcp.types as types


logger = logging.getLogger("fastapi_mcp")


async def execute_api_tool(
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
    path: str = operation["path"]
    method: str = operation["method"]
    parameters: List[Dict[str, Any]] = operation.get("parameters", [])

    # Deep copy arguments to avoid modifying the original
    kwargs = arguments.copy() if arguments else {}

    # Prepare URL with path parameters
    url = f"{base_url}{path}"
    for param in parameters:
        if param.get("in") == "path" and param.get("name") in kwargs:
            param_name = param.get("name", None)
            if param_name is None:
                raise ValueError(f"Parameter name is None for parameter: {param}")
            url = url.replace(f"{{{param_name}}}", str(kwargs.pop(param_name)))

    # Prepare query parameters
    query = {}
    for param in parameters:
        if param.get("in") == "query" and param.get("name") in kwargs:
            param_name = param.get("name", None)
            if param_name is None:
                raise ValueError(f"Parameter name is None for parameter: {param}")
            query[param_name] = kwargs.pop(param_name)

    # Prepare headers
    headers = {}
    for param in parameters:
        if param.get("in") == "header" and param.get("name") in kwargs:
            param_name = param.get("name", None)
            if param_name is None:
                raise ValueError(f"Parameter name is None for parameter: {param}")
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
