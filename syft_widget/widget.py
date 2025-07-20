import asyncio
import threading
import time
from typing import Dict, Any, Optional, Callable
import requests
import ipywidgets as widgets
from IPython.display import display, HTML
import json
import uuid


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
        self._check_thread = None
    
    def _create_snapshots(self):
        """Create snapshots by calling the endpoint functions and caching results"""
        for endpoint, func in self.endpoints.items():
            try:
                result = func()
                self.snapshot_cache[endpoint] = result
            except Exception as e:
                self.snapshot_cache[endpoint] = None
        
    def _check_server_availability(self):
        # No longer needed - JavaScript handles polling
        pass
    
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
    
    def start(self):
        self._check_thread = threading.Thread(target=self._check_server_availability, daemon=True)
        self._check_thread.start()
    
    def stop(self):
        self.checking = False
        if self._check_thread:
            self._check_thread.join()


class TimeWidget(SyftWidget):
    def __init__(self, server_instance=None, server_url="http://localhost:8000", **kwargs):
        # Always create a snapshot with current time
        # This represents what the server endpoint would return
        def get_time_snapshot():
            # Always create a valid timestamp snapshot
            timestamp = int(time.time())
            formatted = time.strftime("%Y-%m-%d %H:%M:%S")
            result = {"timestamp": timestamp, "formatted": formatted}
            return result
        
        endpoints = {
            "/time": get_time_snapshot
        }
        
        # Pass server_url to parent
        kwargs['server_url'] = server_url
        super().__init__(endpoints=endpoints, **kwargs)
        self.widget_id = f"syft-widget-{uuid.uuid4().hex[:8]}"
        self.iframe = widgets.HTML()
        # Create snapshots before first render
        self._create_snapshots()
        
    def _update_display(self):
        # Just render once with snapshot data
        data = self.snapshot_cache.get("/time", {})
        if data:
            self._render_iframe(data, "🔴 Snapshot")
        else:
            self._render_iframe({"timestamp": "N/A", "formatted": "No snapshot"}, "🔴 Snapshot")
    
    def _render_iframe(self, initial_data, status):
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    margin: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    transition: all 0.3s ease;
                }}
                .timestamp {{
                    font-size: 36px;
                    color: #333;
                    margin-bottom: 10px;
                    font-weight: bold;
                }}
                .formatted {{
                    font-size: 18px;
                    color: #666;
                    margin-bottom: 15px;
                }}
                .status {{
                    font-size: 14px;
                    color: #666;
                    padding-top: 10px;
                    border-top: 1px solid #eee;
                }}
                .pulse {{
                    animation: pulse 0.5s ease-in-out;
                }}
                @keyframes pulse {{
                    0% {{ opacity: 1; }}
                    50% {{ opacity: 0.7; }}
                    100% {{ opacity: 1; }}
                }}
            </style>
        </head>
        <body>
            <div class="container" id="container">
                <div class="timestamp" id="timestamp">{initial_data.get('timestamp', 'N/A')}</div>
                <div class="formatted" id="formatted">{initial_data.get('formatted', 'N/A')}</div>
                <div class="status" id="status">{status}</div>
            </div>
            <script>
                let isLive = false;
                const serverUrl = '{self.server_url}';
                const endpoint = '/time';
                const checkInterval = {int(self.check_interval * 1000)};
                
                async function checkAndUpdate() {{
                    try {{
                        // Check health first
                        const healthResponse = await fetch(serverUrl + '/health', {{
                            method: 'GET',
                            mode: 'cors',
                            cache: 'no-cache'
                        }});
                        
                        if (healthResponse.ok) {{
                            // Server is available, get data
                            const dataResponse = await fetch(serverUrl + endpoint, {{
                                method: 'GET',
                                mode: 'cors',
                                cache: 'no-cache'
                            }});
                            
                            if (dataResponse.ok) {{
                                const data = await dataResponse.json();
                                updateDisplay(data, true);
                                return;
                            }}
                        }}
                    }} catch (e) {{
                        // Server not available
                    }}
                    
                    // Keep showing snapshot
                    updateDisplay({initial_data}, false);
                }}
                
                function updateDisplay(data, serverAvailable) {{
                    const wasLive = isLive;
                    isLive = serverAvailable;
                    
                    // Update content
                    document.getElementById('timestamp').textContent = data.timestamp || 'N/A';
                    document.getElementById('formatted').textContent = data.formatted || 'N/A';
                    document.getElementById('status').innerHTML = serverAvailable ? '🟢 Live Server' : '🔴 Snapshot';
                    
                    // Add pulse animation when status changes
                    if (wasLive !== isLive) {{
                        const container = document.getElementById('container');
                        container.classList.add('pulse');
                        setTimeout(() => container.classList.remove('pulse'), 500);
                    }}
                }}
                
                // Start polling
                setInterval(checkAndUpdate, checkInterval);
                
                // Initial check
                checkAndUpdate();
            </script>
        </body>
        </html>
        """
        
        iframe_html = f"""
        <iframe 
            id="{self.widget_id}" 
            srcdoc="{html_content.replace('"', '&quot;')}"
            style="width: 100%; height: 200px; border: none;"
            sandbox="allow-scripts">
        </iframe>
        """
        
        self.iframe.value = iframe_html
    
    def display(self):
        self._update_display()
        return self.iframe


# Keep HelloWidget for backward compatibility
HelloWidget = TimeWidget