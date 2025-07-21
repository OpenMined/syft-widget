"""Display objects that use the fixed endpoints"""
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
                    // Try thread server ports
                    const threadPorts = [8001, 8000];
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


class TimeDisplay(APIDisplay):
    """Display current time and uptime"""
    
    def __init__(self):
        super().__init__(endpoints=["/time/current", "/time/uptime"])
    
    def render_content(self, data, server_type="checkpoint"):
        current = data.get("/time/current", {})
        uptime = data.get("/time/uptime", {})
        
        # Server type badge
        badge_color = {"checkpoint": "#6c757d", "thread": "#28a745", "syftbox": "#007bff"}.get(server_type, "#6c757d")
        server_label = {"checkpoint": "📁 Checkpoint", "thread": "🧵 Thread Server", "syftbox": "📦 SyftBox"}.get(server_type, server_type)
        
        return f"""
        <div style="font-family: -apple-system, sans-serif; padding: 20px; background: #f0f8ff; border-radius: 8px; position: relative;">
            <div style="position: absolute; top: 10px; right: 10px; background: {badge_color}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                {server_label}
            </div>
            
            <h3 style="margin: 0 0 15px 0;">⏰ Time Information</h3>
            
            <div style="margin-bottom: 15px;">
                <div style="font-size: 24px; font-weight: bold;">{current.get('formatted', 'Loading...')}</div>
                <div style="color: #666; font-size: 14px;">
                    Timestamp: {current.get('timestamp', '...')} | 
                    Timezone: {current.get('timezone', '...')}
                </div>
            </div>
            
            <div style="padding-top: 15px; border-top: 1px solid #ddd;">
                <strong>System Uptime:</strong> {uptime.get('formatted', 'Loading...')}
            </div>
        </div>
        """
    
    def get_update_script(self):
        return """
        const current = currentData['/time/current'] || {};
        const uptime = currentData['/time/uptime'] || {};
        
        // Server type badge
        const badgeColors = {checkpoint: "#6c757d", thread: "#28a745", syftbox: "#007bff"};
        const serverLabels = {checkpoint: "📁 Checkpoint", thread: "🧵 Thread Server", syftbox: "📦 SyftBox"};
        const badgeColor = badgeColors[currentServerType] || "#6c757d";
        const serverLabel = serverLabels[currentServerType] || currentServerType;
        
        element.innerHTML = `
        <div style="font-family: -apple-system, sans-serif; padding: 20px; background: #f0f8ff; border-radius: 8px; position: relative;">
            <div style="position: absolute; top: 10px; right: 10px; background: ${badgeColor}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                ${serverLabel}
            </div>
            
            <h3 style="margin: 0 0 15px 0;">⏰ Time Information</h3>
            
            <div style="margin-bottom: 15px;">
                <div style="font-size: 24px; font-weight: bold;">${current.formatted || 'Loading...'}</div>
                <div style="color: #666; font-size: 14px;">
                    Timestamp: ${current.timestamp || '...'} | 
                    Timezone: ${current.timezone || '...'}
                </div>
            </div>
            
            <div style="padding-top: 15px; border-top: 1px solid #ddd;">
                <strong>System Uptime:</strong> ${uptime.formatted || 'Loading...'}
            </div>
        </div>
        `;
        """


