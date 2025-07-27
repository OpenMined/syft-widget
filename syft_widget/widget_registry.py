"""Registry for managing the shared widget infrastructure

This registry uses syft-serve for automatic server management,
handling process spawning, port allocation, and server lifecycle.
"""

from typing import Optional
from .server_backends import get_server_backend


class WidgetRegistry:
    """Registry using syft-serve for automatic server management
    
    This class provides a simple interface for managing widget infrastructure
    using syft-serve for all server operations.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._backend = get_server_backend()
        self._infrastructure_running = False
    
    def start(self, endpoints=None, thread_port: int = 8001, syftbox_port: int = 8002, 
              mode: str = "auto", app_name: str = "syft-widget", 
              repo_url: str = "https://github.com/OpenMined/syft-widget", 
              verbose: bool = True, dependencies=None):
        """Start the shared infrastructure using server backend
        
        Args:
            endpoints: Dictionary of endpoints to serve
            thread_port: Preferred port for thread server (may be ignored by backend)
            syftbox_port: Deprecated, kept for compatibility
            mode: Server mode - auto, development, or production
            app_name: Name of the SyftBox app to manage
            repo_url: GitHub repository URL for the app
            verbose: Whether to show startup and monitoring logs
            dependencies: Optional list of Python packages for the server
        """
        if endpoints is None:
            endpoints = {}
            if verbose:
                print("No endpoints provided - using empty endpoint set")
        
        try:
            if verbose:
                print(f"Starting infrastructure using syft-serve...")
            
            # Create infrastructure server using backend
            server_handle = self._backend.create_infrastructure_server(
                endpoints=endpoints,
                dependencies=dependencies
            )
            
            self._infrastructure_running = True
            
            if verbose:
                server_url = self._backend.get_infrastructure_url()
                print(f"✅ Infrastructure started successfully")
                if server_url:
                    print(f"   Server URL: {server_url}")
                print(f"   Mode: {mode}")
                print(f"   Backend: syft-serve")
        
        except Exception as e:
            if verbose:
                print(f"❌ Failed to start infrastructure: {e}")
            self._infrastructure_running = False
            raise
    
    def get_base_url(self) -> Optional[str]:
        """Get the current active server URL
        
        Returns:
            Server URL if infrastructure is running
        """
        if not self._infrastructure_running:
            return None
        
        return self._backend.get_infrastructure_url()
    
    def stop(self):
        """Stop the infrastructure"""
        try:
            self._backend.stop_infrastructure_server()
            self._infrastructure_running = False
        except Exception as e:
            print(f"Warning: Error stopping infrastructure: {e}")


# Global registry instance
_registry = WidgetRegistry()


def get_current_registry():
    """Get the current registry instance
    
    Returns:
        WidgetRegistry: Global registry instance
    """
    return _registry


def start_infrastructure(thread_port: int = 8001, syftbox_port: int = 8002, mode: str = "auto", 
                        app_name: str = "syft-widget", 
                        repo_url: str = "https://github.com/OpenMined/syft-widget", 
                        verbose: bool = True, dependencies=None):
    """Convenience function to start the infrastructure
    
    This function provides a clean interface for starting widget infrastructure
    with automatic backend selection and simplified configuration.
    
    Args:
        thread_port: Port for the thread server (default: 8001)
        syftbox_port: Deprecated, kept for compatibility
        mode: "development", "production", or "auto" (default)
        app_name: Name of the SyftBox app to manage (default: "syft-widget")
        repo_url: GitHub repository URL for the app
        verbose: Whether to show startup logs (default: True)
        dependencies: Optional list of Python packages for the server
    """
    # Use empty endpoints by default
    endpoints = {}
    
    _registry.start(
        endpoints=endpoints,
        thread_port=thread_port,
        syftbox_port=syftbox_port,
        mode=mode,
        app_name=app_name,
        repo_url=repo_url,
        verbose=verbose,
        dependencies=dependencies
    )


def stop_infrastructure():
    """Convenience function to stop the infrastructure"""
    _registry.stop()


def get_infrastructure_status():
    """Get infrastructure status information
    
    Returns:
        dict: Status information including backend type and server details
    """
    registry = get_current_registry()
    
    status = {
        "running": registry._infrastructure_running,
        "backend": "syft-serve",
        "base_url": registry.get_base_url()
    }
    
    # Add backend-specific information
    try:
        if hasattr(registry._backend, 'list_servers'):
            servers = registry._backend.list_servers()
            status["servers"] = servers
            status["server_count"] = len(servers)
    except:
        pass
    
    return status