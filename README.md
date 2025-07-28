# syft-widget

Build resilient jupyter widgets for viewing syft's private, distributed filesystem

## What is syft-widget?

The Syft ecosystem enables distributed computation over private data, where state is stored as files across many computers. But working with distributed state is hard — especially when you can't see the data directly.

syft-widget solves this by providing file-backed Jupyter widgets that:
- **Watch files for changes** and update in real-time
- **Persist across kernel restarts** via local servers
- **Load instantly** with checkpoint data, then seamlessly transition to live updates
- **Run in protected iframes** isolated from Jupyter's complex DOM

## Why Files?

Decentralized systems need maximum interoperability. Because of Unix, files are the universal language that lets everyone work together — without centralizing data to a single server.

## Installation

```bash
pip install syft-widget
```

## Quick Start

```python
import syft_widget as sw

class LiveClock(sw.DynamicWidget):
    def get_endpoints(self):
        @self.endpoint("/api/time")
        def get_time():
            import time
            return {"time": time.strftime("%H:%M:%S")}
    
    def get_template(self):
        return '''Time:<span data-field="time">{time}</span>'''

# Widget title defaults to class name in snake_case
clock = LiveClock()
clock
```

## How It Works

### 🚀 Instant Load + Live Updates

```
t=0ms:   Python renders template with checkpoint data → instant display
t=50ms:  Spawns FastAPI server watching your files
t=100ms: JavaScript connects and starts live updates
```

Users see content immediately, while servers persist across notebook reloads.

### 📁 File-Backed Architecture

1. **Your widget reads files** (data, state, permissions, etc.)
2. **Server watches for changes** using FSEvents/inotify  
3. **Updates stream to browser** via periodic HTTP requests
4. **State persists** even when notebooks restart

## API Overview

### Basic Widget

```python
class MyWidget(sw.DynamicWidget):
    def get_endpoints(self):
        @self.endpoint("/api/data")
        def get_data():
            # Read your files here
            return {"value": read_file()}
    
    def get_template(self):
        return '''<div data-field="value">{value}</div>'''
```

### Configuration Options

```python
widget = MyWidget(
    server_name="my_server",      # Optional: defaults to class name
    height="200px",               # Widget height
    update_interval=1000,         # Refresh rate (ms)
    dependencies=["pandas"],      # Server dependencies
    expiration_seconds=3600       # Auto-cleanup after 1 hour
)
```

### Server Management

Widgets automatically manage servers via [syft-serve](https://github.com/OpenMined/syft-serve):

```python
# Access the underlying server
widget.server.status      # "running"
widget.server.url         # http://localhost:8001
widget.server.stdout.tail(20)  # View logs

# Manual control if needed
import syft_serve as ss
ss.servers  # List all servers
ss.servers.terminate_all()
```

## Real-World Example

Monitor distributed compute jobs:

```python
class JobMonitor(sw.DynamicWidget):
    def get_endpoints(self):
        @self.endpoint("/api/jobs")
        def get_jobs():
            # Read job states from distributed file system
            jobs = []
            for job_file in Path("jobs/").glob("*.json"):
                jobs.append(json.loads(job_file.read_text()))
            return {"jobs": jobs, "total": len(jobs)}
    
    def get_template(self):
        return '''
        <h3>Distributed Jobs: <span data-field="total">{total}</span></h3>
        <div data-field="jobs">{jobs}</div>
        '''

monitor = JobMonitor()
monitor  # Updates live as job files change
```

## Documentation

- [Full Documentation](https://openmined.github.io/syft-widget)
- [API Reference](https://openmined.github.io/syft-widget/api)
- [Tutorial Notebook](https://colab.research.google.com/github/OpenMined/syft-widget/blob/main/tutorial.ipynb)

## Development

```bash
# Clone the repo
git clone https://github.com/OpenMined/syft-widget.git
cd syft-widget

# Install in development mode
pip install -e .

# Run tests
pytest tests/

# Serve documentation locally
python serve_docs.py
```

## Requirements

- Python ≥ 3.9
- Jupyter (Notebook, Lab, or compatible)
- [syft-serve](https://github.com/OpenMined/syft-serve) (installed automatically)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## About

syft-widget is part of the [OpenMined](https://openmined.org) ecosystem, building privacy-preserving tools for the decentralized web.

---

<p align="center">
  <i>With file-backed widgets — private, distributed state can be effortless</i>
</p>
