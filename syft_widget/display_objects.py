"""Base display object for creating widgets that use API endpoints"""
import json
from typing import List, Optional


class APIDisplay:
    """Base class for display objects that use API endpoints"""
    
    def __init__(self, endpoints: List[str]):
        """
        Args:
            endpoints: List of endpoint paths this display uses (e.g., ["/time/current"])
        """
        self.endpoints = endpoints
        self.id = f"api-display-{id(self)}"
        
        # Import here to avoid circular imports
        from .widget_registry import get_current_registry
        self.registry = get_current_registry()
    
    def get_mock_data(self):
        """Get mock data from endpoints"""
        from .endpoints import ENDPOINT_REGISTRY
        
        mock_data = {}
        for endpoint in self.endpoints:
            if endpoint in ENDPOINT_REGISTRY:
                try:
                    mock_data[endpoint] = ENDPOINT_REGISTRY[endpoint]()
                except Exception as e:
                    mock_data[endpoint] = {"error": str(e)}
            else:
                mock_data[endpoint] = {"error": "Endpoint not found"}
        
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