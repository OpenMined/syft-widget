"""Registry for managing the shared widget infrastructure"""
from typing import Optional
from .endpoints import get_all_endpoints


class WidgetRegistry:
    """Manages the shared infrastructure for all display objects"""
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
        self._widget = None
    
    def start(self, thread_port: int = 8001, syftbox_port: int = 8002, mode: str = "auto",
              app_name: str = "syft-widget", repo_url: str = "https://github.com/OpenMined/syft-widget"):
        """Start the shared infrastructure if not already running
        
        Args:
            thread_port: Port for the thread server
            syftbox_port: Port for the SyftBox app (deprecated, auto-discovered)
            mode: "development" (no SyftBox), "production" (full), or "auto" (default)
            app_name: Name of the SyftBox app to manage
            repo_url: GitHub repository URL for the app
        """
        if not self._widget:
            # Lazy import to avoid circular dependency
            from .managed_widget import ManagedWidget
            
            # Get all registered endpoints
            endpoints = get_all_endpoints()
            
            print(f"Starting widget infrastructure with {len(endpoints)} endpoints:")
            for path in sorted(endpoints.keys()):
                print(f"  {path}")
            
            # Create managed widget with all endpoints
            # We'll create it but not display it
            self._widget = ManagedWidget(
                thread_server_port=thread_port,
                endpoints=endpoints,
                mode=mode,
                app_name=app_name,
                repo_url=repo_url
            )
            
            # Override display to prevent showing the widget
            self._widget.display = lambda: None
            
            print(f"\nInfrastructure started:")
            print(f"  Mode: {mode}")
            print(f"  Thread server port: {thread_port}")
            if mode != "development":
                print(f"  SyftBox: auto-discovery enabled")
    
    def get_base_url(self) -> Optional[str]:
        """Get the current active server URL"""
        if not self._widget:
            return None
            
        # Return the widget's current server URL which is updated when ports change
        return self._widget.server_url
    
    def stop(self):
        """Stop the infrastructure"""
        if self._widget:
            self._widget.stop()
            self._widget = None
            print("Widget infrastructure stopped")


# Global registry instance
_registry = WidgetRegistry()


def get_current_registry():
    """Get the current registry instance"""
    return _registry


def start_infrastructure(thread_port: int = 8001, syftbox_port: int = 8002, mode: str = "auto", 
                        app_name: str = "syft-widget", repo_url: str = "https://github.com/OpenMined/syft-widget"):
    """Convenience function to start the infrastructure
    
    Args:
        thread_port: Port for the thread server (default: 8001)
        syftbox_port: Deprecated, kept for compatibility
        mode: "development", "production", or "auto" (default)
            - development: Only checkpoint and thread server (no SyftBox)
            - production: Full lifecycle with SyftBox
            - auto: Detect based on environment
        app_name: Name of the SyftBox app to manage (default: "syft-widget")
        repo_url: GitHub repository URL for the app (default: "https://github.com/OpenMined/syft-widget")
    """
    _registry.start(thread_port, syftbox_port, mode, app_name, repo_url)


def stop_infrastructure():
    """Convenience function to stop the infrastructure"""
    _registry.stop()