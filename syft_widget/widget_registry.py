"""Registry for managing the shared widget infrastructure"""
from typing import Optional
from .managed_widget import ManagedWidget
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
    
    def start(self, thread_port: int = 8001, syftbox_port: int = 8002):
        """Start the shared infrastructure if not already running"""
        if not self._widget:
            # Get all registered endpoints
            endpoints = get_all_endpoints()
            
            print(f"Starting widget infrastructure with {len(endpoints)} endpoints:")
            for path in sorted(endpoints.keys()):
                print(f"  {path}")
            
            # Create managed widget with all endpoints
            # We'll create it but not display it
            self._widget = ManagedWidget(
                thread_server_port=thread_port,
                endpoints=endpoints
            )
            
            # Override display to prevent showing the widget
            self._widget.display = lambda: None
            
            print(f"\nInfrastructure started:")
            print(f"  Thread server port: {thread_port}")
            print(f"  SyftBox port: {syftbox_port}")
    
    def get_base_url(self) -> Optional[str]:
        """Get the current active server URL"""
        if not self._widget:
            return None
            
        # Check which stage we're in
        if hasattr(self._widget, 'syftbox_manager') and self._widget.syftbox_manager:
            if self._widget.syftbox_manager.is_syftbox_running:
                return self._widget.syftbox_manager.syftbox_server_url
        
        # Default to thread server
        return f"http://localhost:{self._widget.thread_server_port}"
    
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


def start_infrastructure(thread_port: int = 8001, syftbox_port: int = 8002):
    """Convenience function to start the infrastructure"""
    _registry.start(thread_port, syftbox_port)


def stop_infrastructure():
    """Convenience function to stop the infrastructure"""
    _registry.stop()