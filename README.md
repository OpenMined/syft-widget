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

# Create endpoint with real timestamp data
@register_endpoint("/api/time")
def get_current_time(request=None):
    return {"timestamp": time.time(), "formatted": time.strftime("%H:%M:%S")}

# Simple live timestamp widget  
class TimeWidget(APIDisplay):
    def __init__(self):
        super().__init__(endpoints=["/api/time"])
    
    def render_content(self, data, server_type="checkpoint"):
        time_data = data.get("/api/time", {"formatted": "12:34:56"})
        current_time = time_data.get("formatted", "12:34:56")
        
        # Create iframe with live timestamp display
        html = f'''<!DOCTYPE html>
<html><head><style>
body {{ margin:0; font-family:Arial; background:#f5f5f5; }}
.widget {{ background:white; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.1); margin:10px; }}
.header {{ background:linear-gradient(135deg,#667eea,#764ba2); color:white; padding:15px; border-radius:8px 8px 0 0; }}
.content {{ padding:30px; text-align:center; }}
.time-display {{ font-size:48px; font-weight:bold; color:#333; margin:20px 0; font-family:monospace; }}
.mode {{ display:inline-block; padding:4px 12px; border-radius:15px; font-size:12px; color:white; }}
.checkpoint {{ background:#6c757d; }} .thread {{ background:#28a745; }} .syftbox {{ background:#007bff; }}
</style></head><body>
<div class="widget">
    <div class="header"><h3 style="margin:0">🕐 Live Time</h3></div>
    <div class="content">
        <div class="time-display" id="time-display">{current_time}</div>
        <div>Mode: <span class="mode {server_type}" id="mode-display">{server_type.title()}</span></div>
    </div>
</div>
<script>
async function updateTime() {{
    try {{
        for (let port = 8000; port <= 8010; port++) {{
            const resp = await fetch(`http://localhost:${{port}}/api/time`, {{mode:'cors', signal:AbortSignal.timeout(500)}});
            if (resp.ok) {{
                const data = await resp.json();
                document.getElementById('time-display').textContent = data.formatted;
                document.getElementById('mode-display').textContent = 'Thread';
                document.getElementById('mode-display').className = 'mode thread';
                return;
            }}
        }}
        // Fallback to local time if no server
        document.getElementById('time-display').textContent = new Date().toLocaleTimeString();
        document.getElementById('mode-display').textContent = 'Checkpoint';
        document.getElementById('mode-display').className = 'mode checkpoint';
    }} catch(e) {{}}
}}
setInterval(updateTime, 1000);
</script></body></html>'''
        
        return f'<iframe src="data:text/html;base64,{base64.b64encode(html.encode()).decode()}" width="100%" height="200" frameborder="0" style="border:none;border-radius:8px;"></iframe>'
    
    def get_update_script(self):
        return "// Iframe handles updates internally"

# Use it
widget = TimeWidget()
widget

# To see live mode switching, start the thread server:
from syft_widget import start_infrastructure
start_infrastructure()  # Widget will automatically switch to 🧵 Thread mode and show live data
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