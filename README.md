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

Create a live file monitoring widget that automatically updates:

```python
from syft_widget import APIDisplay, register_endpoint
from datetime import datetime

# Define what data to monitor
@register_endpoint("/api/files")
def get_files(request=None):
    # In production, this scans real filesystems
    # In checkpoint mode, returns mock data
    return {
        "files": [
            {"name": "data.csv", "size": 1024, "modified": "10:30"},
            {"name": "report.pdf", "size": 2048, "modified": "11:45"}
        ],
        "total": 2,
        "last_scan": datetime.now().strftime("%H:%M:%S")
    }

# Create the monitoring widget
class FileMonitorWidget(APIDisplay):
    def __init__(self):
        super().__init__(endpoints=["/api/files"])
    
    def render_content(self, data, server_type="checkpoint"):
        files = data.get("/api/files", {}).get("files", [])
        
        # Mode indicator badge
        modes = {
            "checkpoint": ("📁 Mock Data", "#6c757d"),
            "thread": ("🧵 Dev Server", "#28a745"),
            "syftbox": ("📦 Production", "#007bff")
        }
        mode_label, mode_color = modes.get(server_type, ("", ""))
        
        # Build the widget HTML
        rows = "".join(f'<tr><td>{f["name"]}</td><td>{f["size"]}B</td></tr>' 
                      for f in files)
        
        return f'''
        <div style="border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
            <div style="background: #f8f9fa; padding: 10px; display: flex; justify-content: space-between;">
                <strong>📂 File Monitor</strong>
                <span style="background: {mode_color}; color: white; padding: 2px 8px; 
                            border-radius: 4px; font-size: 12px;">{mode_label}</span>
            </div>
            <table style="width: 100%; border-collapse: collapse;">
                <thead><tr style="background: #e9ecef;">
                    <th style="padding: 8px; text-align: left;">File</th>
                    <th style="padding: 8px; text-align: right;">Size</th>
                </tr></thead>
                <tbody>{rows if rows else '<tr><td colspan="2" style="padding: 20px; text-align: center; color: #999;">No files found</td></tr>'}</tbody>
            </table>
        </div>
        '''

# Use it - automatically works in all modes!
widget = FileMonitorWidget()
widget  # Display in Jupyter - updates live when files change
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