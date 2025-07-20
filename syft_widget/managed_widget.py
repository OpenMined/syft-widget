import time
import threading
from typing import Optional, Dict, Callable, Any
import ipywidgets as widgets
import uuid
from .widget import SyftWidget
from .server import run_server_in_thread
from .syftbox_manager import SyftBoxManager


class ManagedWidget(SyftWidget):
    """
    A widget with three-stage server management:
    1. Checkpoint data (immediate)
    2. Python thread server (automatic)
    3. SyftBox app server (when available)
    """
    
    def __init__(
        self,
        app_name: str = "syft-widget",
        repo_url: str = "https://github.com/OpenMined/syft-widget",
        thread_server_port: int = 8001,
        endpoints: Optional[Dict[str, Callable[[], Any]]] = None,
        **kwargs
    ):
        # Initialize with thread server URL first
        super().__init__(
            server_url=f"http://localhost:{thread_server_port}",
            endpoints=endpoints,
            **kwargs
        )
        
        self.app_name = app_name
        self.repo_url = repo_url
        self.thread_server_port = thread_server_port
        self.thread_server = None
        self.syftbox_manager = None
        self.current_stage = "checkpoint"
        self.widget_id = f"syft-widget-{uuid.uuid4().hex[:8]}"
        self.iframe = widgets.HTML()
        
        # Create snapshots
        self._create_snapshots()
        
        # Start the thread server immediately
        self._start_thread_server()
        
        # Start monitoring for SyftBox
        self._start_syftbox_monitoring()
    
    def _start_thread_server(self):
        """Start the Python thread server"""
        print(f"Starting thread server on port {self.thread_server_port}...")
        self.thread_server = run_server_in_thread(port=self.thread_server_port)
        self.current_stage = "thread"
        print("Thread server started")
    
    def _start_syftbox_monitoring(self):
        """Start monitoring for SyftBox app"""
        self.syftbox_manager = SyftBoxManager(
            app_name=self.app_name,
            repo_url=self.repo_url
        )
        
        def on_syftbox_ready(syftbox_url: str):
            """Called when SyftBox app is ready"""
            print(f"SyftBox app ready at {syftbox_url}")
            self.server_url = syftbox_url
            self.current_stage = "syftbox"
            
            # Kill the thread server
            if self.thread_server:
                print("Stopping thread server...")
                # Thread is daemon, so it will stop when main program exits
                # But we can signal the frontend to switch servers
                self.thread_server = None
        
        self.syftbox_manager.start_monitoring(on_ready_callback=on_syftbox_ready)
    
    def _update_display(self):
        """Render the widget"""
        data = self.snapshot_cache.get("/time", {})
        self._render_iframe(data)
    
    def _render_iframe(self, initial_data):
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
                    margin-bottom: 10px;
                }}
                .stage {{
                    font-size: 12px;
                    color: #999;
                    margin-bottom: 5px;
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
                <div class="status" id="status">🔴 Checkpoint</div>
                <div class="stage" id="stage">Stage: Checkpoint data</div>
            </div>
            <script>
                let currentStage = 'checkpoint';
                let isLive = false;
                let threadServerUrl = '{self.server_url}';
                let syftboxServerUrl = null;
                const endpoint = '/time';
                const checkInterval = {int(self.check_interval * 1000)};
                const syftboxCheckInterval = 2000; // Check for SyftBox every 2 seconds
                
                // Stage management
                const stages = {{
                    'checkpoint': {{
                        name: 'Checkpoint data',
                        icon: '🔴',
                        url: null
                    }},
                    'thread': {{
                        name: 'Python thread server',
                        icon: '🟡',
                        url: threadServerUrl
                    }},
                    'syftbox': {{
                        name: 'SyftBox app server',
                        icon: '🟢',
                        url: null
                    }}
                }};
                
                async function checkServer(url) {{
                    try {{
                        const response = await fetch(url + '/health', {{
                            method: 'GET',
                            mode: 'cors',
                            cache: 'no-cache'
                        }});
                        return response.ok;
                    }} catch (e) {{
                        return false;
                    }}
                }}
                
                async function getData(url) {{
                    try {{
                        const response = await fetch(url + endpoint, {{
                            method: 'GET',
                            mode: 'cors',
                            cache: 'no-cache'
                        }});
                        if (response.ok) {{
                            return await response.json();
                        }}
                    }} catch (e) {{
                        // Server not available
                    }}
                    return null;
                }}
                
                async function checkSyftBoxDiscovery() {{
                    try {{
                        const response = await fetch('http://localhost:62050', {{
                            method: 'GET',
                            mode: 'cors',
                            cache: 'no-cache'
                        }});
                        if (response.ok) {{
                            const data = await response.json();
                            const port = data.main_server_port;
                            if (port) {{
                                return `http://localhost:${{port}}`;
                            }}
                        }}
                    }} catch (e) {{
                        // Discovery not available
                    }}
                    return null;
                }}
                
                async function updateDisplay() {{
                    let data = null;
                    let newStage = currentStage;
                    
                    // Check for SyftBox server
                    if (!syftboxServerUrl) {{
                        syftboxServerUrl = await checkSyftBoxDiscovery();
                    }}
                    
                    if (syftboxServerUrl && await checkServer(syftboxServerUrl)) {{
                        // SyftBox is available
                        data = await getData(syftboxServerUrl);
                        if (data) {{
                            newStage = 'syftbox';
                            stages.syftbox.url = syftboxServerUrl;
                        }}
                    }} else if (await checkServer(threadServerUrl)) {{
                        // Thread server is available
                        data = await getData(threadServerUrl);
                        if (data) {{
                            newStage = 'thread';
                        }}
                    }}
                    
                    // Update stage if changed
                    if (newStage !== currentStage) {{
                        currentStage = newStage;
                        const container = document.getElementById('container');
                        container.classList.add('pulse');
                        setTimeout(() => container.classList.remove('pulse'), 500);
                    }}
                    
                    // Update display
                    if (data) {{
                        document.getElementById('timestamp').textContent = data.timestamp || 'N/A';
                        document.getElementById('formatted').textContent = data.formatted || 'N/A';
                    }} else {{
                        // Use initial checkpoint data
                        document.getElementById('timestamp').textContent = '{initial_data.get('timestamp', 'N/A')}';
                        document.getElementById('formatted').textContent = '{initial_data.get('formatted', 'N/A')}';
                    }}
                    
                    // Update status
                    const stage = stages[currentStage];
                    document.getElementById('status').innerHTML = `${{stage.icon}} ${{stage.name}}`;
                    document.getElementById('stage').textContent = `Stage: ${{currentStage}} - ${{stage.url || 'Local data'}}`;
                }}
                
                // Start polling
                setInterval(updateDisplay, checkInterval);
                
                // Initial update
                updateDisplay();
            </script>
        </body>
        </html>
        """
        
        iframe_html = f"""
        <iframe 
            id="{self.widget_id}" 
            srcdoc="{html_content.replace('"', '&quot;')}"
            style="width: 100%; height: 250px; border: none;"
            sandbox="allow-scripts">
        </iframe>
        """
        
        self.iframe.value = iframe_html
    
    def display(self):
        self._update_display()
        return self.iframe
    
    def stop(self):
        """Stop all monitoring and servers"""
        if self.syftbox_manager:
            self.syftbox_manager.stop_monitoring()
        super().stop()


class ManagedTimeWidget(ManagedWidget):
    """Time widget with managed server transitions"""
    
    def __init__(self, **kwargs):
        def get_time_snapshot():
            timestamp = int(time.time())
            formatted = time.strftime("%Y-%m-%d %H:%M:%S")
            return {"timestamp": timestamp, "formatted": formatted}
        
        endpoints = {
            "/time": get_time_snapshot
        }
        
        super().__init__(endpoints=endpoints, **kwargs)