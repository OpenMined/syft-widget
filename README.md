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

Create a live dashboard widget that monitors system metrics:

```python
from syft_widget import APIDisplay, register_endpoint

# First, write the endpoint to a file (required for thread server)
endpoint_code = '''
from syft_widget import register_endpoint

@register_endpoint("/api/metrics")
def get_metrics(request=None):
    # In production: reads real system metrics
    # In checkpoint mode: returns mock data
    return {"cpu": 45, "memory": 72, "disk": 89}
'''

with open("dashboard_endpoints.py", "w") as f:
    f.write(endpoint_code)

# Import the endpoint from the file
import dashboard_endpoints

# Create an iframe-based dashboard widget (solves mode switching issues)
class SystemDashboard(APIDisplay):
    def __init__(self):
        super().__init__(endpoints=["/api/metrics"])
    
    def render_content(self, data, server_type="checkpoint"):
        import base64
        
        # Create complete HTML page for iframe
        iframe_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }}
                .dashboard {{
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    background: white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    padding: 15px;
                }}
                .mode-selector {{
                    background: #f8f9fa;
                    padding: 10px;
                    border-bottom: 1px solid #dee2e6;
                    display: flex;
                    gap: 8px;
                    align-items: center;
                }}
                .mode-btn {{
                    border: none;
                    padding: 4px 12px;
                    border-radius: 15px;
                    font-size: 13px;
                    cursor: pointer;
                }}
                .mode-btn.active {{
                    color: white;
                }}
                .mode-btn.checkpoint {{ background: #6c757d; }}
                .mode-btn.thread {{ background: #28a745; }}
                .mode-btn.syftbox {{ background: #007bff; }}
                .mode-btn.inactive {{ background: #e9ecef; color: #666; }}
                .metrics {{
                    padding: 20px;
                }}
                .metric {{
                    margin-bottom: 15px;
                }}
                .metric-header {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 5px;
                }}
                .metric-bar {{
                    background: #e9ecef;
                    height: 20px;
                    border-radius: 10px;
                    overflow: hidden;
                }}
                .metric-fill {{
                    height: 100%;
                }}
                .cpu {{ background: #28a745; }}
                .memory {{ background: #17a2b8; }}
                .disk {{ background: #6f42c1; }}
                .footer {{
                    background: #f8f9fa;
                    padding: 10px;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="dashboard">
                <div class="header">
                    <h3 style="margin: 0;">📊 System Dashboard</h3>
                </div>
                
                <div class="mode-selector">
                    <span style="font-size: 14px; color: #666;">Mode:</span>
                    <button class="mode-btn checkpoint {'active' if server_type == 'checkpoint' else 'inactive'}">📁 Checkpoint</button>
                    <button class="mode-btn thread {'active' if server_type == 'thread' else 'inactive'}">🧵 Thread</button>
                    <button class="mode-btn syftbox {'active' if server_type == 'syftbox' else 'inactive'}">📦 Syftbox</button>
                </div>
                
                <div class="metrics" id="metrics">
                    <!-- Metrics will be updated by JavaScript -->
                </div>
                
                <div class="footer">
                    Live updates every 5 seconds • Connected to: <span id="current-mode">{server_type}</span>
                </div>
            </div>

            <script>
                let currentData = {{}};
                let currentServerType = '{server_type}';
                
                function updateMetrics(metrics, serverType) {{
                    currentServerType = serverType;
                    
                    // Update mode buttons
                    document.querySelectorAll('.mode-btn').forEach(btn => {{
                        btn.classList.remove('active');
                        btn.classList.add('inactive');
                    }});
                    
                    const activeBtn = document.querySelector(`.mode-btn.${{serverType}}`);
                    if (activeBtn) {{
                        activeBtn.classList.remove('inactive');
                        activeBtn.classList.add('active');
                    }}
                    
                    // Update metrics
                    const metricsEl = document.getElementById('metrics');
                    metricsEl.innerHTML = `
                        <div class="metric">
                            <div class="metric-header">
                                <span>CPU Usage</span>
                                <span style="font-weight: bold;">${{metrics.cpu || 0}}%</span>
                            </div>
                            <div class="metric-bar">
                                <div class="metric-fill cpu" style="width: ${{metrics.cpu || 0}}%;"></div>
                            </div>
                        </div>
                        <div class="metric">
                            <div class="metric-header">
                                <span>Memory</span>
                                <span style="font-weight: bold;">${{metrics.memory || 0}}%</span>
                            </div>
                            <div class="metric-bar">
                                <div class="metric-fill memory" style="width: ${{metrics.memory || 0}}%;"></div>
                            </div>
                        </div>
                        <div class="metric">
                            <div class="metric-header">
                                <span>Disk</span>
                                <span style="font-weight: bold;">${{metrics.disk || 0}}%</span>
                            </div>
                            <div class="metric-bar">
                                <div class="metric-fill disk" style="width: ${{metrics.disk || 0}}%;"></div>
                            </div>
                        </div>
                    `;
                    
                    // Update footer
                    document.getElementById('current-mode').textContent = serverType;
                    
                    console.log('🔄 IFRAME: Updated widget - Mode:', serverType, 'Data:', metrics);
                }}
                
                // Server detection logic
                async function checkServer(url) {{
                    try {{
                        const controller = new AbortController();
                        const timeoutId = setTimeout(() => controller.abort(), 500);
                        const response = await fetch(url + '/health', {{ 
                            signal: controller.signal,
                            mode: 'cors' 
                        }});
                        clearTimeout(timeoutId);
                        return response.ok;
                    }} catch(e) {{
                        return false;
                    }}
                }}
                
                async function updateDisplay() {{
                    let baseUrl = null;
                    let serverType = "checkpoint";
                    
                    // Check for thread servers (8000-8010)
                    for (let port = 8000; port <= 8010; port++) {{
                        if (await checkServer(`http://localhost:${{port}}`)) {{
                            baseUrl = `http://localhost:${{port}}`;
                            serverType = "thread";
                            console.log('🔄 IFRAME: Found thread server at port', port);
                            break;
                        }}
                    }}
                    
                    // Fetch data if server available
                    let metrics = {{cpu: 45, memory: 72, disk: 89}}; // Default checkpoint data
                    if (baseUrl) {{
                        try {{
                            const response = await fetch(baseUrl + '/api/metrics', {{ mode: 'cors' }});
                            if (response.ok) {{
                                metrics = await response.json();
                                console.log('🔄 IFRAME: Fetched live data:', metrics);
                            }}
                        }} catch(e) {{
                            console.log('🔄 IFRAME: Error fetching data, using checkpoint:', e);
                            serverType = "checkpoint";
                        }}
                    }}
                    
                    // Update display
                    updateMetrics(metrics, serverType);
                }}
                
                // Initial load
                updateMetrics({data.get("/api/metrics", {"cpu": 45, "memory": 72, "disk": 89})}, '{server_type}');
                
                // Start polling
                setInterval(updateDisplay, 1000);
                updateDisplay();
            </script>
        </body>
        </html>
        '''
        
        # Encode HTML for iframe
        encoded_html = base64.b64encode(iframe_html.encode('utf-8')).decode('utf-8')
        
        return f'''
        <iframe 
            src="data:text/html;base64,{encoded_html}"
            width="100%" 
            height="400"
            frameborder="0"
            style="border: none; border-radius: 8px;">
        </iframe>
        '''

# Use it in Jupyter
widget = SystemDashboard()
widget  # Shows dashboard in checkpoint mode (📁 Mock Data)

# To see live mode switching, start the thread server:
from syft_widget import start_infrastructure
start_infrastructure()  # Widget will automatically switch to 🧵 Thread mode

# Note: If the widget doesn't switch modes, check the browser console for CORS errors.
# The widget should automatically detect the server within ~5 seconds.

# To stop the server:
# from syft_widget import stop_infrastructure
# stop_infrastructure()
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