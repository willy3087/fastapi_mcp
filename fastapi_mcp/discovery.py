"""
Discovery module for finding FastAPI endpoints.
"""

import inspect
import sys
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, get_type_hints, Union

import fastapi
from fastapi import APIRouter, FastAPI, Query
from fastapi.routing import APIRoute
try:
    # Pydantic v2
    from pydantic import BaseModel
except ImportError:
    # Pydantic v1 fallback
    from pydantic import BaseModel

# Check if Python version supports PEP 604 (|) union types
PY310_OR_HIGHER = sys.version_info >= (3, 10)


class Endpoint:
    """
    Represents a FastAPI endpoint.
    """
    
    def __init__(
        self,
        path: str,
        method: str,
        handler: Callable,
        name: str,
        description: Optional[str] = None,
        request_model: Optional[Type[BaseModel]] = None,
        response_model: Optional[Type[BaseModel]] = None,
        path_params: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        body_params: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[Any]] = None,
    ):
        self.path = path
        self.method = method
        self.handler = handler
        self.name = name
        self.description = description
        self.request_model = request_model
        self.response_model = response_model
        self.path_params = path_params or {}
        self.query_params = query_params or {}
        self.body_params = body_params or {}
        self.dependencies = dependencies or []
        self.return_type = self._get_return_type()
    
    def _get_return_type(self) -> Optional[Type]:
        """
        Get the return type of the handler.
        """
        try:
            type_hints = get_type_hints(self.handler)
            return type_hints.get("return")
        except (TypeError, ValueError):
            return None
    
    def __repr__(self) -> str:
        return f"<Endpoint {self.method} {self.path}>"


def discover_fastapi_app(app: FastAPI) -> List[Endpoint]:
    """
    Discover all endpoints in a FastAPI application.
    
    Args:
        app: The FastAPI application to discover endpoints in.
        
    Returns:
        A list of Endpoint objects representing all endpoints in the application.
    """
    endpoints = []
    
    # Get all routes from the app
    routes = get_all_routes(app)
    
    # Process each route
    for route in routes:
        if not isinstance(route, APIRoute):
            continue
        
        # Skip automatically generated openapi and docs routes
        if route.path.startswith("/openapi") or route.path.startswith("/docs") or route.path.startswith("/redoc"):
            continue
        
        # Get the HTTP methods for this route
        methods = route.methods or {"GET"}
        
        for method in methods:
            # Skip HEAD and OPTIONS methods
            if method in {"HEAD", "OPTIONS"}:
                continue
            
            # Parse the endpoint parameters
            path_params, query_params, body_params = parse_endpoint_params(route)
            
            # Get the handler name
            handler_name = get_handler_name(route.endpoint)
            
            # Get the handler description
            description = route.description or getattr(route.endpoint, "__doc__", None)
            
            # Create an Endpoint object
            endpoint = Endpoint(
                path=route.path,
                method=method,
                handler=route.endpoint,
                name=handler_name,
                description=description,
                request_model=route.body_field.type_ if hasattr(route, 'body_field') and route.body_field else None,
                response_model=route.response_model,
                path_params=path_params,
                query_params=query_params,
                body_params=body_params,
                dependencies=route.dependencies,
            )
            
            endpoints.append(endpoint)
    
    return endpoints


def get_all_routes(app: FastAPI) -> List[APIRoute]:
    """
    Get all routes from a FastAPI application, including those in nested routers.
    
    Args:
        app: The FastAPI application to get routes from.
        
    Returns:
        A list of all APIRoute objects in the application.
    """
    routes = []
    
    # Get routes directly from the app
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes.append(route)
        elif isinstance(route, APIRouter):
            # Handle mounted APIRouters
            routes.extend(get_router_routes(route))
    
    return routes


def get_router_routes(router: APIRouter) -> List[APIRoute]:
    """
    Get all routes from an APIRouter, including those in nested routers.
    
    Args:
        router: The APIRouter to get routes from.
        
    Returns:
        A list of all APIRoute objects in the router.
    """
    routes = []
    
    for route in router.routes:
        if isinstance(route, APIRoute):
            routes.append(route)
        elif isinstance(route, APIRouter):
            # Handle nested routers
            routes.extend(get_router_routes(route))
    
    return routes


def parse_endpoint_params(route: APIRoute) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Parse the parameters of an endpoint.
    
    Args:
        route: The APIRoute to parse parameters for.
        
    Returns:
        A tuple of (path_params, query_params, body_params) dictionaries.
    """
    path_params = {}
    query_params = {}
    body_params = {}
    
    # Get the signature of the endpoint function
    sig = inspect.signature(route.endpoint)
    
    # Process each parameter
    for name, param in sig.parameters.items():
        # Skip self, cls, and **kwargs
        if name in {"self", "cls"} or param.kind == inspect.Parameter.VAR_KEYWORD:
            continue
        
        # Get the parameter type hint
        annotation = param.annotation
        if annotation is inspect.Parameter.empty:
            annotation = Any
        
        # Get the default value
        default = None if param.default is inspect.Parameter.empty else param.default
        
        # Check if this is a path parameter
        if f"{{{name}}}" in route.path:
            path_params[name] = {
                "type": annotation,
                "default": default,
            }
        # Check if this is a body parameter (Pydantic model)
        elif isinstance(annotation, type) and issubclass(annotation, BaseModel):
            body_params[name] = {
                "type": annotation,
                "default": default,
            }
        # Otherwise, it's a query parameter
        else:
            # Simplify the annotation if it's a complex type
            simplified_annotation = annotation
            
            # Handle PEP 604 union types (X | Y) in Python 3.10+
            if PY310_OR_HIGHER:
                if (hasattr(annotation, "__or__") or 
                    (hasattr(annotation, "__origin__") and str(annotation.__origin__) == "types.UnionType")):
                    args = getattr(annotation, "__args__", [])
                    for arg in args:
                        if arg is not type(None):  # noqa
                            simplified_annotation = arg
                            break
            
            # Handle traditional Union types
            if hasattr(annotation, "__origin__") and annotation.__origin__ is Union:
                for arg in getattr(annotation, "__args__", []):
                    if arg is not type(None):  # noqa
                        simplified_annotation = arg
                        break
            
            # Extract information from Query if it's used
            if default is not None and hasattr(default, "__class__") and default.__class__.__name__ == "Query":
                # Handle different Query parameter styles for FastAPI
                try:
                    # FastAPI >= 0.95.0 with Pydantic v2
                    query_default = getattr(default, "default", None)
                except AttributeError:
                    # Try to get default from Query object
                    query_default = None
                    for attr_name in dir(default):
                        if attr_name.startswith('_') and hasattr(default, attr_name):
                            attr = getattr(default, attr_name)
                            if hasattr(attr, 'default'):
                                query_default = attr.default
                                break
                
                query_params[name] = {
                    "type": simplified_annotation,
                    "default": query_default,
                }
            else:
                query_params[name] = {
                    "type": simplified_annotation,
                    "default": default,
                }
    
    return path_params, query_params, body_params


def get_handler_name(handler: Callable) -> str:
    """
    Get the name of a handler function.
    
    Args:
        handler: The handler function to get the name of.
        
    Returns:
        The name of the handler function.
    """
    if hasattr(handler, "__name__"):
        return handler.__name__
    
    # For async handlers wrapped with other decorators
    if hasattr(handler, "__wrapped__"):
        return get_handler_name(handler.__wrapped__)
    
    # Fallback to a default name
    return "handler" 