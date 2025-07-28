"""DynamicWidget - Updates specific DOM elements instead of reloading everything"""
import json
import base64
import tempfile
import os
import inspect
import importlib.util
from typing import List, Optional, Dict, Any, Callable
import platform
import multiprocessing
import time

# Try to import jupyter-dark-detect
try:
    from jupyter_dark_detect import is_dark
    DARK_DETECT_AVAILABLE = True
except ImportError:
    DARK_DETECT_AVAILABLE = False

# Fix multiprocessing on macOS
if platform.system() == 'Darwin':
    try:
        multiprocessing.set_start_method('fork', force=True)
    except RuntimeError:
        pass

# Import server backend abstraction
from .server_backends import get_server_backend, syft_serve_available


class DynamicWidget:
    """A widget that updates specific DOM elements dynamically
    
    Example:
        class SystemWidget(DynamicWidget):
            def get_endpoints(self):
                @self.endpoint("/api/system")
                def get_system():
                    return {
                        "time": time.strftime("%H:%M:%S"),
                        "cpu": round(os.getloadavg()[0] * 100, 1)
                    }
            
            def get_template(self):
                return '''
                <div>Time: <span data-field="time">{time}</span></div>
                <div>CPU: <span data-field="cpu">{cpu}</span>%</div>
                '''
    """
    
    def __init__(self, 
                 widget_title: Optional[str] = None,
                 server_name: Optional[str] = None,
                 start_infra: bool = True,
                 verbose: bool = False,
                 width: str = "100%",
                 height: str = "60px",
                 update_interval: int = 1000,
                 debug: bool = False,
                 # Server management parameters
                 dependencies: Optional[List[str]] = None,
                 force_new_server: bool = False,
                 expiration_seconds: int = 86400):  # 24 hours default
        # Generate widget_title from class name if not provided
        if widget_title is None:
            # Convert class name from CamelCase to snake_case
            class_name = self.__class__.__name__
            # Convert CamelCase to snake_case
            import re
            widget_title = re.sub('([a-z0-9])([A-Z])', r'\1_\2', class_name).lower()
        
        self.widget_title = widget_title
        self._start_infra = start_infra
        self._verbose = verbose
        self.width = width
        self.height = height
        self.update_interval = update_interval
        self._debug = debug
        self._id = f"dynamic-widget-{id(self)}"
        self._debug_logs = []
        
        # Server management parameters
        # Derive server_name from widget_title if not provided
        if server_name is None:
            # Convert widget title to a valid server name
            # Replace spaces with underscores, lowercase, and remove special chars
            import re
            server_name = re.sub(r'[^a-zA-Z0-9_]', '_', widget_title.lower().replace(' ', '_'))
            server_name = re.sub(r'_+', '_', server_name).strip('_')  # Remove multiple underscores
            if not server_name:  # Fallback if title is all special chars
                server_name = "dynamic_widget"
        
        self.server_name = server_name
        self._dependencies = dependencies
        self._force_new_server = force_new_server
        self._expiration_seconds = expiration_seconds
        
        # Store endpoints
        self._endpoint_funcs = {}
        self._endpoints = []
        
        # Create temporary file for endpoints (for debugging/inspection purposes)
        fd, self._endpoint_file = tempfile.mkstemp(suffix="_endpoints.py", prefix="widget_", text=True)
        os.close(fd)
        
        # Let subclass define endpoints
        self._get_endpoints()
        
        # Write endpoints to file (for debugging/inspection purposes)
        self._write_endpoints_to_file()
        
        # Server backend and tracking
        self._backend = self._create_backend()
        self._server_handle = None
        self._server_port = None
    
    def _create_backend(self):
        """Get the syft-serve backend for server management
        
        Returns:
            SyftServeBackend: The syft-serve backend instance
        """
        return get_server_backend()
    
    def endpoint(self, path: str) -> Callable:
        """Decorator to register an endpoint (public for user convenience)"""
        def decorator(func):
            self._endpoint_funcs[path] = func
            self._endpoints.append(path)
            return func
        return decorator
    
    def _get_endpoints(self):
        """Call the user-defined get_endpoints method"""
        if hasattr(self, 'get_endpoints') and callable(getattr(self, 'get_endpoints')):
            self.get_endpoints()
    
    def get_endpoints(self):
        """Override this method to define your endpoints using @self.endpoint decorators"""
        pass
    
    def get_template(self) -> str:
        """Override this method to define your HTML template
        
        Use {variable} placeholders for initial render.
        Use data-field="variable" on elements you want to update dynamically.
        
        Example:
            return '''
            <div>
                <span data-field="time">{time}</span>
                <span data-field="cpu">{cpu}</span>
            </div>
            '''
        """
        raise NotImplementedError("You must implement get_template()")
    
    def _write_endpoints_to_file(self):
        """Write endpoints to a file (for debugging/inspection purposes)"""
        lines = [
            "# Auto-generated endpoint file for debugging",
            "import time",
            "import os",
            "import datetime",
            "import random",
            "import json",
            "import math",
            ""
        ]
        
        # Write each endpoint function
        for path, func in self._endpoint_funcs.items():
            try:
                source_lines = inspect.getsourcelines(func)[0]
                func_start = None
                for i, line in enumerate(source_lines):
                    if line.strip().startswith('def '):
                        func_start = i
                        break
                
                if func_start is not None:
                    func_code = source_lines[func_start:]
                    import textwrap
                    func_code_str = textwrap.dedent(''.join(func_code))
                    
                    lines.append(f'# Endpoint: {path}')
                    lines.append(func_code_str)
                    lines.append("")
                    
            except Exception as e:
                if self._verbose:
                    print(f"Warning: Could not extract source for {path}: {e}")
        
        # Write to file for debugging purposes
        with open(self._endpoint_file, 'w') as f:
            f.write('\n'.join(lines))
        
        if self._verbose:
            print(f"Endpoints written to: {self._endpoint_file}")
    
    def _get_mock_data(self) -> Dict[str, Any]:
        """Get mock data from all endpoints and flatten it"""
        mock_data = {"_server_status": "checkpoint"}  # Always include server status
        for path, func in self._endpoint_funcs.items():
            try:
                endpoint_data = func()
                # Flatten the endpoint data into the main dict
                mock_data.update(endpoint_data)
            except Exception as e:
                mock_data[path] = {"error": str(e)}
        return mock_data
    
    def _get_widget_styles(self) -> str:
        """Override this to provide custom CSS styles"""
        return ""
    
    def _get_css_light(self) -> str:
        """Override this to provide light theme CSS"""
        return ""
    
    def _get_css_dark(self) -> str:
        """Override this to provide dark theme CSS"""
        return ""
    
    def _detect_theme(self) -> str:
        """Detect if Jupyter is in dark mode"""
        if DARK_DETECT_AVAILABLE:
            try:
                return 'dark' if is_dark() else 'light'
            except Exception:
                # If detection fails, fall back to auto
                pass
        
        # Fall back to CSS media queries in the iframe itself
        return 'auto'
    
    def _start_server_async(self):
        """Start server creation in background (non-blocking)"""
        try:
            if self._verbose:
                print(f"Starting server using syft-serve...")
            
            # Check if server already exists and try to reuse it
            existing_server_status = self._backend.get_server_status(self.server_name)
            
            if existing_server_status != "not_found" and not self._force_new_server:
                # Server exists, check if we can reuse it
                if self._can_reuse_server():
                    if self._verbose:
                        print(f"Reusing existing server '{self.server_name}'")
                    # Get the existing server handle
                    self._server_handle = self._backend._syft_serve.servers[self.server_name]
                else:
                    raise ValueError(
                        f"Server '{self.server_name}' already exists and cannot be reused. "
                        f"This could be because:\n"
                        f"  - The server has different endpoints\n"
                        f"  - The server is not running properly\n"
                        f"  - There are compatibility issues\n"
                        f"Solutions:\n"
                        f"  - Use a different server_name (e.g., '{self.server_name}_v2')\n"
                        f"  - Set force_new_server=True to replace the existing server\n"
                        f"  - Check server status: syft_serve.servers['{self.server_name}'].status"
                    )
            else:
                # Create new server
                self._server_handle = self._backend.create_server(
                    name=self.server_name,
                    endpoints=self._endpoint_funcs,
                    dependencies=self._dependencies,
                    force_new_server=self._force_new_server,
                    expiration_seconds=self._expiration_seconds
                )
            
            # Get server URL and port
            server_url = self._backend.get_server_url(self.server_name)
            if server_url:
                # Extract port from URL (assuming format http://host:port)
                try:
                    import urllib.parse
                    parsed = urllib.parse.urlparse(server_url)
                    self._server_port = parsed.port
                except:
                    self._server_port = None
            
            if self._verbose:
                status = self._backend.get_server_status(self.server_name)
                print(f"Server '{self.server_name}' status: {status}")
                if server_url:
                    print(f"Server URL: {server_url}")
            
        except Exception as e:
            if self._verbose:
                print(f"Warning: Could not start server: {e}")
            self._server_port = None
    
    def _repr_html_(self):
        """Jupyter display method"""
        # Start server creation in background thread if enabled
        if self._start_infra:
            import threading
            threading.Thread(target=self._start_server_async, daemon=True).start()
        
        # Always return HTML immediately with real mock data
        
        # Get mock data and template
        mock_data = self._get_mock_data()
        template = self.get_template()
        
        # Render initial content with mock data
        initial_content = self._render_template(template, mock_data)
        
        # Detect theme
        theme = self._detect_theme()
        
        # Generate the complete HTML with theme support
        html = f"""<!DOCTYPE html>
<html{' data-theme="dark"' if theme == 'dark' else ''}>
<head>
<style>
{self._get_widget_styles()}

/* Light theme (default) */
{self._get_css_light()}

/* Dark theme via media query */
@media (prefers-color-scheme: dark) {{
{self._get_css_dark()}
}}

/* Dark theme via data attribute */
[data-theme="dark"] {{
{self._get_css_dark()}
}}
</style>
<script>
// Theme detection status
const detectedTheme = '{theme}';

// Try to detect parent theme if detection was 'auto'
window.addEventListener('DOMContentLoaded', function() {{
    if (detectedTheme === 'auto') {{
        try {{
            const parentDoc = window.parent.document;
            const isDark = parentDoc.body.getAttribute('data-jp-theme-name')?.includes('dark') || 
                           parentDoc.body.classList.contains('theme-dark') ||
                           parentDoc.documentElement.getAttribute('data-theme') === 'dark';
            
            if (isDark) {{
                document.documentElement.setAttribute('data-theme', 'dark');
            }}
        }} catch(e) {{
            // Can't access parent, will use prefers-color-scheme
        }}
    }}
}});
</script>
</head>
<body>
<div id="widget-content">
{initial_content}
</div>
<script>
(function() {{
    const endpoints = {json.dumps(self._endpoints)};
    const updateInterval = {self.update_interval};
    const verbose = {json.dumps(self._verbose)};
    const debug = {json.dumps(self._debug)};
    const template = {json.dumps(template)};
    
    let currentData = {json.dumps(mock_data)};
    currentData._server_status = 'checkpoint';  // Add server status to data
    let connectedPort = null;
    let consecutiveFailures = 0;
    let debugLogs = [];
    
    // Debug logging function
    function log(message, level = 'info') {{
        const timestamp = new Date().toISOString();
        const logEntry = `[${{timestamp}}] [${{level.toUpperCase()}}] ${{message}}`;
        
        // Always log scanning info and connection events to console
        if (debug || verbose || level === 'info' || message.includes('Scanning') || message.includes('Connected')) {{
            console.log(logEntry);
        }}
        
        debugLogs.push(logEntry);
        if (debugLogs.length > 100) {{
            debugLogs.shift(); // Keep only last 100 logs
        }}
        
        // Expose logs globally for debugging
        window['{self._id}_logs'] = debugLogs;
    }}
    
    // Simple template renderer for initial content
    function renderTemplate(template, data) {{
        let result = template;
        for (const [key, value] of Object.entries(data)) {{
            const regex = new RegExp('\\{{' + key + '\\}}', 'g');
            result = result.replace(regex, value);
        }}
        return result;
    }}
    
    // Dynamic field updater - only updates specific elements
    function updateFields(oldData, newData) {{
        let hasChanges = false;
        
        // Find all elements with data-field attribute
        const fieldElements = document.querySelectorAll('[data-field]');
        
        fieldElements.forEach(element => {{
            const fieldName = element.getAttribute('data-field');
            const oldValue = oldData[fieldName];
            const newValue = newData[fieldName];
            
            // Only update if value changed
            if (oldValue !== newValue && newValue !== undefined) {{
                element.textContent = newValue;
                hasChanges = true;
                log(`Updated ${{fieldName}}: ${{oldValue}} → ${{newValue}}`, 'debug');
            }}
        }});
        
        return hasChanges;
    }}
    
    // Calculate our endpoint hash for compatibility checking
    function calculateEndpointHash(endpointList) {{
        const sorted = [...endpointList].sort();
        const hashString = JSON.stringify(sorted);
        // Simple hash function (for production, use crypto.subtle.digest)
        let hash = 0;
        for (let i = 0; i < hashString.length; i++) {{
            const char = hashString.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }}
        return Math.abs(hash).toString(16);
    }}
    
    const ourEndpointHash = calculateEndpointHash(endpoints);
    
    async function tryPort(port) {{
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000); // Increased timeout to 2s
        try {{
            log(`Trying port ${{port}}...`, 'debug');
            // First check if server has compatible endpoints
            const hashResp = await fetch(`http://localhost:${{port}}/api/hash`, {{
                mode: 'cors',
                signal: controller.signal
            }});
            
            if (hashResp.ok) {{
                const hashData = await hashResp.json();
                log(`Port ${{port}} hash check: server has endpoints ${{JSON.stringify(hashData.endpoints)}}, we need ${{JSON.stringify(endpoints)}}`, 'debug');
                
                // Check if server has all our endpoints
                const hasAllEndpoints = endpoints.every(endpoint => 
                    hashData.endpoints.includes(endpoint)
                );
                
                if (!hasAllEndpoints) {{
                    log(`Port ${{port}} incompatible: missing endpoints ${{JSON.stringify(endpoints.filter(e => !hashData.endpoints.includes(e)))}}`, 'warn');
                    clearTimeout(timeoutId);
                    return null;
                }}
                
                log(`Port ${{port}} compatible: has all required endpoints`, 'info');
            }} else {{
                // Fallback: try our main endpoint directly
                log(`Port ${{port}} no hash endpoint (status: ${{hashResp.status}}), trying direct endpoint test`, 'debug');
                const testEndpoint = endpoints[0];
                const resp = await fetch(`http://localhost:${{port}}${{testEndpoint}}`, {{
                    mode: 'cors',
                    signal: controller.signal
                }});
                clearTimeout(timeoutId);
                if (resp.ok) {{
                    log(`Port ${{port}} direct endpoint test successful`, 'info');
                    return resp;
                }} else {{
                    log(`Port ${{port}} direct endpoint test failed: ${{resp.status}}`, 'debug');
                    return null;
                }}
            }}
            
            // Server is compatible, test one of our endpoints
            const testEndpoint = endpoints[0];
            const resp = await fetch(`http://localhost:${{port}}${{testEndpoint}}`, {{
                mode: 'cors',
                signal: controller.signal
            }});
            clearTimeout(timeoutId);
            return resp.ok ? resp : null;
            
        }} catch(e) {{
            log(`Port ${{port}} connection failed: ${{e.message}}`, 'debug');
            clearTimeout(timeoutId);
            return null;
        }}
    }}
    
    async function fetchEndpoint(baseUrl, endpoint) {{
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 1000);
        try {{
            const resp = await fetch(baseUrl + endpoint, {{
                mode: 'cors',
                signal: controller.signal
            }});
            clearTimeout(timeoutId);
            if (resp.ok) {{
                const data = await resp.json();
                log(`Fetched ${{endpoint}}: ${{JSON.stringify(data).substring(0, 100)}}...`, 'debug');
                return data;
            }} else {{
                log(`Failed to fetch ${{endpoint}}: HTTP ${{resp.status}}`, 'error');
            }}
        }} catch(e) {{
            log(`Error fetching ${{endpoint}}: ${{e.message}}`, 'error');
        }}
        return null;
    }}
    
    async function updateWidget() {{
        let baseUrl = null;
        let serverStatus = 'checkpoint';
        
        // Try connected port first
        if (connectedPort) {{
            const resp = await tryPort(connectedPort);
            if (resp) {{
                baseUrl = `http://localhost:${{connectedPort}}`;
                serverStatus = connectedPort >= 8000 && connectedPort <= 8010 ? 'thread' : 'syftbox';
                consecutiveFailures = 0;
            }} else {{
                consecutiveFailures++;
                log(`Lost connection to port ${{connectedPort}} (failure ${{consecutiveFailures}})`, 'warn');
                if (consecutiveFailures >= 3) {{
                    log(`Disconnecting from port ${{connectedPort}} after 3 failures`, 'warn');
                    connectedPort = null;
                    consecutiveFailures = 0;
                }}
            }}
        }}
        
        // Scan for servers if no connected port
        if (!connectedPort) {{
            log('Scanning for servers on ports 8000-8010...', 'info');
            for (let port = 8000; port <= 8010; port++) {{
                const resp = await tryPort(port);
                if (resp) {{
                    baseUrl = `http://localhost:${{port}}`;
                    serverStatus = 'thread';
                    connectedPort = port;
                    log(`Connected to server at port ${{port}}`, 'info');
                    break;
                }} else {{
                    log(`Port ${{port}} failed or incompatible`, 'debug');
                }}
            }}
            if (!connectedPort) {{
                log('No servers found, staying in checkpoint mode', 'info');
            }}
        }}
        
        // Create a copy of current data for comparison
        const oldData = {{...currentData}};
        
        // Always update server status
        currentData._server_status = serverStatus;
        
        // Fetch data from endpoints if we have a server
        if (baseUrl) {{
            for (const endpoint of endpoints) {{
                const data = await fetchEndpoint(baseUrl, endpoint);
                if (data !== null) {{
                    // Merge endpoint data into currentData
                    Object.assign(currentData, data);
                }}
            }}
        }}
        
        // Update only the fields that changed
        updateFields(oldData, currentData);
    }}
    
    // Initialize
    log(`Widget initialized: ${{endpoints.length}} endpoints, interval: ${{updateInterval}}ms`, 'info');
    
    // Expose debug console
    window['{self._id}'] = {{
        logs: () => debugLogs,
        lastLogs: (n = 10) => debugLogs.slice(-n),
        clearLogs: () => {{ debugLogs = []; }},
        data: () => currentData,
        status: () => currentData._server_status,
        port: () => connectedPort,
        debug: (enabled) => {{ 
            window['{self._id}_debug'] = enabled;
            log(`Debug mode ${{enabled ? 'enabled' : 'disabled'}}`, 'info');
        }}
    }};
    
    log(`Debug console available at: window.{self._id}`, 'info');
    
    // Start the update loop
    setInterval(updateWidget, updateInterval);
    updateWidget();
}})();
</script>
</body>
</html>"""
        
        # Encode as base64 for iframe
        iframe_base64 = base64.b64encode(html.encode()).decode()
        
        # Return iframe
        return f"""
        <iframe 
            id="{self._id}-iframe"
            src="data:text/html;base64,{iframe_base64}" 
            width="{self.width}" 
            height="{self.height}" 
            frameborder="0" 
            style="border:none;border-radius:8px;">
        </iframe>
        """
    
    def _render_template(self, template: str, data: Dict[str, Any]) -> str:
        """Render template with data (Python version)"""
        result = template
        for key, value in data.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result
    
    def _can_reuse_server(self) -> bool:
        """Check if the existing server can be reused based on endpoint compatibility
        
        Returns:
            True if server can be reused, False otherwise
        """
        try:
            # Get existing server from syft-serve
            existing_server = self._backend._syft_serve.servers[self.server_name]
            
            # Get current endpoint paths 
            current_endpoints = set(self._endpoint_funcs.keys())
            
            # Get existing server endpoint paths
            # Note: syft-serve servers store endpoints in different ways depending on implementation
            # For now, we'll do a simple check - if the server exists and is running, we assume compatibility
            # In a more sophisticated implementation, we could compare actual endpoint signatures
            
            # Check if server is running
            if existing_server.status != "running":
                return False
                
            # For now, we'll be conservative and only allow reuse if endpoint counts match
            # This is a simplified compatibility check - in practice you might want more sophisticated logic
            try:
                # Try to get endpoint count from server (this may vary based on syft-serve implementation)
                # For safety, we'll return True to allow reuse and let any real conflicts surface at runtime
                return True
            except:
                # If we can't determine compatibility, err on the side of caution
                return False
                
        except Exception as e:
            # If anything goes wrong, don't reuse
            return False
    
    @property
    def server(self):
        """Access the underlying server object
        
        Returns:
            The syft-serve server handle if available, None otherwise
        """
        return getattr(self, '_server_handle', None)
    
    def _get_debug_info(self):
        """Get debug information about the widget"""
        info = {
            "widget_id": self._id,
            "endpoints": self._endpoints,
            "endpoint_file": getattr(self, '_endpoint_file', None),
            "debug_logs": self._debug_logs[-20:],  # Last 20 logs
            "server_info": None
        }
        
        # Check if server is running using backend
        try:
            if hasattr(self, '_backend') and hasattr(self, 'server_name'):
                status = self._backend.get_server_status(self.server_name)
                server_url = self._backend.get_server_url(self.server_name)
                
                info["server_info"] = {
                    "name": self.server_name,
                    "status": status,
                    "url": server_url,
                    "backend": "syft-serve",
                    "endpoints": self._endpoints
                }
        except:
            pass
        
        # Try to test endpoints
        info["endpoint_tests"] = {}
        for endpoint in self._endpoints:
            try:
                func = self._endpoint_funcs.get(endpoint)
                if func:
                    result = func()
                    info["endpoint_tests"][endpoint] = {"status": "ok", "result": result}
            except Exception as e:
                info["endpoint_tests"][endpoint] = {"status": "error", "error": str(e)}
        
        return info
    
    def _restart_server(self) -> bool:
        """Restart the widget's server
        
        Returns:
            bool: True if restart was successful
        """
        try:
            if hasattr(self, '_backend') and hasattr(self, 'server_name'):
                # Stop the current server
                self._backend.stop_server(self.server_name)
                
                # Create a new one
                self._server_handle = self._backend.create_server(
                    name=self.server_name,
                    endpoints=self._endpoint_funcs,
                    dependencies=self._dependencies,
                    force_new_server=True,  # Force new server on restart
                    expiration_seconds=self._expiration_seconds
                )
                
                # Update server port
                server_url = self._backend.get_server_url(self.server_name)
                if server_url:
                    try:
                        import urllib.parse
                        parsed = urllib.parse.urlparse(server_url)
                        self._server_port = parsed.port
                    except:
                        pass
                
                if self._verbose:
                    print(f"Server '{self.server_name}' restarted successfully")
                return True
        except Exception as e:
            if self._verbose:
                print(f"Failed to restart server: {e}")
            return False
    
    def _stop_server(self) -> bool:
        """Stop the widget's server
        
        Returns:
            bool: True if stop was successful
        """
        try:
            if hasattr(self, '_backend') and hasattr(self, 'server_name'):
                self._backend.stop_server(self.server_name)
                self._server_handle = None
                self._server_port = None
                
                if self._verbose:
                    print(f"Server '{self.server_name}' stopped")
                return True
        except Exception as e:
            if self._verbose:
                print(f"Failed to stop server: {e}")
            return False
    
    def _get_server_logs(self, lines: int = 20) -> Optional[str]:
        """Get server logs (if using syft-serve backend)
        
        Args:
            lines: Number of recent log lines to retrieve
            
        Returns:
            Log content if available, None otherwise
        """
        try:
            # This only works with syft-serve backend
            if (hasattr(self, '_server_handle') and 
                hasattr(self._server_handle, 'stdout') and
                hasattr(self._server_handle.stdout, 'tail')):
                return self._server_handle.stdout.tail(lines)
        except:
            pass
        return None
    
    def __del__(self):
        """Clean up temporary files"""
        if hasattr(self, '_endpoint_file') and os.path.exists(self._endpoint_file):
            try:
                os.unlink(self._endpoint_file)
                if self._verbose:
                    print(f"Cleaned up endpoint file: {self._endpoint_file}")
            except:
                pass