class CPUDisplay(APIDisplay):
    """Display CPU statistics with visual gauge"""
    
    def __init__(self):
        super().__init__(endpoints=["/system/cpu"])
    
    def render_content(self, data, server_type="checkpoint"):
        cpu = data.get("/system/cpu", {})
        usage = cpu.get('usage_percent', 0)
        color = self._get_color(usage)
        
        # Server type badge
        badge_color = {"checkpoint": "#6c757d", "thread": "#28a745", "syftbox": "#007bff"}.get(server_type, "#6c757d")
        server_label = {"checkpoint": "📁 Checkpoint", "thread": "🧵 Thread Server", "syftbox": "📦 SyftBox"}.get(server_type, server_type)
        
        return f"""
        <div style="font-family: -apple-system, sans-serif; padding: 20px; background: #fff; border: 1px solid #ddd; border-radius: 8px; position: relative;">
            <div style="position: absolute; top: 10px; right: 10px; background: {badge_color}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                {server_label}
            </div>
            
            <h3 style="margin: 0 0 15px 0;">🖥️ CPU Monitor</h3>
            
            <div style="margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span>CPU Usage</span>
                    <span style="font-weight: bold; color: {color};">{usage}%</span>
                </div>
                <div style="background: #e0e0e0; height: 30px; border-radius: 15px; overflow: hidden;">
                    <div style="background: {color}; height: 100%; width: {usage}%; transition: all 0.3s ease;"></div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 14px;">
                <div>
                    <strong>Cores:</strong> {cpu.get('cores', '...')}
                </div>
                <div>
                    <strong>Temperature:</strong> {cpu.get('temperature', '...')}°C
                </div>
                <div style="grid-column: 1 / -1;">
                    <strong>Load Average:</strong> {', '.join(map(str, cpu.get('load_average', ['...', '...', '...'])))}
                </div>
            </div>
        </div>
        """
    
    def _get_color(self, usage):
        """Get color based on usage percentage"""
        if usage < 50:
            return "#4CAF50"  # Green
        elif usage < 80:
            return "#FF9800"  # Orange
        else:
            return "#F44336"  # Red
    
    def get_update_script(self):
        return """
        const cpu = currentData['/system/cpu'] || {};
        const usage = cpu.usage_percent || 0;
        const color = usage < 50 ? '#4CAF50' : usage < 80 ? '#FF9800' : '#F44336';
        
        // Server type badge
        const badgeColors = {checkpoint: "#6c757d", thread: "#28a745", syftbox: "#007bff"};
        const serverLabels = {checkpoint: "📁 Checkpoint", thread: "🧵 Thread Server", syftbox: "📦 SyftBox"};
        const badgeColor = badgeColors[currentServerType] || "#6c757d";
        const serverLabel = serverLabels[currentServerType] || currentServerType;
        
        element.innerHTML = `
        <div style="font-family: -apple-system, sans-serif; padding: 20px; background: #fff; border: 1px solid #ddd; border-radius: 8px; position: relative;">
            <div style="position: absolute; top: 10px; right: 10px; background: ${badgeColor}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                ${serverLabel}
            </div>
            
            <h3 style="margin: 0 0 15px 0;">🖥️ CPU Monitor</h3>
            
            <div style="margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span>CPU Usage</span>
                    <span style="font-weight: bold; color: ${color};">${usage}%</span>
                </div>
                <div style="background: #e0e0e0; height: 30px; border-radius: 15px; overflow: hidden;">
                    <div style="background: ${color}; height: 100%; width: ${usage}%; transition: all 0.3s ease;"></div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 14px;">
                <div>
                    <strong>Cores:</strong> ${cpu.cores || '...'}
                </div>
                <div>
                    <strong>Temperature:</strong> ${cpu.temperature || '...'}°C
                </div>
                <div style="grid-column: 1 / -1;">
                    <strong>Load Average:</strong> ${(cpu.load_average || ['...', '...', '...']).join(', ')}
                </div>
            </div>
        </div>
        `;
        """


