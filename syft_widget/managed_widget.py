import time
import threading
import random
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
        mode: str = "auto",
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
        self._stop_monitoring = False
        self._starting_thread_server = False
        self.mode = mode
        
        # Get initial mock data from endpoints
        self.initial_data = self._get_initial_data()
        
        if mode == "development":
            # Development mode: only use checkpoint and thread server
            print("Starting in development mode (no SyftBox integration)")
            self._start_thread_server()
        else:
            # Auto/production mode: full lifecycle
            # Start monitoring for SyftBox
            self._start_syftbox_monitoring()
            
            # Only start thread server if SyftBox isn't already available
            self._check_and_start_thread_server()
    
    def _check_and_start_thread_server(self):
        """Check if we need to start the thread server"""
        # First check if thread server is already running
        import requests
        try:
            response = requests.get(f"{self.server_url}/health", timeout=0.5)
            if response.status_code == 200:
                print(f"Thread server already running on {self.server_url}")
                self.current_stage = "thread"
                return
        except:
            pass
        
        # Quick check if SyftBox server is already available
        if self.syftbox_manager and self.syftbox_manager.check_syftbox_server():
            print("SyftBox server already available, skipping thread server")
            self.current_stage = "syftbox"
            self.server_url = self.syftbox_manager.get_syftbox_server_url()
        else:
            # No servers available, start thread server
            print("No existing servers found, starting thread server")
            self._start_thread_server()
    
    def _start_thread_server(self):
        """Start the Python thread server with a delay to simulate startup time"""
        print(f"_start_thread_server called. Current stage: {self.current_stage}, thread_server: {self.thread_server}")
        
        if self.thread_server:
            print("Thread server already running")
            return
        
        if self._starting_thread_server:
            print("Thread server already being started")
            return
        
        self._starting_thread_server = True
        
        # Check if port is already in use and try to kill existing process
        import socket
        import subprocess
        
        # First try to kill any existing process on this port
        self._kill_process_on_port(self.thread_server_port)
        
        # Try to find an available port, starting with the configured one
        available_port = None
        for port_offset in range(10):  # Try up to 10 ports
            test_port = self.thread_server_port + port_offset
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(('', test_port))
                sock.close()
                available_port = test_port
                break
            except OSError:
                if port_offset == 0:
                    print(f"Port {test_port} is still in use after kill attempt")
                continue
        
        if available_port is None:
            print(f"Could not find available port in range {self.thread_server_port}-{self.thread_server_port + 9}")
            return
        
        # Update our port and server URL
        if available_port != self.thread_server_port:
            print(f"Using alternate port {available_port} instead of {self.thread_server_port}")
        self.thread_server_port = available_port
        self.server_url = f"http://localhost:{self.thread_server_port}"
            
        def delayed_start():
            print(f"Thread server starting on port {self.thread_server_port}...")
            time.sleep(0.5)  # Much shorter delay for faster recovery
            
            try:
                self.thread_server = run_server_in_thread(port=self.thread_server_port, delay=0, endpoints=self.endpoints)
                self.current_stage = "thread"
                print(f"Thread server started on port {self.thread_server_port}")
                # Store the process for later cleanup
                if hasattr(self.thread_server, 'pid'):
                    print(f"Thread server process PID: {self.thread_server.pid}")
            except Exception as e:
                print(f"Failed to start thread server: {e}")
                self.current_stage = "checkpoint"
            finally:
                self._starting_thread_server = False
        
        # Start in a separate thread so it doesn't block
        start_thread = threading.Thread(target=delayed_start, daemon=True)
        start_thread.start()
    
    def _stop_thread_server(self):
        """Stop the thread server"""
        from .process_tracker import kill_processes_on_port
        
        print(f"_stop_thread_server called. Current thread_server: {self.thread_server}")
        
        if self.thread_server and hasattr(self.thread_server, 'is_alive'):
            print(f"Stopping thread server on port {self.thread_server_port}...")
            try:
                pid = self.thread_server.pid if hasattr(self.thread_server, 'pid') else None
                
                if self.thread_server.is_alive():
                    # Terminate the process
                    self.thread_server.terminate()
                    self.thread_server.join(timeout=2)  # Wait up to 2 seconds
                    
                    if self.thread_server.is_alive():
                        print("Thread server didn't stop gracefully, force killing...")
                        self.thread_server.kill()  # Force kill if still alive
                        self.thread_server.join(timeout=1)
                    
                    print("Thread server process terminated")
                else:
                    print("Thread server process was already dead")
                
                # Process cleanup complete
                    
            except Exception as e:
                print(f"Error stopping thread server: {e}")
            finally:
                self.thread_server = None
        else:
            print("No thread server to stop")
        
        # Always try to kill by port to catch any orphaned processes
        if self.thread_server_port:
            print(f"Killing any remaining processes on port {self.thread_server_port}")
            kill_processes_on_port(self.thread_server_port)
        
        self.thread_server = None
    
    def _kill_process_on_port(self, port):
        """Kill any process running on the specified port"""
        from .process_tracker import kill_processes_on_port
        kill_processes_on_port(port)
    
    def _start_syftbox_monitoring(self):
        """Start monitoring for SyftBox app"""
        if self.mode == "development":
            # Skip SyftBox in development mode
            return
            
        self.syftbox_manager = SyftBoxManager(
            app_name=self.app_name,
            repo_url=self.repo_url,
            discovery_port=self.discovery_port
        )
        
        def on_syftbox_ready(syftbox_url: str):
            """Called when SyftBox app is ready"""
            if self.current_stage == "syftbox":
                # Already in syftbox mode, skip
                return
                
            print(f"SyftBox app ready at {syftbox_url}")
            self.server_url = syftbox_url
            self.current_stage = "syftbox"
            
            # Wait a bit before stopping thread server to ensure smooth transition
            def delayed_stop():
                # Wait 10 seconds for frontend to switch + 5 seconds extra = 15 seconds total
                print("Waiting 15 seconds before stopping thread server (10s for frontend + 5s buffer)...")
                time.sleep(15)
                print("Stopping thread server after transition delay...")
                self._stop_thread_server()
            
            stop_thread = threading.Thread(target=delayed_stop, daemon=True)
            stop_thread.start()
        
        def on_syftbox_lost():
            """Called when SyftBox app becomes unavailable"""
            print(f"SyftBox app lost, falling back to thread server")
            self.current_stage = "checkpoint"  # First go to checkpoint
            
            # Restart thread server (which will update self.server_url with the actual port)
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
        # Give initial monitoring time to complete
        time.sleep(1)
        
        # Check initial state
        if self.current_stage == "syftbox":
            print("Already connected to SyftBox, monitoring for disconnection")
        elif self.current_stage == "thread":
            print("Thread server active, monitoring for SyftBox availability")
        
        last_syftbox_url = None
        consecutive_failures = 0
        thread_check_counter = 0
        next_filesystem_check = 0
        
        while not self._stop_monitoring:
            try:
                if self.syftbox_manager:
                    # Get current URL without clearing cache
                    current_url = self.syftbox_manager.get_syftbox_server_url()
                    is_available = self.syftbox_manager.check_syftbox_server()
                    
                    if is_available:
                        consecutive_failures = 0
                        
                        # Check version of running SyftBox app
                        needs_update = False
                        try:
                            import requests
                            version_response = requests.get(f"{current_url}/version", timeout=0.5)
                            if version_response.status_code == 200:
                                server_version = version_response.json().get("version", "unknown")
                                current_version = self.syftbox_manager.get_current_version()
                                
                                if server_version != "unknown" and server_version != current_version:
                                    print(f"SyftBox app version mismatch: server={server_version}, local={current_version}")
                                    
                                    # Compare versions - if local is newer, kill and remove the app
                                    def compare_versions(v1, v2):
                                        """Simple version comparison"""
                                        try:
                                            parts1 = [int(x) for x in v1.split('.')]
                                            parts2 = [int(x) for x in v2.split('.')]
                                            return parts1 > parts2
                                        except:
                                            return v1 > v2  # Fallback to string comparison
                                    
                                    if compare_versions(current_version, server_version):
                                        print(f"Local version ({current_version}) is newer than SyftBox app ({server_version})")
                                        needs_update = True
                        except:
                            pass
                        
                        if needs_update:
                            print("Killing outdated SyftBox app...")
                            # Try to kill the SyftBox app via API
                            try:
                                kill_response = requests.post(f"{current_url}/kill-syftbox", timeout=0.5)
                            except:
                                pass
                            
                            # Remove the app directory
                            time.sleep(1)  # Give it a moment to die
                            if self.syftbox_manager.remove_app():
                                print("Removed outdated SyftBox app, will re-clone on next check")
                                # Reset state
                                last_syftbox_url = None
                                if self.current_stage == "syftbox":
                                    on_lost()
                            else:
                                print("Failed to remove outdated app")
                        elif current_url != last_syftbox_url and self.current_stage != "syftbox":
                            # New SyftBox server detected with correct version
                            print(f"SyftBox server detected at {current_url}!")
                            print(f"Current stage: {self.current_stage}, Thread server: {self.thread_server}")
                            last_syftbox_url = current_url
                            on_ready(current_url)
                    else:
                        # Server check failed
                        if self.current_stage == "syftbox":
                            consecutive_failures += 1
                            # Only consider it lost after 2 consecutive failures (faster detection)
                            if consecutive_failures >= 2:
                                print(f"SyftBox server lost after {consecutive_failures} failed checks!")
                                last_syftbox_url = None
                                consecutive_failures = 0
                                on_lost()
                
                # Also check if we're in checkpoint mode and need a thread server
                if self.current_stage == "checkpoint":
                    thread_check_counter += 1
                    if thread_check_counter >= 2:  # After 3 seconds in checkpoint
                        print("Still in checkpoint mode, checking if thread server needed")
                        self._check_and_start_thread_server()
                        thread_check_counter = 0
                
                # If we're on thread server and SyftBox not available, periodically check filesystem
                if self.current_stage == "thread" and time.time() >= next_filesystem_check:
                    if not is_available and self.syftbox_manager:
                        print("Thread server active, checking if SyftBox app needs to be re-cloned...")
                        
                        # Check if app still exists
                        if not self.syftbox_manager.check_app_exists():
                            print("SyftBox app missing! Re-cloning...")
                            
                            # Clone in a separate thread to avoid blocking
                            def clone_async():
                                if self.syftbox_manager.clone_app():
                                    print("App re-cloned successfully, waiting for SyftBox to start it...")
                                else:
                                    print("Failed to re-clone app")
                            
                            clone_thread = threading.Thread(target=clone_async, daemon=True)
                            clone_thread.start()
                        else:
                            print("App exists but server not responding")
                        
                        # Schedule next check with random backoff
                        import random
                        backoff = random.randint(30, 90)
                        next_filesystem_check = time.time() + backoff
                        print(f"Next filesystem check in {backoff} seconds")
                
                time.sleep(1.5)  # Check every 1.5 seconds for faster response
            except Exception as e:
                print(f"Error in monitoring: {e}")
                time.sleep(5)
        
        print("Monitoring thread exiting")
    
    def _get_initial_data(self):
        """Get initial data from endpoints"""
        if not self.endpoints:
            return {}
        
        # Import here to avoid circular imports
        from .endpoints import ENDPOINT_REGISTRY
        
        # Get data from first endpoint
        first_endpoint = list(self.endpoints.keys())[0] if self.endpoints else None
        if first_endpoint and first_endpoint in ENDPOINT_REGISTRY:
            try:
                return ENDPOINT_REGISTRY[first_endpoint]()
            except Exception:
                pass
        return {}
    
    def _update_display(self):
        """Render the widget"""
        self._render_iframe(self.initial_data)
    
    def _format_initial_data(self, data):
        """Format initial data for display - override this for custom formatting"""
        if not data:
            return "No data available"
        
        # Default: show as formatted JSON
        import json
        return f'<pre>{json.dumps(data, indent=2)}</pre>'
    
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
                .data-display {{
                    color: #333;
                    margin-bottom: 15px;
                    min-height: 60px;
                }}
                .data-display pre {{
                    background: #f8f8f8;
                    padding: 10px;
                    border-radius: 4px;
                    overflow-x: auto;
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
                <div class="data-display" id="data-display">{self._format_initial_data(initial_data)}</div>
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
                let originalThreadPort = {self.thread_server_port};
                let syftboxServerUrl = null;
                let lastSuccessfulData = {initial_data}; // Keep track of last good data
                const endpoints = {self.endpoints};
                const endpoint = endpoints[0] || '/health'; // Use first endpoint or fallback to health
                const checkInterval = {int(self.check_interval * 1000)};
                const syftboxCheckInterval = 2000; // Check for SyftBox every 2 seconds
                
                // Default data formatter - can be overridden by subclasses
                function formatData(data) {{
                    if (!data || Object.keys(data).length === 0) {{
                        return 'No data available';
                    }}
                    return '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                }}
                
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
                
                async function findThreadServer() {{
                    // Try the current URL first
                    if (await checkServer(threadServerUrl)) {{
                        return threadServerUrl;
                    }}
                    
                    // If that fails, try a range of ports starting from the original
                    for (let offset = 0; offset < 10; offset++) {{
                        const testUrl = `http://localhost:${{originalThreadPort + offset}}`;
                        if (await checkServer(testUrl)) {{
                            console.log(`Found thread server on alternate port: ${{testUrl}}`);
                            return testUrl;
                        }}
                    }}
                    
                    return null;
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
                        // Add timeout to prevent hanging
                        const controller = new AbortController();
                        const timeoutId = setTimeout(() => controller.abort(), 500); // 500ms timeout
                        
                        const response = await fetch('http://localhost:62050', {{
                            method: 'GET',
                            mode: 'cors',
                            cache: 'no-cache',
                            signal: controller.signal
                        }});
                        
                        clearTimeout(timeoutId);
                        
                        if (response.ok) {{
                            const data = await response.json();
                            const port = data.main_server_port;
                            if (port) {{
                                return `http://localhost:${{port}}`;
                            }}
                        }}
                    }} catch (e) {{
                        // Discovery not available or timed out
                    }}
                    return null;
                }}
                
                let syftboxReadyCount = 0;
                let syftboxFailureCount = 0;
                let transitioningToSyftbox = false;
                let syftboxDiscoveredTime = null;
                
                async function updateDisplay() {{
                    let data = null;
                    let newStage = currentStage;
                    
                    // Check for SyftBox server first
                    // Only check discovery if we're not already in syftbox mode or transitioning
                    if (!syftboxServerUrl && currentStage !== 'syftbox' && !transitioningToSyftbox) {{
                        syftboxServerUrl = await checkSyftBoxDiscovery();
                    }}
                    
                    let syftboxAvailable = false;
                    let threadAvailable = false;
                    
                    // Check both servers
                    if (syftboxServerUrl && currentStage !== 'syftbox' && !transitioningToSyftbox) {{
                        // For SyftBox, require both health check AND successful data fetch
                        const healthOk = await checkServer(syftboxServerUrl);
                        if (healthOk) {{
                            const testData = await getData(syftboxServerUrl);
                            if (testData && testData.timestamp) {{
                                syftboxReadyCount++;
                                
                                // Mark when we first discovered SyftBox
                                if (!syftboxDiscoveredTime) {{
                                    syftboxDiscoveredTime = Date.now();
                                    console.log('SyftBox server discovered, waiting 10 seconds before switching...');
                                }}
                                
                                // Check if we've waited long enough (10 seconds)
                                const waitTime = Date.now() - syftboxDiscoveredTime;
                                if (waitTime >= 10000 && syftboxReadyCount >= 2) {{
                                    syftboxAvailable = true;
                                    data = testData;
                                    newStage = 'syftbox';
                                    stages.syftbox.url = syftboxServerUrl;
                                    transitioningToSyftbox = true;  // Lock in the transition
                                    console.log('Switching to SyftBox server after', Math.round(waitTime/1000), 'seconds');
                                    
                                    // Clear the transition lock after a delay
                                    setTimeout(() => {{
                                        transitioningToSyftbox = false;
                                        syftboxFailureCount = 0;  // Reset failure count
                                    }}, 5000);  // 5 seconds should be enough for backend to kill thread
                                }} else {{
                                    // Keep using thread server while we wait
                                    console.log('Waiting before switch:', Math.round((10000 - waitTime)/1000), 'seconds remaining');
                                }}
                            }} else {{
                                syftboxReadyCount = 0;
                                syftboxDiscoveredTime = null;  // Reset discovery time
                            }}
                        }} else {{
                            syftboxReadyCount = 0;
                            syftboxDiscoveredTime = null;  // Reset discovery time
                            syftboxServerUrl = null;
                        }}
                    }} else if (syftboxServerUrl && currentStage === 'syftbox') {{
                        // Already on SyftBox, check if still available
                        syftboxAvailable = await checkServer(syftboxServerUrl);
                        if (syftboxAvailable) {{
                            data = await getData(syftboxServerUrl);
                            if (data) {{
                                syftboxFailureCount = 0;  // Reset on success
                                syftboxAvailable = true;  // Stay on SyftBox
                            }} else {{
                                syftboxFailureCount++;
                                // Only mark as unavailable after multiple failures
                                if (syftboxFailureCount >= 3) {{
                                    syftboxAvailable = false;
                                }} else {{
                                    // Use last successful data while we wait
                                    syftboxAvailable = true;
                                    data = lastSuccessfulData;
                                }}
                            }}
                        }} else {{
                            syftboxFailureCount++;
                            if (syftboxFailureCount >= 3) {{
                                syftboxServerUrl = null;
                                syftboxReadyCount = 0;
                                syftboxFailureCount = 0;
                                syftboxDiscoveredTime = null;  // Reset discovery time
                            }} else {{
                                // Keep using SyftBox during temporary failures
                                syftboxAvailable = true;
                                data = lastSuccessfulData;
                            }}
                        }}
                    }}
                    
                    // If SyftBox not available and not transitioning, check thread server
                    if (!syftboxAvailable && !transitioningToSyftbox) {{
                        const foundThreadUrl = await findThreadServer();
                        if (foundThreadUrl) {{
                            threadServerUrl = foundThreadUrl;
                            stages.thread.url = threadServerUrl;
                            data = await getData(threadServerUrl);
                            if (data) {{
                                threadAvailable = true;
                                newStage = 'thread';
                            }}
                        }}
                    }}
                    
                    // If neither available, use checkpoint
                    if (!syftboxAvailable && !threadAvailable) {{
                        newStage = 'checkpoint';
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
                        document.getElementById('data-display').innerHTML = formatData(data);
                        lastSuccessfulData = data; // Update checkpoint with fresh data
                    }} else {{
                        // Use last successful data as checkpoint
                        document.getElementById('data-display').innerHTML = formatData(lastSuccessfulData);
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
                    if (!syftboxServerUrl) {{
                        alert('SyftBox server URL not available');
                        return;
                    }}
                    
                    try {{
                        // Call the kill endpoint on the SyftBox server
                        const response = await fetch(syftboxServerUrl + '/kill-syftbox', {{
                            method: 'POST',
                            mode: 'cors',
                            cache: 'no-cache'
                        }});
                        
                        if (response.ok) {{
                            console.log('SyftBox app kill signal sent');
                        }}
                    }} catch (e) {{
                        // Server might not respond if it's shutting down
                        console.log('SyftBox app may be shutting down');
                    }}
                    
                    // Update UI immediately to checkpoint
                    currentStage = 'checkpoint';
                    syftboxServerUrl = null;
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
        print("Stopping ManagedWidget...")
        
        # Stop monitoring thread
        if hasattr(self, '_monitor_thread') and self._monitor_thread and self._monitor_thread.is_alive():
            print("Stopping monitoring thread...")
            # Set a flag to stop the monitoring loop
            self._stop_monitoring = True
            
        # Stop thread server
        self._stop_thread_server()
        
        # Stop SyftBox monitoring
        if self.syftbox_manager:
            self.syftbox_manager.stop_monitoring()
            
        # Call parent stop
        super().stop()
        print("ManagedWidget stopped")
    
    def __del__(self):
        """Cleanup when object is garbage collected"""
        try:
            print(f"ManagedWidget being destroyed (port {self.thread_server_port})")
            self.stop()
        except Exception as e:
            print(f"Error during ManagedWidget cleanup: {e}")
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup when exiting context"""
        self.stop()
        return False

