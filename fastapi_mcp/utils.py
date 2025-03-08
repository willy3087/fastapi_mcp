"""
Utility functions for FastAPI-MCP.
"""

import importlib.util
import inspect
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Optional, TypeVar

from fastapi import FastAPI

T = TypeVar("T")


def load_module_from_path(path: Path) -> ModuleType:
    """
    Load a Python module from a file path.
    
    Args:
        path: The path to the Python file.
        
    Returns:
        The loaded module.
    """
    module_name = path.stem
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    
    return module


def find_fastapi_app(module: ModuleType, var_name: str = None) -> Optional[FastAPI]:
    """
    Find a FastAPI application in a module.
    
    Args:
        module: The module to search in.
        var_name: The name of the variable to look for. If None, will try to find any FastAPI app.
        
    Returns:
        The FastAPI application if found, None otherwise.
    """
    # If a var_name is provided, try to find it directly
    if var_name is not None:
        obj = getattr(module, var_name, None)
        if obj is not None and isinstance(obj, FastAPI):
            return obj
        return None
        
    # Otherwise, check all attributes of the module
    for attr_name in dir(module):
        if is_dunder(attr_name):
            continue
        
        try:
            attr = getattr(module, attr_name)
            if isinstance(attr, FastAPI):
                return attr
        except Exception:
            continue
    
    return None


def find_object_by_name(module: ModuleType, name: str) -> Optional[Any]:
    """
    Find an object in a module by its name.
    
    Args:
        module: The module to search in.
        name: The name of the object to find.
        
    Returns:
        The object if found, None otherwise.
    """
    # Check if the name is a direct attribute of the module
    if hasattr(module, name):
        return getattr(module, name)
    
    # Check if the name contains dots (e.g., "package.module.object")
    if "." in name:
        parts = name.split(".")
        obj = module
        
        for part in parts:
            if not hasattr(obj, part):
                return None
            obj = getattr(obj, part)
        
        return obj
    
    return None


def is_dunder(name: str) -> bool:
    """
    Check if a name is a dunder name (starts and ends with double underscores).
    
    Args:
        name: The name to check.
        
    Returns:
        True if the name is a dunder name, False otherwise.
    """
    return name.startswith("__") and name.endswith("__")


def get_all_functions(obj: Any) -> Dict[str, Any]:
    """
    Get all functions defined in an object.
    
    Args:
        obj: The object to get functions from.
        
    Returns:
        A dictionary mapping function names to function objects.
    """
    functions = {}
    
    for name, value in inspect.getmembers(obj):
        # Skip dunder methods
        if is_dunder(name):
            continue
        
        # Skip non-callable attributes
        if not callable(value):
            continue
        
        # Skip methods defined in parent classes
        if inspect.ismethod(value) and value.__self__.__class__ is not obj.__class__:
            continue
        
        functions[name] = value
    
    return functions


def get_absolute_import_path(obj: Any) -> str:
    """
    Get the absolute import path for an object.
    
    Args:
        obj: The object to get the import path for.
        
    Returns:
        The absolute import path (e.g., "package.module.function").
    """
    module = inspect.getmodule(obj)
    if module is None:
        return obj.__name__
    
    module_name = module.__name__
    if module_name == "__main__":
        return obj.__name__
    
    return f"{module_name}.{obj.__name__}" 