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

# Create a dashboard widget
class SystemDashboard(APIDisplay):
    def __init__(self):
        super().__init__(endpoints=["/api/metrics"])
    
    def render_content(self, data, server_type="checkpoint"):
        metrics = data.get("/api/metrics", {})
        
        # Determine active mode
        modes = {"checkpoint": "📁", "thread": "🧵", "syftbox": "📦"}
        colors = {"checkpoint": "#6c757d", "thread": "#28a745", "syftbox": "#007bff"}
        
        return f'''
        <div style="border: 1px solid #ddd; border-radius: 8px; background: white; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1); font-family: sans-serif;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea, #764ba2); 
                        color: white; padding: 15px;">
                <h3 style="margin: 0;">📊 System Dashboard</h3>
            </div>
            
            <!-- Mode Selector -->
            <div style="background: #f8f9fa; padding: 10px; border-bottom: 1px solid #dee2e6;">
                <div style="display: flex; gap: 8px; align-items: center;">
                    <span style="font-size: 14px; color: #666;">Mode:</span>
                    {"".join(f'''<button style="background: {colors[mode] if server_type == mode else '#e9ecef'}; 
                             color: {'white' if server_type == mode else '#666'}; border: none; 
                             padding: 4px 12px; border-radius: 15px; font-size: 13px;">
                             {icon} {mode.title()}</button>''' 
                             for mode, icon in modes.items())}
                </div>
            </div>
            
            <!-- Metrics -->
            <div style="padding: 20px;">
                <div style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>CPU Usage</span>
                        <span style="font-weight: bold;">{metrics.get('cpu', 0)}%</span>
                    </div>
                    <div style="background: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden;">
                        <div style="background: #28a745; width: {metrics.get('cpu', 0)}%; height: 100%;"></div>
                    </div>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>Memory</span>
                        <span style="font-weight: bold;">{metrics.get('memory', 0)}%</span>
                    </div>
                    <div style="background: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden;">
                        <div style="background: #17a2b8; width: {metrics.get('memory', 0)}%; height: 100%;"></div>
                    </div>
                </div>
                
                <div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>Disk</span>
                        <span style="font-weight: bold;">{metrics.get('disk', 0)}%</span>
                    </div>
                    <div style="background: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden;">
                        <div style="background: #6f42c1; width: {metrics.get('disk', 0)}%; height: 100%;"></div>
                    </div>
                </div>
            </div>
            
            <!-- Footer -->
            <div style="background: #f8f9fa; padding: 10px; text-align: center; 
                        font-size: 12px; color: #666;">
                Live updates every 5 seconds • Connected to: {server_type}
            </div>
        </div>
        '''
    
    def get_update_script(self):
        """Override to maintain widget HTML (prevents fallback to JSON)"""
        return '''
        // Get fresh data and current mode
        const metrics = currentData['/api/metrics'] || {};
        const currentMode = serverType; // Direct reference to avoid sync issues
        
        // Mode styling
        const modes = {"checkpoint": "📁", "thread": "🧵", "syftbox": "📦"};
        const colors = {"checkpoint": "#6c757d", "thread": "#28a745", "syftbox": "#007bff"};
        
        // Log for debugging
        console.log(`🔄 Updating widget - Mode: ${currentMode}, Data:`, metrics);
        
        // Generate mode buttons
        let modeButtons = '';
        Object.entries(modes).forEach(([mode, icon]) => {
            const isActive = mode === currentMode;
            const bgColor = isActive ? colors[mode] : '#e9ecef';
            const textColor = isActive ? 'white' : '#666';
            
            modeButtons += `<button style="background: ${bgColor}; 
                                           color: ${textColor}; border: none; 
                                           padding: 4px 12px; border-radius: 15px; font-size: 13px;">
                                       ${icon} ${mode.charAt(0).toUpperCase() + mode.slice(1)}
                                   </button>`;
        });
        
        // Completely replace widget content
        element.innerHTML = `
        <div style="border: 1px solid #ddd; border-radius: 8px; background: white; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1); font-family: sans-serif;">
            <div style="background: linear-gradient(135deg, #667eea, #764ba2); 
                        color: white; padding: 15px;">
                <h3 style="margin: 0;">📊 System Dashboard</h3>
            </div>
            <div style="background: #f8f9fa; padding: 10px; border-bottom: 1px solid #dee2e6;">
                <div style="display: flex; gap: 8px; align-items: center;">
                    <span style="font-size: 14px; color: #666;">Mode:</span>
                    ${modeButtons}
                </div>
            </div>
            <div style="padding: 20px;">
                <div style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>CPU Usage</span>
                        <span style="font-weight: bold;">${metrics.cpu || 0}%</span>
                    </div>
                    <div style="background: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden;">
                        <div style="background: #28a745; width: ${metrics.cpu || 0}%; height: 100%;"></div>
                    </div>
                </div>
                <div style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>Memory</span>
                        <span style="font-weight: bold;">${metrics.memory || 0}%</span>
                    </div>
                    <div style="background: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden;">
                        <div style="background: #17a2b8; width: ${metrics.memory || 0}%; height: 100%;"></div>
                    </div>
                </div>
                <div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>Disk</span>
                        <span style="font-weight: bold;">${metrics.disk || 0}%</span>
                    </div>
                    <div style="background: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden;">
                        <div style="background: #6f42c1; width: ${metrics.disk || 0}%; height: 100%;"></div>
                    </div>
                </div>
            </div>
            <div style="background: #f8f9fa; padding: 10px; text-align: center; 
                        font-size: 12px; color: #666;">
                Live updates every 5 seconds • Connected to: ${currentMode}
            </div>
        </div>
        `;
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