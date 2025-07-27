"""SyftServe backend implementation

This module provides the syft-serve backend for server management.
"""

from typing import Dict, Callable, Optional, Any, List
from .base import ServerBackend

class SyftServeBackend(ServerBackend):
    """Server backend using syft-serve
    
    This backend leverages syft-serve for advanced server management including:
    - Process isolation
    - Dependency management  
    - Automatic port discovery
    - Server persistence
    """
    
    def __init__(self):
        self._widget_server_map = {}  # widget_id -> server_name
        
        # Import syft-serve (will fail gracefully if not available)
        try:
            import syft_serve
            self._syft_serve = syft_serve
            self._available = True
        except ImportError:
            self._syft_serve = None
            self._available = False
    
    def create_server(self, name: str, endpoints: Dict[str, Callable], 
                     dependencies: Optional[List[str]] = None, **kwargs) -> Any:
        """Create server using syft-serve
        
        Args:
            name: Server name
            endpoints: Endpoint dictionary
            dependencies: Optional Python packages to install
            **kwargs: Additional options (force_new_server, etc.)
            
        Returns:
            syft-serve ServerHandle
        """
        if not self._available:
            raise RuntimeError("syft-serve is not available. Install with: pip install syft-serve")
        
        # Add default dependencies for widgets
        default_deps = ["fastapi>=0.100.0", "uvicorn[standard]>=0.23.0", "requests>=2.28.0"]
        all_deps = default_deps + (dependencies or [])
        
        server = self._syft_serve.create(
            name=name,
            endpoints=endpoints,
            dependencies=all_deps,
            force=kwargs.get('force_new_server', False),
            expiration_seconds=kwargs.get('expiration_seconds', 86400)  # Default 24 hours for widgets
        )
        
        return server
    
    def get_server_url(self, server_name: str) -> Optional[str]:
        """Get server URL from syft-serve registry
        
        Args:
            server_name: Name of the server
            
        Returns:
            Server URL if found
        """
        if not self._available:
            return None
            
        servers = self._syft_serve.servers
        if server_name in servers:
            return servers[server_name].url
        return None
    
    def stop_server(self, server_name: str) -> None:
        """Stop specific server
        
        Args:
            server_name: Name of server to stop
        """
        if not self._available:
            return
            
        servers = self._syft_serve.servers
        if server_name in servers:
            servers[server_name].terminate()
    
    def stop_all_servers(self) -> None:
        """Stop all syft-serve servers"""
        if not self._available:
            return
            
        self._syft_serve.terminate_all()
    
    def get_server_status(self, server_name: str) -> str:
        """Get server status from syft-serve
        
        Args:
            server_name: Name of server
            
        Returns:
            Status string
        """
        if not self._available:
            return "backend_unavailable"
            
        servers = self._syft_serve.servers
        if server_name in servers:
            return servers[server_name].status
        return "not_found"
    
    def list_servers(self) -> List[Dict[str, Any]]:
        """List all syft-serve servers
        
        Returns:
            List of server information
        """
        if not self._available:
            return []
            
        servers = self._syft_serve.servers
        return [
            {
                'name': name,
                'url': server.url,
                'status': server.status,
                'backend': 'syft-serve'
            }
            for name, server in servers.items()
        ]
    
    def create_infrastructure_server(self, endpoints: Dict[str, Callable], **kwargs):
        """Create the main infrastructure server for APIDisplay widgets
        
        Args:
            endpoints: Endpoint dictionary
            **kwargs: Additional options
            
        Returns:
            Server handle
        """
        return self.create_server(
            name="syft_widget_infrastructure",
            endpoints=endpoints,
            dependencies=kwargs.get('dependencies'),
            force_new_server=True  # Always replace infrastructure server
        )
    
    def stop_infrastructure_server(self):
        """Stop the infrastructure server"""
        self.stop_server("syft_widget_infrastructure")
    
    def get_infrastructure_url(self) -> Optional[str]:
        """Get infrastructure server URL
        
        Returns:
            Infrastructure server URL if available
        """
        return self.get_server_url("syft_widget_infrastructure")