class SystemDashboard(APIDisplay):
    """Complete system dashboard with multiple metrics"""
    
    def __init__(self):
        super().__init__(endpoints=[
            "/system/cpu",
            "/system/memory", 
            "/system/disk",
            "/network/status"
        ])
    
    def render_content(self, data, server_type="checkpoint"):
        cpu = data.get("/system/cpu", {})
        memory = data.get("/system/memory", {})
        disk = data.get("/system/disk", {})
        network = data.get("/network/status", {})
        
        # Server type badge
        badge_color = {"checkpoint": "#6c757d", "thread": "#28a745", "syftbox": "#007bff"}.get(server_type, "#6c757d")
        server_label = {"checkpoint": "📁 Checkpoint", "thread": "🧵 Thread Server", "syftbox": "📦 SyftBox"}.get(server_type, server_type)
        
        return f"""
        <div style="font-family: -apple-system, sans-serif; padding: 20px; background: #f5f5f5; border-radius: 8px; position: relative;">
            <div style="position: absolute; top: 10px; right: 10px; background: {badge_color}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                {server_label}
            </div>
            
            <h2 style="margin: 0 0 20px 0;">📊 System Dashboard</h2>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                {self._render_metric("CPU", cpu.get('usage_percent', 0), "%", self._get_color(cpu.get('usage_percent', 0)))}
                {self._render_metric("Memory", memory.get('percent', 0), "%", self._get_color(memory.get('percent', 0)))}
                {self._render_metric("Disk", disk.get('percent', 0), "%", self._get_color(disk.get('percent', 0)))}
                
                <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h4 style="margin: 0 0 10px 0;">🌐 Network</h4>
                    <div style="font-size: 14px;">
                        <div>Status: <span style="color: #4CAF50;">●</span> Connected</div>
                        <div>↓ {network.get('download_mbps', '...')} Mbps | ↑ {network.get('upload_mbps', '...')} Mbps</div>
                        <div>Latency: {network.get('latency_ms', '...')} ms</div>
                    </div>
                </div>
            </div>
        </div>
        """
    
    def _render_metric(self, name, value, unit, color):
        return f"""
        <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h4 style="margin: 0 0 10px 0;">{name}</h4>
            <div style="font-size: 32px; font-weight: bold; color: {color};">{value}{unit}</div>
            <div style="background: #e0e0e0; height: 8px; border-radius: 4px; overflow: hidden; margin-top: 10px;">
                <div style="background: {color}; height: 100%; width: {value}%;"></div>
            </div>
        </div>
        """
    
    def _get_color(self, value):
        if value < 50:
            return "#4CAF50"
        elif value < 80:
            return "#FF9800"
        else:
            return "#F44336"
    
    def get_update_script(self):
        return """
        const cpu = currentData['/system/cpu'] || {};
        const memory = currentData['/system/memory'] || {};
        const disk = currentData['/system/disk'] || {};
        const network = currentData['/network/status'] || {};
        
        // Server type badge
        const badgeColors = {checkpoint: "#6c757d", thread: "#28a745", syftbox: "#007bff"};
        const serverLabels = {checkpoint: "📁 Checkpoint", thread: "🧵 Thread Server", syftbox: "📦 SyftBox"};
        const badgeColor = badgeColors[currentServerType] || "#6c757d";
        const serverLabel = serverLabels[currentServerType] || currentServerType;
        
        // Helper function to get color
        const getColor = (value) => {
            if (value < 50) return '#4CAF50';
            if (value < 80) return '#FF9800';
            return '#F44336';
        };
        
        // Helper function to render metric
        const renderMetric = (name, value, unit) => {
            const color = getColor(value);
            return `
            <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="margin: 0 0 10px 0;">${name}</h4>
                <div style="font-size: 32px; font-weight: bold; color: ${color};">${value}${unit}</div>
                <div style="background: #e0e0e0; height: 8px; border-radius: 4px; overflow: hidden; margin-top: 10px;">
                    <div style="background: ${color}; height: 100%; width: ${value}%;"></div>
                </div>
            </div>
            `;
        };
        
        element.innerHTML = `
        <div style="font-family: -apple-system, sans-serif; padding: 20px; background: #f5f5f5; border-radius: 8px; position: relative;">
            <div style="position: absolute; top: 10px; right: 10px; background: ${badgeColor}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                ${serverLabel}
            </div>
            
            <h2 style="margin: 0 0 20px 0;">📊 System Dashboard</h2>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                ${renderMetric("CPU", cpu.usage_percent || 0, "%")}
                ${renderMetric("Memory", memory.percent || 0, "%")}
                ${renderMetric("Disk", disk.percent || 0, "%")}
                
                <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h4 style="margin: 0 0 10px 0;">🌐 Network</h4>
                    <div style="font-size: 14px;">
                        <div>Status: <span style="color: #4CAF50;">●</span> Connected</div>
                        <div>↓ ${network.download_mbps || '...'} Mbps | ↑ ${network.upload_mbps || '...'} Mbps</div>
                        <div>Latency: ${network.latency_ms || '...'} ms</div>
                    </div>
                </div>
            </div>
        </div>
        `;
        """