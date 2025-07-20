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
        discovery_port: int = 62050,
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
        self.discovery_port = discovery_port
        self.thread_server = None
        self.syftbox_manager = None
        self.current_stage = "checkpoint"
        self.widget_id = f"syft-widget-{uuid.uuid4().hex[:8]}"
        self.iframe = widgets.HTML()
        
        # Create snapshots
        self._create_snapshots()
        
        # Start monitoring for SyftBox
        self._start_syftbox_monitoring()
        
        # Only start thread server if SyftBox isn't already available
        self._check_and_start_thread_server()
    
    def _check_and_start_thread_server(self):
        """Check if we need to start the thread server"""
        # Quick check if SyftBox server is already available
        if self.syftbox_manager and self.syftbox_manager.check_syftbox_server():
            print("SyftBox server already available, skipping thread server")
            self.current_stage = "syftbox"
            self.server_url = self.syftbox_manager.get_syftbox_server_url()
        else:
            # No SyftBox server, start thread server
            self._start_thread_server()
    
    def _start_thread_server(self):
        """Start the Python thread server with a delay to simulate startup time"""
        if self.thread_server:
            print("Thread server already running")
            return
            
        def delayed_start():
            print(f"Thread server will start in 2 seconds on port {self.thread_server_port}...")
            time.sleep(2)
            self.thread_server = run_server_in_thread(port=self.thread_server_port, delay=0)
            self.current_stage = "thread"
            print(f"Thread server started on port {self.thread_server_port}")
        
        # Start in a separate thread so it doesn't block
        start_thread = threading.Thread(target=delayed_start, daemon=True)
        start_thread.start()
    
    def _stop_thread_server(self):
        """Stop the thread server"""
        if self.thread_server:
            print("Stopping thread server...")
            # Thread is daemon, so it will stop when main program exits
            # But we can signal that it's no longer needed
            self.thread_server = None
    
    def _start_syftbox_monitoring(self):
        """Start monitoring for SyftBox app"""
        self.syftbox_manager = SyftBoxManager(
            app_name=self.app_name,
            repo_url=self.repo_url,
            discovery_port=self.discovery_port
        )
        
        def on_syftbox_ready(syftbox_url: str):
            """Called when SyftBox app is ready"""
            print(f"SyftBox app ready at {syftbox_url}")
            self.server_url = syftbox_url
            self.current_stage = "syftbox"
            
            # Stop the thread server since SyftBox is available
            self._stop_thread_server()
        
        def on_syftbox_lost():
            """Called when SyftBox app becomes unavailable"""
            print("SyftBox app lost, falling back to thread server")
            self.current_stage = "thread"
            self.server_url = f"http://localhost:{self.thread_server_port}"
            
            # Restart thread server
            self._start_thread_server()
        
        # Start standard monitoring first
        self.syftbox_manager.start_monitoring(on_ready_callback=on_syftbox_ready)
        
        # Then start continuous monitoring for lost connections
        self._monitor_thread = threading.Thread(
            target=self._continuous_monitoring,
            args=(on_syftbox_ready, on_syftbox_lost),
            daemon=True
        )
        self._monitor_thread.start()
    
    def _continuous_monitoring(self, on_ready, on_lost):
        """Continuously monitor SyftBox availability and manage thread server"""
        syftbox_was_available = False
        
        while True:
            try:
                if self.syftbox_manager:
                    is_available = self.syftbox_manager.check_syftbox_server()
                    
                    if is_available and not syftbox_was_available:
                        # SyftBox became available
                        syftbox_was_available = True
                        on_ready(self.syftbox_manager.get_syftbox_server_url())
                    elif not is_available and syftbox_was_available:
                        # SyftBox became unavailable
                        syftbox_was_available = False
                        on_lost()
                
                time.sleep(2)  # Check every 2 seconds
            except Exception as e:
                print(f"Error in monitoring: {e}")
                time.sleep(5)
    
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
                    margin-bottom: 15px;
                }}
                .button-group {{
                    display: flex;
                    gap: 10px;
                    margin-top: 15px;
                }}
                .control-button {{
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    flex: 1;
                }}
                .control-button:disabled {{
                    background: #e0e0e0;
                    color: #999;
                    cursor: not-allowed;
                }}
                .kill-thread {{
                    background: #ff6b6b;
                    color: white;
                }}
                .kill-thread:hover:not(:disabled) {{
                    background: #ff5252;
                }}
                .kill-syftbox {{
                    background: #ff9800;
                    color: white;
                }}
                .kill-syftbox:hover:not(:disabled) {{
                    background: #f57c00;
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
                <div class="button-group">
                    <button class="control-button kill-thread" id="killThreadBtn" disabled onclick="killThreadServer()">
                        Kill Thread Server
                    </button>
                    <button class="control-button kill-syftbox" id="killSyftBoxBtn" disabled onclick="killSyftBoxApp()">
                        Kill SyftBox App
                    </button>
                </div>
            </div>
            <script>
                let currentStage = 'checkpoint';
                let isLive = false;
                let threadServerUrl = '{self.server_url}';
                let syftboxServerUrl = null;
                let lastSuccessfulData = {initial_data}; // Keep track of last good data
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
                        lastSuccessfulData = data; // Update checkpoint with fresh data
                    }} else {{
                        // Use last successful data as checkpoint
                        document.getElementById('timestamp').textContent = lastSuccessfulData.timestamp || 'N/A';
                        document.getElementById('formatted').textContent = lastSuccessfulData.formatted || 'N/A';
                    }}
                    
                    // Update status
                    const stage = stages[currentStage];
                    document.getElementById('status').innerHTML = `${{stage.icon}} ${{stage.name}}`;
                    document.getElementById('stage').textContent = `Stage: ${{currentStage}} - ${{stage.url || 'Local data'}}`;
                    
                    // Update button states
                    const killThreadBtn = document.getElementById('killThreadBtn');
                    const killSyftBoxBtn = document.getElementById('killSyftBoxBtn');
                    
                    // Thread server button: enabled only when thread server is running
                    killThreadBtn.disabled = currentStage !== 'thread';
                    
                    // SyftBox button: enabled only when SyftBox is running
                    killSyftBoxBtn.disabled = currentStage !== 'syftbox';
                }}
                
                async function killThreadServer() {{
                    try {{
                        // Signal to kill thread server
                        const response = await fetch(threadServerUrl + '/shutdown', {{
                            method: 'POST',
                            mode: 'cors',
                            cache: 'no-cache'
                        }});
                    }} catch (e) {{
                        // Server might not respond if it's shutting down
                    }}
                    
                    // Update UI immediately
                    currentStage = 'checkpoint';
                    updateDisplay();
                }}
                
                async function killSyftBoxApp() {{
                    // For SyftBox, we can't directly kill it from JavaScript
                    // But we can simulate it being unavailable
                    alert('To kill the SyftBox app, you need to stop it from the SyftBox interface or terminal.');
                    
                    // You could also make a request to a management endpoint if available
                    // For now, just update the UI to show it's checking
                    currentStage = 'checkpoint';
                    updateDisplay();
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
            style="width: 100%; height: 320px; border: none;"
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