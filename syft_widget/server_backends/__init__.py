"""Server backend using syft-serve for automatic process management

This module provides server management via syft-serve, which handles
automatic process spawning, port management, and server lifecycle.
"""

from .base import ServerBackend
from .syft_serve_backend import SyftServeBackend  

def get_server_backend():
    """Get the syft-serve backend
    
    Returns:
        SyftServeBackend: The syft-serve backend instance
        
    Raises:
        ImportError: If syft-serve is not available (should not happen as it's a required dependency)
    """
    return SyftServeBackend()

def syft_serve_available():
    """Check if syft-serve is available
    
    Returns:
        bool: Should always be True since syft-serve is a required dependency
    """
    try:
        import syft_serve
        return True
    except ImportError:
        return False

__all__ = ['ServerBackend', 'SyftServeBackend', 'get_server_backend', 'syft_serve_available']