# syft-widget

**Build resilient, live-updating widget systems that monitor filesystems and never break.**

[![Documentation](https://img.shields.io/badge/docs-syft--widget-blue)](https://openmined.github.io/syft-widget/)
[![PyPI](https://img.shields.io/pypi/v/syft-widget)](https://pypi.org/project/syft-widget/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)

## ✨ The Problem

Traditional Jupyter widgets fail when servers go down, don't update automatically, and require complex setup. Your data visualization shouldn't depend on infrastructure being perfect.

## 🚀 The Solution

syft-widget provides a **three-mode architecture** that ensures your widgets always work:

1. **📦 SyftBox Mode** - Production deployment with live filesystem monitoring
2. **🧵 Thread Mode** - Development server for testing with real data
3. **📁 Checkpoint Mode** - Fallback with mock data when servers are down

Your widgets automatically transition between modes, so users **never see a broken widget**.

## 💻 Quick Start

> **Note:** syft-widget is designed for **Jupyter notebooks**. In a Python REPL, you'll see JSON data instead of the widget UI.

```bash
pip install syft-widget
```

Create a simple live timestamp widget:

```python
from syft_widget import APIDisplay, register_endpoint
import time, base64

# Write endpoint to file (required for thread server)
with open("time_endpoint.py", "w") as f:
    f.write('''
from syft_widget import register_endpoint
import time
import os

@register_endpoint("/api/system")
def get_system_info(request=None):
    # Get CPU load average (only available on server, not in browser)
    try:
        load_avg = os.getloadavg()[0] * 100  # 1-minute load average as percentage
        load_avg = min(load_avg, 100)  # Cap at 100%
    except:
        load_avg = 0
    
    return {
        "timestamp": time.time(), 
        "formatted_time": time.strftime("%H:%M:%S"),
        "cpu_load": round(load_avg, 1),
        "server_pid": os.getpid(),
        "source": "SERVER"
    }
''')

# Import the endpoint
import time_endpoint

# Simple live system monitor widget  
class SystemWidget(APIDisplay):
    def __init__(self):
        super().__init__(endpoints=["/api/system"])
    
    def render_content(self, data, server_type="checkpoint"):
        system_data = data.get("/api/system", {"formatted_time": "12:34:56", "cpu_load": 0, "source": "MOCK"})
        current_time = system_data.get("formatted_time", "12:34:56")
        cpu_load = system_data.get("cpu_load", 0)
        source = system_data.get("source", "MOCK")
        
        # Create iframe with live system display
        html = f'''<!DOCTYPE html>
<html><head><style>
body {{ margin:0; font-family:Arial; background:#f5f5f5; }}
.widget {{ background:white; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.1); margin:10px; }}
.header {{ background:linear-gradient(135deg,#667eea,#764ba2); color:white; padding:15px; border-radius:8px 8px 0 0; }}
.content {{ padding:30px; text-align:center; }}
.time-display {{ font-size:48px; font-weight:bold; color:#333; margin:20px 0; font-family:monospace; }}
.cpu-display {{ font-size:24px; font-weight:bold; color:#28a745; margin:10px 0; }}
.mode {{ display:inline-block; padding:4px 12px; border-radius:15px; font-size:12px; color:white; }}
.checkpoint {{ background:#6c757d; }} .thread {{ background:#28a745; }} .syftbox {{ background:#007bff; }}
.source {{ font-size:10px; color:#666; margin-top:10px; }}
</style></head><body>
<div class="widget">
    <div class="header"><h3 style="margin:0">⚡ System Monitor</h3></div>
    <div class="content">
        <div class="time-display" id="time-display">{current_time}</div>
        <div class="cpu-display" id="cpu-display">CPU: {cpu_load}%</div>
        <div>Mode: <span class="mode {server_type}" id="mode-display">{server_type.title()}</span></div>
        <div class="source" id="source-display">Source: {source}</div>
    </div>
</div>
<script>
let connectedPort = null;
let consecutiveFailures = 0;

async function tryPort(port) {{
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 500);
    try {{
        const resp = await fetch(`http://localhost:${{port}}/api/system`, {{
            mode: 'cors',
            signal: controller.signal
        }});
        clearTimeout(timeoutId);
        return resp.ok ? resp : null;
    }} catch(e) {{
        clearTimeout(timeoutId);
        return null;
    }}
}}

