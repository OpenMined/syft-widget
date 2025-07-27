"""Base display object for creating widgets that use API endpoints"""
import json
from typing import List, Optional, Dict, Any

# Import server backend abstraction
from .server_backends import get_server_backend, syft_serve_available


class APIDisplay:
    """Base class for display objects that use API endpoints
    
    Updated to use the new server backend abstraction layer for better
    server management and syft-serve integration.
    """
    
    def __init__(self, endpoints: List[str], start_infra: bool = True,
                 # Server management parameters
                 server_name: Optional[str] = None,
                 dependencies: Optional[List[str]] = None,
                 force_new_server: bool = False,
                 verbose: bool = False):
        """
        Args:
            endpoints: List of endpoint paths this display uses (e.g., ["/time/current"])
            start_infra: Whether to automatically start infrastructure when displayed (default: True)
            server_name: Optional name for the server
            dependencies: Optional list of Python packages for the server
            force_new_server: Whether to force creation of a new server
            verbose: Whether to show server status messages
        """
        self.endpoints = endpoints
        self.start_infra = start_infra
        self.id = f"api-display-{id(self)}"
        
        # Server management parameters
        self.server_name = server_name or f"api_display_{self.id}"
        self.dependencies = dependencies
        self.force_new_server = force_new_server
        self.verbose = verbose
        
        # Server backend and tracking
        self._backend = self._create_backend()
        self._server_handle = None
        
        # Keep registry for backward compatibility
        from .widget_registry import get_current_registry
        self.registry = get_current_registry()
    
    def _create_backend(self):
        """Get the syft-serve backend for server management"""
        return get_server_backend()
    
    def get_mock_data(self):
        """Get mock data from endpoints for initial display
        
        Returns placeholder data for initial rendering before server starts.
        """
        mock_data = {"_server_status": "initializing"}  # Server is starting
        
        # Generate placeholder data for each endpoint
        for endpoint in self.endpoints:
            mock_data[endpoint] = {
                "message": "Loading...", 
                "endpoint": endpoint,
                "timestamp": "initializing"
            }
        
        return mock_data
    
    def render_content(self, data: dict, server_type: str = "checkpoint") -> str:
        """Override this to render your content"""
        return f"<pre>{json.dumps(data, indent=2)}</pre>"
    
    def get_update_script(self) -> str:
        """Override this to provide custom update logic"""
        return """
        element.innerHTML = `<pre>${JSON.stringify(currentData, null, 2)}</pre>`;
        """
    
    def _repr_html_(self):
        """Jupyter display method"""
        # Auto-start infrastructure if enabled
        if self.start_infra:
            try:
                if self.verbose:
                    print(f"Starting infrastructure using syft-serve...")
                
                # Use registry to start infrastructure (for backward compatibility)
                from .widget_registry import start_infrastructure
                start_infrastructure(verbose=self.verbose, dependencies=self.dependencies)
                
                if self.verbose:
                    print(f"Infrastructure started successfully")
                    
            except Exception as e:
                if self.verbose:
                    print(f"Warning: Could not start infrastructure: {e}")
        
        mock_data = self.get_mock_data()
        initial_content = self.render_content(mock_data, "checkpoint")
        
        # Get current server URL if available
        base_url = self.registry.get_base_url() if self.registry else None
        
        return f"""
        <div id="{self.id}">
            {initial_content}
        </div>
        <script>
        (function() {{
            const displayId = "{self.id}";
            const endpoints = {json.dumps(self.endpoints)};
            const mockData = {json.dumps(mock_data)};
            let currentData = JSON.parse(JSON.stringify(mockData));
            let currentServerType = "checkpoint";
            let currentPort = null;
            
            console.log(`[APIDisplay ${{displayId}}] Initialized with endpoints:`, endpoints);
            
            async function checkServer(url) {{
                try {{
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 500);
                    
                    const resp = await fetch(url + '/health', {{
                        signal: controller.signal,
                        mode: 'cors'
                    }});
                    
                    clearTimeout(timeoutId);
                    return resp.ok;
                }} catch(e) {{
                    return false;
                }}
            }}
            
            async function checkSyftBoxDiscovery() {{
                try {{
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 500);
                    
                    const resp = await fetch('http://localhost:62050', {{
                        signal: controller.signal,
                        mode: 'cors'
                    }});
                    
                    clearTimeout(timeoutId);
                    
                    if (resp.ok) {{
                        const data = await resp.json();
                        const port = data.main_server_port;
                        if (port) {{
                            return `http://localhost:${{port}}`;
                        }}
                    }}
                }} catch(e) {{
                    // Discovery not available
                }}
                return null;
            }}
            
            async function updateDisplay() {{
                // Try different server ports
                let baseUrl = null;
                let serverType = "checkpoint";
                
                // First check for SyftBox via discovery
                const syftboxUrl = await checkSyftBoxDiscovery();
                if (syftboxUrl && await checkServer(syftboxUrl)) {{
                    baseUrl = syftboxUrl;
                    serverType = "syftbox";
                    currentPort = parseInt(syftboxUrl.split(':').pop());
                    console.log(`[APIDisplay ${{displayId}}] Found SyftBox server at ${{syftboxUrl}}`);
                }} else {{
                    // Try thread server ports - check a range in case ports are in use
                    const threadPorts = [];
                    for (let p = 8000; p <= 8010; p++) {{
                        threadPorts.push(p);
                    }}
                    for (const port of threadPorts) {{
                        if (await checkServer(`http://localhost:${{port}}`)) {{
                            baseUrl = `http://localhost:${{port}}`;
                            serverType = "thread";
                            currentPort = port;
                            console.log(`[APIDisplay ${{displayId}}] Found thread server at port ${{port}}`);
                            break;
                        }}
                    }}
                }}
                
                if (!baseUrl) {{
                    console.log(`[APIDisplay ${{displayId}}] No servers available, using checkpoint data`);
                    serverType = "checkpoint";
                    currentPort = null;
                }}
                
                // Update server type if changed
                if (serverType !== currentServerType) {{
                    currentServerType = serverType;
                    console.log(`[APIDisplay ${{displayId}}] Server type changed to: ${{serverType}}`);
                }}
                
                // Fetch data from endpoints if we have a server
                let dataChanged = false;
                if (baseUrl) {{
                    for (const endpoint of endpoints) {{
                        try {{
                            const controller = new AbortController();
                            const timeoutId = setTimeout(() => controller.abort(), 1000);
                            
                            const resp = await fetch(baseUrl + endpoint, {{ 
                                mode: 'cors',
                                signal: controller.signal
                            }});
                            
                            clearTimeout(timeoutId);
                            
                            if (resp.ok) {{
                                const data = await resp.json();
                                if (JSON.stringify(data) !== JSON.stringify(currentData[endpoint])) {{
                                    currentData[endpoint] = data;
                                    dataChanged = true;
                                    console.log(`[APIDisplay ${{displayId}}] Updated ${{endpoint}}:`, data);
                                }}
                            }}
                        }} catch(e) {{
                            // On error, keep using last known data
                            console.debug(`[APIDisplay ${{displayId}}] Error fetching ${{endpoint}} (will retry):`, e.message);
                        }}
                    }}
                }}
                
                // Always update display if server type changed
                const serverTypeChanged = serverType !== currentServerType;
                
                // Update display if data changed or server type changed or we're in checkpoint mode
                if (dataChanged || serverTypeChanged || serverType === 'checkpoint') {{
                    const element = document.getElementById(displayId);
                    if (element) {{
                        {self.get_update_script()}
                    }}
                }}
            }}
            
            // Start polling
            setInterval(updateDisplay, 1000);
            updateDisplay();
        }})();
        </script>
        """
    
    def restart_server(self) -> bool:
        """Restart the infrastructure server
        
        Returns:
            bool: True if restart was successful
        """
        try:
            # Use registry to restart infrastructure
            from .widget_registry import stop_infrastructure, start_infrastructure
            
            if self.verbose:
                print(f"Restarting infrastructure...")
            
            stop_infrastructure()
            start_infrastructure(verbose=self.verbose, dependencies=self.dependencies)
            
            if self.verbose:
                print(f"Infrastructure restarted successfully")
            return True
        except Exception as e:
            if self.verbose:
                print(f"Failed to restart infrastructure: {e}")
            return False
    
    def stop_server(self) -> bool:
        """Stop the infrastructure server
        
        Returns:
            bool: True if stop was successful
        """
        try:
            from .widget_registry import stop_infrastructure
            
            if self.verbose:
                print(f"Stopping infrastructure...")
            
            stop_infrastructure()
            
            if self.verbose:
                print(f"Infrastructure stopped")
            return True
        except Exception as e:
            if self.verbose:
                print(f"Failed to stop infrastructure: {e}")
            return False
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get infrastructure status information
        
        Returns:
            dict: Status information including backend type and server details
        """
        try:
            from .widget_registry import get_infrastructure_status
            return get_infrastructure_status()
        except Exception as e:
            return {
                "error": str(e),
                "running": False,
                "backend": "unknown"
            }
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information about the APIDisplay
        
        Returns:
            dict: Debug information including endpoints and server status
        """
        info = {
            "display_id": self.id,
            "endpoints": self.endpoints,
            "server_name": self.server_name,
            "dependencies": self.dependencies,
            "backend": "syft-serve"
        }
        
        # Add server status
        try:
            info["server_status"] = self.get_server_status()
        except Exception as e:
            info["server_status"] = {"error": str(e)}
        
        # Add mock data test
        try:
            info["mock_data"] = self.get_mock_data()
        except Exception as e:
            info["mock_data"] = {"error": str(e)}
        
        return info