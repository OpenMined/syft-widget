from typing import Dict, Any, Optional, Callable
import requests


class SyftWidget:
    def __init__(
        self,
        server_url: str = "http://localhost:8000",
        check_interval: float = 1.0,
        endpoints: Optional[Dict[str, Callable[[], Any]]] = None
    ):
        self.server_url = server_url
        self.check_interval = check_interval
        self.endpoints = endpoints or {}
        self.snapshot_cache = {}
        self.is_server_available = False
        self.checking = True
        self.widget = None
    
    def _create_snapshots(self):
        """Create snapshots by calling the endpoint functions and caching results"""
        for endpoint, func in self.endpoints.items():
            try:
                result = func()
                self.snapshot_cache[endpoint] = result
            except Exception as e:
                self.snapshot_cache[endpoint] = None
        
    def _get_data(self, endpoint: str) -> Any:
        if self.is_server_available:
            try:
                response = requests.get(f"{self.server_url}{endpoint}", timeout=2)
                if response.status_code == 200:
                    return response.json()
            except:
                pass
        
        # Fall back to cached snapshot
        return self.snapshot_cache.get(endpoint)
    
    def stop(self):
        """Stop the widget (for compatibility)"""
        self.checking = False


