import time
from typing import Optional, Dict, Callable, Any
import requests
import ipywidgets as widgets
import json
import uuid
from .widget import SyftWidget


class InteractiveWidget(SyftWidget):
    def __init__(self, server_instance=None, **kwargs):
        # Create snapshot functions
        def get_time_snapshot():
            timestamp = int(time.time())
            formatted = time.strftime("%Y-%m-%d %H:%M:%S")
            return {"timestamp": timestamp, "formatted": formatted}
        
        def get_action_snapshot():
            return {"message": "Action not available (server offline)"}
        
        endpoints = {
            "/time": get_time_snapshot,
            "/action": get_action_snapshot
        }
        
        super().__init__(endpoints=endpoints, **kwargs)
        self.widget_id = f"syft-widget-{uuid.uuid4().hex[:8]}"
        self.iframe = widgets.HTML()
        self._create_snapshots()
        
    def _update_display(self):
        # Render with snapshot data
        time_data = self.snapshot_cache.get("/time", {})
        action_data = self.snapshot_cache.get("/action", {})
        self._render_iframe(time_data, action_data)
    
    def _render_iframe(self, time_data, action_data):
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
                    font-size: 24px;
                    color: #333;
                    margin-bottom: 10px;
                    font-weight: bold;
                }}
                .formatted {{
                    font-size: 16px;
                    color: #666;
                    margin-bottom: 20px;
                }}
                .status {{
                    font-size: 14px;
                    color: #666;
                    padding: 10px 0;
                    border-top: 1px solid #eee;
                    border-bottom: 1px solid #eee;
                    margin-bottom: 20px;
                }}
                .action-button {{
                    background: #007bff;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-size: 16px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    margin-right: 10px;
                }}
                .action-button:hover:not(:disabled) {{
                    background: #0056b3;
                    transform: translateY(-1px);
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                }}
                .action-button:disabled {{
                    background: #ccc;
                    cursor: not-allowed;
                    opacity: 0.6;
                }}
                .action-result {{
                    margin-top: 20px;
                    padding: 10px;
                    background: #f8f9fa;
                    border-radius: 5px;
                    font-size: 14px;
                    min-height: 40px;
                    display: flex;
                    align-items: center;
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
                <div class="timestamp" id="timestamp">{time_data.get('timestamp', 'N/A')}</div>
                <div class="formatted" id="formatted">{time_data.get('formatted', 'N/A')}</div>
                <div class="status" id="status">🔴 Snapshot</div>
                
                <button class="action-button" id="actionButton" disabled onclick="performAction()">
                    Perform Server Action
                </button>
                <button class="action-button" id="refreshButton" onclick="manualRefresh()">
                    Refresh Status
                </button>
                
                <div class="action-result" id="actionResult">
                    Server not available - button will enable when server is online
                </div>
            </div>
            <script>
                let isLive = false;
                const serverUrl = '{self.server_url}';
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
                            // Server is available, get time data
                            const dataResponse = await fetch(serverUrl + '/time', {{
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
                    updateDisplay({time_data}, false);
                }}
                
                function updateDisplay(data, serverAvailable) {{
                    const wasLive = isLive;
                    isLive = serverAvailable;
                    
                    // Update time display
                    document.getElementById('timestamp').textContent = data.timestamp || 'N/A';
                    document.getElementById('formatted').textContent = data.formatted || 'N/A';
                    document.getElementById('status').innerHTML = serverAvailable ? '🟢 Live Server' : '🔴 Snapshot';
                    
                    // Update button state
                    const actionButton = document.getElementById('actionButton');
                    actionButton.disabled = !serverAvailable;
                    
                    // Update action result message
                    const actionResult = document.getElementById('actionResult');
                    if (!serverAvailable && actionResult.textContent.includes('Server not available')) {{
                        // Keep the existing message
                    }} else if (serverAvailable && actionResult.textContent.includes('Server not available')) {{
                        actionResult.textContent = 'Server is online - button is now active!';
                    }}
                    
                    // Add pulse animation when status changes
                    if (wasLive !== isLive) {{
                        const container = document.getElementById('container');
                        container.classList.add('pulse');
                        setTimeout(() => container.classList.remove('pulse'), 500);
                    }}
                }}
                
                async function performAction() {{
                    const actionResult = document.getElementById('actionResult');
                    actionResult.textContent = 'Performing action...';
                    
                    try {{
                        const response = await fetch(serverUrl + '/action', {{
                            method: 'POST',
                            mode: 'cors',
                            cache: 'no-cache',
                            headers: {{
                                'Content-Type': 'application/json'
                            }},
                            body: JSON.stringify({{timestamp: new Date().toISOString()}})
                        }});
                        
                        if (response.ok) {{
                            const data = await response.json();
                            actionResult.textContent = '✅ ' + (data.message || 'Action completed successfully!');
                        }} else {{
                            actionResult.textContent = '❌ Action failed: ' + response.statusText;
                        }}
                    }} catch (e) {{
                        actionResult.textContent = '❌ Error: ' + e.message;
                    }}
                }}
                
                function manualRefresh() {{
                    checkAndUpdate();
                    const actionResult = document.getElementById('actionResult');
                    actionResult.textContent = 'Checking server status...';
                    setTimeout(() => {{
                        if (!isLive) {{
                            actionResult.textContent = 'Server not available - button will enable when server is online';
                        }} else {{
                            actionResult.textContent = 'Server is online - button is now active!';
                        }}
                    }}, 500);
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
            style="width: 100%; height: 300px; border: none;"
            sandbox="allow-scripts">
        </iframe>
        """
        
        self.iframe.value = iframe_html
    
    def display(self):
        self._update_display()
        return self.iframe