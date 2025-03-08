"""
Generator module for creating MCP servers from FastAPI applications.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Type, get_type_hints, get_origin, get_args

from fastapi import FastAPI
try:
    # Pydantic v2
    from pydantic import BaseModel, Field
except ImportError:
    # Pydantic v1 fallback
    from pydantic.main import BaseModel
    from pydantic.fields import Field

from fastapi_mcp.converter import convert_endpoint_to_mcp_tool
from fastapi_mcp.discovery import Endpoint

# Check if Python version supports PEP 604 (|) union types
PY310_OR_HIGHER = sys.version_info >= (3, 10)


def generate_mcp_server(
    app: FastAPI,
    endpoints: List[Endpoint],
    output_dir: Path,
    base_url: str = "http://localhost:8000",
) -> Path:
    """
    Generate an MCP server from a FastAPI application.
    
    Args:
        app: The FastAPI application to generate an MCP server from.
        endpoints: The list of endpoints to convert.
        output_dir: The directory to output the generated server to.
        base_url: The base URL of the FastAPI server (default: http://localhost:8000).
        
    Returns:
        The path to the generated server file.
    """
    # Create the output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate the server code
    server_code = generate_server_code(app, endpoints, base_url)
    
    # Write the server code to a file
    server_path = output_dir / "server.py"
    with open(server_path, "w") as f:
        f.write(server_code)
    
    # Generate the requirements.txt file
    requirements = [
        "mcp>=1.3.0",  # Updated to use the official MCP Python SDK
        "fastapi>=0.100.0",
        "pydantic>=2.0.0",
        "uvicorn>=0.20.0",
    ]
    
    requirements_path = output_dir / "requirements.txt"
    with open(requirements_path, "w") as f:
        f.write("\n".join(requirements))
    
    # Generate a README.md file
    readme_path = output_dir / "README.md"
    with open(readme_path, "w") as f:
        f.write(generate_readme(app, endpoints))
    
    return server_path


def generate_server_code(
    app: FastAPI,
    endpoints: List[Endpoint],
    base_url: str = "http://localhost:8000",
) -> str:
    """
    Generate the code for an MCP server.
    
    Args:
        app: The FastAPI application to generate an MCP server from.
        endpoints: The list of endpoints to convert.
        base_url: The base URL of the FastAPI server (default: http://localhost:8000).
        
    Returns:
        The generated server code as a string.
    """
    # Collect all Pydantic models used by endpoints
    pydantic_models = {}
    for endpoint in endpoints:
        # Handle path parameters
        for param_name, param_info in endpoint.path_params.items():
            param_type = param_info["type"]
            if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                if param_type.__name__ not in pydantic_models:
                    pydantic_models[param_type.__name__] = param_type
        
        # Handle query parameters
        for param_name, param_info in endpoint.query_params.items():
            param_type = param_info["type"]
            if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                if param_type.__name__ not in pydantic_models:
                    pydantic_models[param_type.__name__] = param_type
        
        # Handle body parameters
        for param_name, param_info in endpoint.body_params.items():
            param_type = param_info["type"]
            if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                if param_type.__name__ not in pydantic_models:
                    pydantic_models[param_type.__name__] = param_type
    
    # Get the FastAPI app title
    app_title = getattr(app, "title", "FastAPI") or "FastAPI"
    
    # Get the FastAPI app description
    app_description = getattr(app, "description", "") or ""
    
    # Generate imports
    handler_imports = []
    for endpoint in endpoints:
        handler = endpoint.handler
        if handler.__module__ != "__main__":
            handler_imports.append(f"# Original handler: from {handler.__module__} import {handler.__name__}")
    
    # Create the MCP server
    server_code = [
        "# Generated MCP server",
        f"# Original FastAPI app: {app_title}",
        "",
        "from mcp.server.fastmcp import FastMCP",
        "import json",
        "import requests",  # Add requests library import
        "from typing import Dict, List, Optional, Union, Any",
        "try:",
        "    from pydantic import BaseModel, Field",
        "    try:",
        "        # Pydantic v2",
        "        from pydantic import Undefined",
        "        # Add function to handle both pydantic v1 and v2 model serialization",
        "        def serialize_model(model):",
        "            if hasattr(model, 'model_dump'):",
        "                # Pydantic v2",
        "                return model.model_dump()",
        "            else:",
        "                # Pydantic v1",
        "                return model.dict()",
        "    except ImportError:",
        "        # For Pydantic v1 compatibility",
        "        Undefined = ...",
        "        def serialize_model(model):",
        "            return model.dict()",
        "except ImportError:",
        "    from pydantic.main import BaseModel",
        "    from pydantic.fields import Field",
        "    Undefined = ...",
        "    def serialize_model(model):",
        "        return model.dict()",
    ]
    
    # Add model definitions
    if pydantic_models:
        server_code.append("")
        server_code.append("# Pydantic models used by the API")
        server_code.append("")
        
        # Define model classes
        for model_name, model_class in pydantic_models.items():
            server_code.append("")
            model_lines = [f"class {model_name}(BaseModel):"]
            
            # Get model fields
            fields = get_model_fields(model_class)
            for field_name, field_info in fields.items():
                # Get type name
                type_name = _get_simple_type_name(field_info["type"])
                
                # Check if the field is optional
                is_optional = field_info.get("optional", False)
                
                # Check if the field has a default value
                if field_info["default"] is None and field_info["required"]:
                    # Required field with no default value - use Undefined
                    model_lines.append(f"    {field_name}: {type_name} = Undefined")
                elif field_info["default"] is None and not field_info["required"]:
                    # Optional field with None default
                    if is_optional:
                        model_lines.append(f"    {field_name}: Optional[{type_name}] = None")
                    else:
                        model_lines.append(f"    {field_name}: {type_name} = None")
                elif isinstance(field_info["default"], str):
                    # String default value
                    model_lines.append(f'    {field_name}: {type_name} = "{field_info["default"]}"')
                else:
                    # Other default value
                    model_lines.append(f"    {field_name}: {type_name} = {field_info['default']}")
            
            # Add the model definition
            server_code.extend(model_lines)
    
    # Add comments for handler imports
    if handler_imports:
        server_code.append("")
        server_code.extend(handler_imports)
    
    # Create FastMCP instance
    server_code.append("")
    server_code.append(f'mcp = FastMCP("{app_title}")')
    
    # Add tool definitions
    server_code.append("")
    
    # Convert endpoints to tools
    for endpoint in endpoints:
        tool_def = convert_endpoint_to_mcp_tool(endpoint)
        tool_code = generate_tool_code(tool_def, base_url)
        server_code.append(tool_code)
    
    # Add main block to run the server
    server_code.append("")
    server_code.append('if __name__ == "__main__":')
    server_code.append("    # Run the MCP server")
    server_code.append("    mcp.run()")
    
    return "\n".join(server_code)


def generate_tool_code(tool_def: Dict, base_url: str = "http://localhost:8000") -> str:
    """
    Generate code for an MCP tool.
    
    Args:
        tool_def: The tool definition to generate code for.
        base_url: The base URL of the FastAPI server (default: http://localhost:8000).
        
    Returns:
        The generated tool code as a string.
    """
    name = tool_def["name"]
    description = tool_def["description"]
    parameters = tool_def["parameters"]
    handler = tool_def["handler"]
    endpoint = tool_def["original_endpoint"]
    
    # Generate the function signature
    params = []
    for param_name, param_info in parameters.items():
        param_type = param_info["type"]
        if param_info["required"]:
            params.append(f"{param_name}: {param_type}")
        else:
            default = param_info["default"]
            if default is None:
                params.append(f"{param_name}: {param_type} = None")
            elif isinstance(default, str):
                params.append(f'{param_name}: {param_type} = "{default}"')
            elif isinstance(default, list) and not default:
                params.append(f"{param_name}: {param_type} = []")
            else:
                params.append(f"{param_name}: {param_type} = {default}")
    
    # Calculate the indentation level for the docstring
    indent = "    "
    
    # Clean up the description for the docstring
    docstring = description.strip()
    if not docstring:
        docstring = f"{endpoint.method} {endpoint.path}"
    
    # Format the docstring
    docstring_lines = [f'"""{docstring}', ""]
    docstring_lines.append(f"Original route: {endpoint.method} {endpoint.path}")
    docstring_lines.append(f'"""')
    formatted_docstring = f"\n{indent}".join(docstring_lines)
    
    # Generate the function code
    tool_code = [
        "@mcp.tool()",
        f"async def {name}({', '.join(params)}) -> Any:",
        f"{indent}{formatted_docstring}",
    ]
    
    # Add a comment about the original handler
    tool_code.append(f"{indent}# Original handler: {endpoint.handler.__module__}.{endpoint.handler.__name__}")
    
    # Get request method
    method = endpoint.method.lower()
    
    # Build the URL path with path parameters
    url_path = endpoint.path
    path_params_dict = {}
    for param_name in endpoint.path_params:
        path_params_dict[param_name] = f"{{{param_name}}}"
    
    # Build the query parameters dictionary
    query_params = []
    for param_name in endpoint.query_params:
        query_params.append(f"{indent}if {param_name} is not None:")
        query_params.append(f"{indent}    params['{param_name}'] = {param_name}")
    
    # Create request body for applicable methods
    body_params = []
    if endpoint.body_params:
        # Add code to bundle parameters for Pydantic models
        for param_name, param_info in endpoint.body_params.items():
            param_type = param_info["type"]
            if isinstance(param_type, type) and hasattr(param_type, "__name__"):
                if hasattr(param_type, "__annotations__"):
                    fields = {}
                    for field_name in param_type.__annotations__:
                        if field_name in parameters:
                            fields[field_name] = f"{field_name}"
                    
                    if fields:
                        model_dict = ", ".join([f'"{k}": {v}' for k, v in fields.items()])
                        body_params.append(f"{indent}{param_name} = {param_type.__name__}(**{{{model_dict}}})")
                        body_params.append(f"{indent}json_data = serialize_model({param_name})")
    
    # Format the URL with path parameters
    if path_params_dict:
        formatted_path = url_path
        for param, value in path_params_dict.items():
            # Replace {param} in URL with actual parameter
            formatted_path = formatted_path.replace(f"{{{param}}}", f"{{{param}}}")
        url_code = f"{indent}url = f'{base_url}{formatted_path}'"
    else:
        url_code = f"{indent}url = '{base_url}{url_path}'"
    
    tool_code.append(url_code)
    
    # Add parameters and request code
    if endpoint.query_params:
        tool_code.append(f"{indent}params = {{}}")
        tool_code.extend(query_params)
    
    # Generate HTTP request based on method
    if method == "get":
        if endpoint.query_params:
            tool_code.append(f"{indent}response = requests.get(url, params=params)")
        else:
            tool_code.append(f"{indent}response = requests.get(url)")
    elif method == "post":
        if body_params:
            tool_code.extend(body_params)
            tool_code.append(f"{indent}response = requests.post(url, json=json_data)")
        else:
            tool_code.append(f"{indent}response = requests.post(url)")
    elif method == "put":
        if body_params:
            tool_code.extend(body_params)
            tool_code.append(f"{indent}response = requests.put(url, json=json_data)")
        else:
            tool_code.append(f"{indent}response = requests.put(url)")
    elif method == "delete":
        if endpoint.query_params:
            tool_code.append(f"{indent}response = requests.delete(url, params=params)")
        else:
            tool_code.append(f"{indent}response = requests.delete(url)")
    elif method == "patch":
        if body_params:
            tool_code.extend(body_params)
            tool_code.append(f"{indent}response = requests.patch(url, json=json_data)")
        else:
            tool_code.append(f"{indent}response = requests.patch(url)")
    
    # Add error handling
    tool_code.append(f"{indent}response.raise_for_status()")
    tool_code.append(f"{indent}return response.json()")
    
    return "\n".join(tool_code)


def generate_readme(app: FastAPI, endpoints: List[Endpoint]) -> str:
    """
    Generate a README.md file for the MCP server.
    
    Args:
        app: The FastAPI application to generate a README for.
        endpoints: The list of endpoints in the application.
        
    Returns:
        The generated README as a string.
    """
    app_title = getattr(app, "title", "FastAPI") or "FastAPI"
    app_description = getattr(app, "description", "") or "A FastAPI application"
    
    readme = [
        f"# {app_title} MCP Server",
        "",
        app_description,
        "",
        "This is an automatically generated MCP server from a FastAPI application.",
        "",
        "## Installation",
        "",
        "```bash",
        "pip install -r requirements.txt",
        "```",
        "",
        "## Running the Server",
        "",
        "```bash",
        "python server.py",
        "```",
        "",
        "## Available Tools",
        "",
    ]
    
    # Add a section for each endpoint
    for endpoint in endpoints:
        readme.append(f"### {endpoint.name}")
        
        if endpoint.description:
            readme.append("")
            readme.append(endpoint.description)
        
        readme.append("")
        readme.append(f"Original route: `{endpoint.method} {endpoint.path}`")
        
        if endpoint.path_params or endpoint.query_params or endpoint.body_params:
            readme.append("")
            readme.append("Parameters:")
            readme.append("")
            
            # Path parameters
            for param_name, param_info in endpoint.path_params.items():
                param_type = param_info["type"]
                readme.append(f"- `{param_name}` (Path parameter, type: `{param_type.__name__}`)")
            
            # Query parameters
            for param_name, param_info in endpoint.query_params.items():
                param_type = param_info["type"]
                readme.append(f"- `{param_name}` (Query parameter, type: `{param_type.__name__}`)")
            
            # Body parameters
            for param_name, param_info in endpoint.body_params.items():
                param_type = param_info["type"]
                if hasattr(param_type, "__name__"):
                    readme.append(f"- `{param_name}` (Body parameter, type: `{param_type.__name__}`)")
                else:
                    readme.append(f"- `{param_name}` (Body parameter)")
        
        readme.append("")
    
    # Add a footer
    readme.extend([
        "## Generated by FastAPI-MCP",
        "",
        "This MCP server was automatically generated by [FastAPI-MCP](https://github.com/yourusername/fastapi-mcp).",
        "",
    ])
    
    return "\n".join(readme)


def _get_simple_type_name(type_annotation):
    """
    Get a simplified string representation of a type annotation.
    
    Args:
        type_annotation: The type annotation to simplify.
        
    Returns:
        A string representation of the type.
    """
    # Handle primitive types directly
    if type_annotation is str:
        return "str"
    elif type_annotation is int:
        return "int"
    elif type_annotation is float:
        return "float"
    elif type_annotation is bool:
        return "bool"
    elif type_annotation is list:
        return "List"
    elif type_annotation is dict:
        return "Dict"
    elif type_annotation is Any:
        return "Any"
    
    # Handle PEP 604 union types (X | Y) in Python 3.10+
    if PY310_OR_HIGHER:
        if (hasattr(type_annotation, "__or__") or 
            (hasattr(type_annotation, "__origin__") and str(type_annotation.__origin__) == "types.UnionType")):
            args = getattr(type_annotation, "__args__", [])
            
            # Check if this is equivalent to Optional[T]
            if any(arg is type(None) for arg in args):
                # Get the non-None type
                non_none_args = [arg for arg in args if arg is not type(None)]
                if len(non_none_args) == 1:
                    return f"Optional[{_get_simple_type_name(non_none_args[0])}]"
            
            # Regular Union
            arg_strs = [_get_simple_type_name(arg) for arg in args]
            return f"Union[{', '.join(arg_strs)}]"
    
    if hasattr(type_annotation, "__origin__"):
        # Handle generics like List, Dict, etc.
        origin = get_origin(type_annotation)
        args = get_args(type_annotation)
        
        if origin is list or str(origin).endswith("list"):
            if args:
                return f"List[{_get_simple_type_name(args[0])}]"
            return "List"
        elif origin is dict or str(origin).endswith("dict"):
            if len(args) == 2:
                return f"Dict[{_get_simple_type_name(args[0])}, {_get_simple_type_name(args[1])}]"
            return "Dict"
        elif origin is Union or str(origin).endswith("Union"):
            # Check if this is equivalent to Optional[T]
            if len(args) == 2 and args[1] is type(None):  # noqa
                return f"Optional[{_get_simple_type_name(args[0])}]"
                
            # Regular Union
            arg_strs = [_get_simple_type_name(arg) for arg in args]
            return f"Union[{', '.join(arg_strs)}]"
        else:
            # Other generic types
            try:
                return str(type_annotation).replace("typing.", "")
            except:
                return "Any"
    elif hasattr(type_annotation, "__name__"):
        # Regular classes
        return type_annotation.__name__
    else:
        # Fallback
        try:
            return str(type_annotation).replace("typing.", "")
        except:
            return "Any"


def get_model_fields(model_class):
    """
    Get all fields for a Pydantic model class.
    
    Args:
        model_class: The Pydantic model class to extract fields from.
        
    Returns:
        A dictionary of field information.
    """
    annotations = getattr(model_class, "__annotations__", {})
    fields = {}
    
    # Try to inspect Field objects directly from the model
    for field_name, field_type in annotations.items():
        # Try to get Field object if available
        field_obj = getattr(model_class, field_name, None)
        
        # Check if it's required or has a default
        required = True
        default = None
        
        # Try to determine if it's a pydantic Field
        if hasattr(field_obj, "default") and hasattr(field_obj, "default_factory"):
            # Looks like a Pydantic Field object
            if field_obj.default is not ...:
                default = field_obj.default
                required = False
            elif field_obj.default_factory is not None:
                try:
                    default = field_obj.default_factory()
                    required = False
                except:
                    pass
        
        # Check for Optional type (PEP 604 union types)
        is_optional = False
        clean_type = field_type  # Store the cleaned type
        
        # Handle PEP 604 union types (X | Y) in Python 3.10+
        if PY310_OR_HIGHER:
            if (hasattr(field_type, "__or__") or 
                (hasattr(field_type, "__origin__") and str(field_type.__origin__) == "types.UnionType")):
                args = getattr(field_type, "__args__", [])
                if any(arg is type(None) for arg in args):
                    is_optional = True
                    required = False
                    # Extract the non-None type
                    non_none_args = [arg for arg in args if arg is not type(None)]
                    if len(non_none_args) == 1:
                        clean_type = non_none_args[0]
        
        # Check for traditional Union with None type
        if hasattr(field_type, "__origin__") and field_type.__origin__ is Union:
            args = field_type.__args__
            if any(arg is type(None) for arg in args):
                is_optional = True
                required = False
                # Extract the non-None type
                non_none_args = [arg for arg in args if arg is not type(None)]
                if len(non_none_args) == 1:
                    clean_type = non_none_args[0]
        
        # Add the field info
        fields[field_name] = {
            "type": clean_type,
            "required": required and not is_optional,
            "default": default,
            "optional": is_optional
        }
    
    return fields 