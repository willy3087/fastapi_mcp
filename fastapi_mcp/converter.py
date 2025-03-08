"""
Converter module for converting FastAPI endpoints to MCP tools.
"""

import inspect
import sys
from typing import Any, Callable, Dict, List, Optional, Type, Union, get_type_hints

from fastapi import FastAPI
from fastapi.routing import APIRoute
try:
    # Pydantic v2
    from pydantic import BaseModel, create_model
    from pydantic.fields import FieldInfo
except ImportError:
    # Pydantic v1 fallback
    from pydantic import BaseModel, create_model
    from pydantic.fields import FieldInfo

from fastapi_mcp.discovery import Endpoint

# Check if Python version supports PEP 604 (|) union types
PY310_OR_HIGHER = sys.version_info >= (3, 10)


def convert_endpoint_to_mcp_tool(endpoint: Endpoint) -> Dict[str, Any]:
    """
    Convert a FastAPI endpoint to an MCP tool definition.
    
    Args:
        endpoint: The endpoint to convert.
        
    Returns:
        A dictionary representing the MCP tool definition.
    """
    # Extract relevant information from the endpoint
    name = endpoint.name
    description = endpoint.description or f"{endpoint.method} {endpoint.path}"
    
    # Combine all parameters
    params = {}
    
    # Add path parameters
    for param_name, param_info in endpoint.path_params.items():
        params[param_name] = {
            "type": _convert_type_annotation(param_info["type"]),
            "description": f"Path parameter: {param_name}",
            "required": param_info["default"] is None,
            "default": param_info["default"],
        }
    
    # Add query parameters
    for param_name, param_info in endpoint.query_params.items():
        params[param_name] = {
            "type": _convert_type_annotation(param_info["type"]),
            "description": f"Query parameter: {param_name}",
            "required": param_info["default"] is None,
            "default": param_info["default"],
        }
    
    # Add body parameters
    for param_name, param_info in endpoint.body_params.items():
        param_type = param_info["type"]
        
        if isinstance(param_type, type) and issubclass(param_type, BaseModel):
            # For Pydantic models, flatten the fields
            try:
                # Pydantic v2
                model_fields = param_type.model_fields
                for field_name, field in model_fields.items():
                    field_description = getattr(field, "description", f"Field: {field_name}")
                    field_default = getattr(field, "default", None)
                    field_required = field_default is None and not field.is_optional
                    
                    params[field_name] = {
                        "type": _convert_type_annotation(field.annotation),
                        "description": field_description,
                        "required": field_required,
                        "default": None if field_default == ... else field_default,
                    }
            except AttributeError:
                # Pydantic v1 fallback
                model_fields = {}
                for field_name, field in getattr(param_type, "__fields__", {}).items():
                    field_description = getattr(field, "description", f"Field: {field_name}")
                    field_required = getattr(field, "required", True)
                    field_default = getattr(field, "default", None)
                    model_fields[field_name] = {
                        "description": field_description,
                        "required": field_required,
                        "default": field_default,
                    }
                
                for field_name, field_info in model_fields.items():
                    field_type = param_type.__annotations__.get(field_name, Any)
                    params[field_name] = {
                        "type": _convert_type_annotation(field_type),
                        "description": field_info["description"],
                        "required": field_info["required"],
                        "default": field_info["default"],
                    }
        else:
            # For non-Pydantic types
            params[param_name] = {
                "type": _convert_type_annotation(param_type),
                "description": f"Body parameter: {param_name}",
                "required": param_info["default"] is None,
                "default": param_info["default"],
            }
    
    # Determine the return type
    return_type = _convert_type_annotation(endpoint.return_type or Any)
    
    # Build the MCP tool definition
    tool_def = {
        "name": name,
        "description": description,
        "parameters": params,
        "return_type": return_type,
        "handler": _create_handler_wrapper(endpoint),
        "original_endpoint": endpoint,
    }
    
    return tool_def


def _create_handler_wrapper(endpoint: Endpoint) -> Callable:
    """
    Create a wrapper function that calls the original endpoint handler.
    
    Args:
        endpoint: The endpoint to create a wrapper for.
        
    Returns:
        A function that wraps the original handler.
    """
    async def handler_wrapper(**kwargs):
        """
        Wrapper function for the endpoint handler.
        """
        # Extract the original handler
        original_handler = endpoint.handler
        
        # Prepare arguments
        handler_kwargs = {}
        
        # Extract path parameters
        for param_name in endpoint.path_params:
            if param_name in kwargs:
                handler_kwargs[param_name] = kwargs[param_name]
        
        # Extract query parameters
        for param_name in endpoint.query_params:
            if param_name in kwargs:
                handler_kwargs[param_name] = kwargs[param_name]
        
        # Handle body parameters
        for param_name, param_info in endpoint.body_params.items():
            param_type = param_info["type"]
            
            if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                # For Pydantic models, collect fields
                model_fields = {}
                try:
                    # Pydantic v2
                    for field_name in param_type.model_fields:
                        if field_name in kwargs:
                            model_fields[field_name] = kwargs[field_name]
                except AttributeError:
                    # Pydantic v1 fallback
                    for field_name in param_type.__annotations__:
                        if field_name in kwargs:
                            model_fields[field_name] = kwargs[field_name]
                
                # Create the model instance
                model_instance = param_type(**model_fields)
                handler_kwargs[param_name] = model_instance
            elif param_name in kwargs:
                handler_kwargs[param_name] = kwargs[param_name]
        
        # Call the original handler
        if inspect.iscoroutinefunction(original_handler):
            result = await original_handler(**handler_kwargs)
        else:
            result = original_handler(**handler_kwargs)
        
        return result
    
    # Copy metadata from the original handler
    handler_wrapper.__name__ = endpoint.name
    handler_wrapper.__doc__ = endpoint.description
    
    return handler_wrapper


def _convert_type_annotation(annotation: Any) -> str:
    """
    Convert a Python type annotation to a string representation for Python.
    
    Args:
        annotation: The type annotation to convert.
        
    Returns:
        A string representation of the type.
    """
    if annotation is None or annotation is inspect.Parameter.empty:
        return "Any"
    
    # Handle special cases
    if annotation is Any:
        return "Any"
    elif annotation is str:
        return "str"
    elif annotation is int:
        return "int"
    elif annotation is float:
        return "float"
    elif annotation is bool:
        return "bool"
    elif annotation is list or getattr(annotation, "__origin__", None) is list:
        return "list"
    elif annotation is dict or getattr(annotation, "__origin__", None) is dict:
        return "dict"
    elif isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return "dict"
    
    # Handle PEP 604 union types (X | Y) in Python 3.10+
    if PY310_OR_HIGHER:
        # Check if the annotation has the __or__ method, indicating it's a type that can be used with |
        # or if it has the __origin__ attribute that matches types.UnionType
        if (hasattr(annotation, "__or__") or 
            (hasattr(annotation, "__origin__") and str(annotation.__origin__) == "types.UnionType")):
            # Get the args of the union
            args = getattr(annotation, "__args__", [])
            # Filter out NoneType to handle Optional types
            for arg in args:
                if arg is not type(None):  # noqa
                    return _convert_type_annotation(arg)
            return "Any"
    
    # Try to handle Union types
    if hasattr(annotation, "__origin__") and annotation.__origin__ is Union:
        for arg in getattr(annotation, "__args__", []):
            if arg is not type(None):  # noqa
                return _convert_type_annotation(arg)
        return "Any"
    
    # Default to string for other types
    return "str" 