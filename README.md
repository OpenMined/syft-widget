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

```bash
pip install syft-widget
```

Create a resilient widget in just a few lines:

```python
from syft_widget import APIDisplay

class SimpleWidget(APIDisplay):
    def __init__(self):
        super().__init__(endpoints=[])  # No endpoints needed for simple widgets
    
    def render_content(self, data, server_type="checkpoint"):
        # Shows different content based on connection mode
        mode_info = {
            "checkpoint": ("📁", "Using cached data"),
            "thread": ("🧵", "Connected to dev server"), 
            "syftbox": ("📦", "Connected to SyftBox")
        }
        icon, status = mode_info.get(server_type, ("❓", "Unknown"))
        
        return f"""
        <div style="padding: 20px; border: 2px solid #ccc; border-radius: 8px;">
            <h2>{icon} Live Widget Dashboard</h2>
            <p>Status: <strong>{status}</strong></p>
            <p>This widget automatically switches between modes!</p>
        </div>
        """

# Automatically works in all three modes
widget = SimpleWidget()
widget  # Display in Jupyter
```

For widgets that use data from endpoints:

```python
from syft_widget import APIDisplay, register_endpoint

# Create an endpoint (note: request parameter is optional for checkpoint mode)
@register_endpoint("/api/stats")
def get_stats(request=None):
    return {"users": 42, "files": 128, "status": "healthy"}

class DashboardWidget(APIDisplay):
    def __init__(self):
        super().__init__(endpoints=["/api/stats"])
    
    def render_content(self, data, server_type="checkpoint"):
        stats = data.get("/api/stats", {})
        users = stats.get("users", 0)
        files = stats.get("files", 0)
        
        return f"""
        <div style="padding: 20px; background: #f0f0f0; border-radius: 8px;">
            <h2>📊 System Dashboard</h2>
            <p>👥 Active Users: <strong>{users}</strong></p>
            <p>📁 Total Files: <strong>{files}</strong></p>
            <p>Mode: {server_type}</p>
        </div>
        """

widget = DashboardWidget()
widget  # Display in Jupyter
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