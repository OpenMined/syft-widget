# syft-widget

**Create live-updating Jupyter widgets with automatic server management.**

[![PyPI](https://img.shields.io/pypi/v/syft-widget)](https://pypi.org/project/syft-widget/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)

## 🚀 What is syft-widget?

syft-widget automatically spawns server processes for your Jupyter widgets using syft-serve:

- ✨ **Zero Configuration**: Every widget automatically gets its own server process
- 🔄 **Live Updates**: Widgets refresh data automatically 
- 🛡️ **Process Isolation**: Each widget runs in its own isolated environment
- 📦 **Dependency Management**: Per-widget Python package isolation
- 🚀 **Built on syft-serve**: Advanced process lifecycle management

## 💻 Quick Start

```bash
pip install syft-widget
```

```python
from syft_widget import DynamicWidget
import time

class LiveClock(DynamicWidget):
    def get_endpoints(self):
        @self.endpoint("/api/time")
        def get_time():
            return {"time": time.strftime("%H:%M:%S")}
    
    def get_template(self):
        return '<div data-field="time">{time}</div>'

clock = LiveClock()  # Server process starts automatically!
clock
```

## 📚 Learn More

**👉 See [tutorial.ipynb](tutorial.ipynb) for the complete guide to the new API!**

The tutorial covers:
- Basic widget creation with automatic servers
- System monitoring widgets  
- Server management and control
- Dependency isolation
- Server deduplication
- Debugging and diagnostics
- Custom styling and themes

## 🔧 What's New in v0.3.0

- **Automatic Process Spawning**: Every widget creates its own server automatically
- **Simplified API**: No more manual server setup or backend selection  
- **syft-serve Integration**: Built-in process isolation and lifecycle management
- **Required Dependencies**: syft-serve is now included automatically

## 🚀 Get Started

Open [tutorial.ipynb](tutorial.ipynb) in Jupyter and start building!

## 📄 License

Apache License 2.0 - see [LICENSE](LICENSE) for details.