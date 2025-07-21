"""Endpoint registry for syft-widget

This module provides the registration mechanism for API endpoints.
Endpoints are defined at module level so they can be pickled for multiprocessing.
"""

from typing import Dict, Any, Callable


# Registry to hold all endpoints
ENDPOINT_REGISTRY: Dict[str, Callable[[], Any]] = {}


def register_endpoint(path: str):
    """Decorator to register an endpoint
    
    Example:
        @register_endpoint("/api/data")
        def get_data():
            return {"value": 42}
    """
    def decorator(func):
        ENDPOINT_REGISTRY[path] = func
        return func
    return decorator


def get_all_endpoints() -> Dict[str, Callable[[], Any]]:
    """Get all registered endpoints"""
    return ENDPOINT_REGISTRY.copy()


# Import demo endpoints to register them
# This ensures they're available when the module is imported
try:
    from . import demo_endpoints
except ImportError:
    # Demo endpoints are optional
    pass