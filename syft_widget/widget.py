from typing import Dict, Any, Optional, Callable


class SyftWidget:
    """Base class for widgets - provides minimal interface for ManagedWidget"""
    
    def __init__(
        self,
        server_url: str = "http://localhost:8000",
        check_interval: float = 1.0,
        endpoints: Optional[Dict[str, Callable[[], Any]]] = None
    ):
        self.server_url = server_url
        self.check_interval = check_interval
        self.endpoints = endpoints or {}
    
    def stop(self):
        """Stop the widget (for compatibility)"""
        pass