async function updateSystem() {{
    try {{
        // If we have a connected port, try it first
        if (connectedPort) {{
            const resp = await tryPort(connectedPort);
            if (resp) {{
                const data = await resp.json();
                document.getElementById('time-display').textContent = data.formatted_time;
                document.getElementById('cpu-display').textContent = `CPU: ${{data.cpu_load}}%`;
                document.getElementById('mode-display').textContent = 'Thread';
                document.getElementById('mode-display').className = 'mode thread';
                document.getElementById('source-display').textContent = `Source: ${{data.source}} (PID: ${{data.server_pid}})`;
                consecutiveFailures = 0;
                return;
            }} else {{
                consecutiveFailures++;
                console.log(`⚠️ Lost connection to port ${{connectedPort}} (failure ${{consecutiveFailures}})`);
                
                // After 3 failures, start scanning for new ports
                if (consecutiveFailures >= 3) {{
                    console.log('🔄 Starting port scan after connection loss');
                    connectedPort = null;
                    consecutiveFailures = 0;
                }}
            }}
        }}
        
        // Scan for servers (only if no connected port or connection lost)
        if (!connectedPort) {{
            console.log('🔍 Scanning ports 8000-8010...');
            for (let port = 8000; port <= 8010; port++) {{
                const resp = await tryPort(port);
                if (resp) {{
                    const data = await resp.json();
                    connectedPort = port;
                    consecutiveFailures = 0;
                    
                    document.getElementById('time-display').textContent = data.formatted_time;
                    document.getElementById('cpu-display').textContent = `CPU: ${{data.cpu_load}}%`;
                    document.getElementById('mode-display').textContent = 'Thread';
                    document.getElementById('mode-display').className = 'mode thread';
                    document.getElementById('source-display').textContent = `Source: ${{data.source}} (PID: ${{data.server_pid}})`;
                    console.log(`✅ Connected to Thread server on port ${{port}}`);
                    return;
                }}
            }}
            console.log('📁 No server found - staying in checkpoint mode');
        }}
    }} catch(e) {{
        console.error('❌ Error in updateSystem:', e);
    }}
}}
setInterval(updateSystem, 1000);
</script></body></html>'''
        
        return f'<iframe src="data:text/html;base64,{base64.b64encode(html.encode()).decode()}" width="100%" height="200" frameborder="0" style="border:none;border-radius:8px;"></iframe>'
    
    def get_update_script(self):
        return "// Iframe handles updates internally"
    
    def _repr_html_(self):
        """Override to return only iframe, bypassing main widget JavaScript"""
        return self.render_content({}, "checkpoint")

def restart_infrastructure():
    """Properly restart the infrastructure after it's been stopped"""
    from syft_widget.widget_registry import get_current_registry
    
    # Get the registry and force cleanup
    registry = get_current_registry()
    
    # Stop any existing infrastructure
    registry.stop()
    
    # Reset internal state
    if hasattr(registry, '_widget') and registry._widget:
        registry._widget._starting_thread_server = False
        registry._widget._stop_monitoring = True
    
    # Wait a moment for cleanup
    import time
    time.sleep(1)
    
    # Start fresh
    from syft_widget import start_infrastructure
    start_infrastructure()

# Use it
widget = SystemWidget()
widget

# To see live mode switching, start the thread server:
from syft_widget import start_infrastructure
start_infrastructure()  # Widget will automatically switch to 🧵 Thread mode and show live data

# If start_infrastructure() stops working after interruption, use:
# restart_infrastructure()
```

## 📚 Documentation

Visit our comprehensive documentation at **[openmined.github.io/syft-widget](https://openmined.github.io/syft-widget/)** for:

- 🎓 **[Interactive Tutorial](https://openmined.github.io/syft-widget/)** - Build your first widget in Google Colab
- 📖 **[API Reference](https://openmined.github.io/syft-widget/api/)** - Complete API documentation
- 🏗️ **Architecture Guide** - Understand the three-mode system
- 🚀 **Deployment Guide** - Deploy to production with SyftBox

## 🎯 Key Features

- **Never Break** - Automatic fallback ensures widgets always display
- **Live Updates** - Monitor filesystems and update in real-time
- **Zero Config** - Start with mock data, scale to production
- **REST APIs** - Built-in endpoint creation with CORS handling
- **Multi-User** - Production-ready with permissions support
- **Hot Reload** - Development mode with automatic reloading

## 🤝 Community

syft-widget is part of the [OpenMined](https://openmined.org) ecosystem, building privacy-preserving data science tools.

- 🐛 [Report Issues](https://github.com/OpenMined/syft-widget/issues)
- 💬 [Join Discussions](https://github.com/OpenMined/syft-widget/discussions)
- 🌟 [Star on GitHub](https://github.com/OpenMined/syft-widget)

## 📄 License

Apache License 2.0 - see [LICENSE](LICENSE) for details.