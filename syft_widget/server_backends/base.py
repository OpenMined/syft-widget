"""Base class for server backends

This module defines the abstract interface that all server backends must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Callable, Optional, Any, List

class ServerBackend(ABC):
    """Abstract base class for server management backends
    
    This class defines the interface that all server backends must implement,
    whether they use syft-serve, legacy server management, or future backends.
    """
    
    @abstractmethod
    def create_server(self, name: str, endpoints: Dict[str, Callable], **kwargs) -> Any:
        """Create a new server
        
        Args:
            name: Unique server name
            endpoints: Dictionary mapping endpoint paths to handler functions
            **kwargs: Additional backend-specific options
            
        Returns:
            Server handle or identifier
        """
        pass
    
    @abstractmethod  
    def get_server_url(self, server_id: str) -> Optional[str]:
        """Get server URL by ID
        
        Args:
            server_id: Server identifier
            
        Returns:
            Server URL if available, None otherwise
        """
        pass
    
    @abstractmethod
    def stop_server(self, server_id: str) -> None:
        """Stop a specific server
        
        Args:
            server_id: Server identifier to stop
        """
        pass
    
    @abstractmethod
    def stop_all_servers(self) -> None:
        """Stop all managed servers"""
        pass
    
    @abstractmethod
    def get_server_status(self, server_id: str) -> str:
        """Get server status
        
        Args:
            server_id: Server identifier
            
        Returns:
            Status string ('running', 'stopped', 'error', etc.)
        """
        pass
    
    @abstractmethod
    def list_servers(self) -> List[Dict[str, Any]]:
        """List all managed servers
        
        Returns:
            List of server information dictionaries
        """
        pass