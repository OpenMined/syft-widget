"""Debug utilities for syft-widget development and troubleshooting"""

import json
import sys
from typing import Dict, Any, Optional
from .server_backends import get_server_backend, syft_serve_available


def debug_widget_status(widget_obj=None) -> Dict[str, Any]:
    """Get comprehensive debug information about widget status
    
    Args:
        widget_obj: Optional widget object (DynamicWidget or APIDisplay) to debug
        
    Returns:
        Dict containing debug information
    """
    debug_info = {
        "syft_widget_version": None,
        "syft_serve_available": syft_serve_available(),
        "python_version": sys.version,
        "backend_info": {},
        "infrastructure_status": {},
        "widget_info": None
    }
    
    # Get version
    try:
        from . import __version__
        debug_info["syft_widget_version"] = __version__
    except:
        debug_info["syft_widget_version"] = "unknown"
    
    # Get backend information
    try:
        backend = get_server_backend()
        debug_info["backend_info"] = {
            "type": "syft-serve",
            "backend_class": backend.__class__.__name__
        }
        
        # Try to get server list if available
        if hasattr(backend, 'list_servers'):
            try:
                servers = backend.list_servers()
                debug_info["backend_info"]["servers"] = servers
                debug_info["backend_info"]["server_count"] = len(servers)
            except:
                debug_info["backend_info"]["servers"] = "error_retrieving"
    except Exception as e:
        debug_info["backend_info"] = {"error": str(e)}
    
    # Get infrastructure status
    try:
        from .widget_registry import get_infrastructure_status
        debug_info["infrastructure_status"] = get_infrastructure_status()
    except Exception as e:
        debug_info["infrastructure_status"] = {"error": str(e)}
    
    # Get widget-specific info if provided
    if widget_obj:
        try:
            if hasattr(widget_obj, 'get_debug_info'):
                debug_info["widget_info"] = widget_obj.get_debug_info()
            else:
                debug_info["widget_info"] = {
                    "type": widget_obj.__class__.__name__,
                    "id": getattr(widget_obj, 'id', 'unknown'),
                    "methods": [m for m in dir(widget_obj) if not m.startswith('_')]
                }
        except Exception as e:
            debug_info["widget_info"] = {"error": str(e)}
    
    return debug_info


def print_debug_status(widget_obj=None, detailed: bool = False):
    """Print formatted debug information
    
    Args:
        widget_obj: Optional widget object to debug
        detailed: Whether to show detailed information
    """
    info = debug_widget_status(widget_obj)
    
    print("=== syft-widget Debug Status ===")
    print(f"Version: {info['syft_widget_version']}")
    print(f"Python: {info['python_version']}")
    print(f"syft-serve available: {info['syft_serve_available']}")
    
    if info['backend_info']:
        print(f"\nBackend: {info['backend_info'].get('type', 'unknown')}")
        if 'server_count' in info['backend_info']:
            print(f"Active servers: {info['backend_info']['server_count']}")
    
    if info['infrastructure_status']:
        status = info['infrastructure_status']
        print(f"\nInfrastructure running: {status.get('running', 'unknown')}")
        if 'base_url' in status and status['base_url']:
            print(f"Base URL: {status['base_url']}")
    
    if info['widget_info']:
        widget_info = info['widget_info']
        print(f"\nWidget: {widget_info.get('type', 'unknown')}")
        if 'id' in widget_info:
            print(f"Widget ID: {widget_info['id']}")
    
    if detailed:
        print(f"\n=== Detailed Information ===")
        print(json.dumps(info, indent=2, default=str))


def check_dependencies() -> Dict[str, Any]:
    """Check status of optional dependencies
    
    Returns:
        Dict with dependency status information
    """
    deps = {
        "required": {},
        "optional": {}
    }
    
    # Check required dependencies
    required_deps = [
        "ipywidgets",
        "requests", 
        "fastapi",
        "uvicorn"
    ]
    
    for dep in required_deps:
        try:
            module = __import__(dep)
            deps["required"][dep] = {
                "available": True,
                "version": getattr(module, "__version__", "unknown")
            }
        except ImportError:
            deps["required"][dep] = {
                "available": False,
                "version": None
            }
    
    # Check optional dependencies
    optional_deps = [
        "syft_serve",
        "psutil"
    ]
    
    for dep in optional_deps:
        try:
            module = __import__(dep)
            deps["optional"][dep] = {
                "available": True,
                "version": getattr(module, "__version__", "unknown")
            }
        except ImportError:
            deps["optional"][dep] = {
                "available": False,
                "version": None
            }
    
    return deps


def print_dependency_status():
    """Print formatted dependency status"""
    deps = check_dependencies()
    
    print("=== Dependency Status ===")
    
    print("\nRequired:")
    for name, info in deps["required"].items():
        status = "✅" if info["available"] else "❌"
        version = f" (v{info['version']})" if info["version"] else ""
        print(f"  {status} {name}{version}")
    
    print("\nOptional:")
    for name, info in deps["optional"].items():
        status = "✅" if info["available"] else "⚠️"
        version = f" (v{info['version']})" if info["version"] else ""
        note = ""
        if name == "syft_serve" and not info["available"]:
            note = " - Install with: pip install syft-serve"
        elif name == "psutil" and not info["available"]:
            note = " - Install with: pip install psutil"
        print(f"  {status} {name}{version}{note}")


def test_widget_functionality(widget_class, **kwargs) -> Dict[str, Any]:
    """Test basic functionality of a widget class
    
    Args:
        widget_class: Widget class to test (e.g., DynamicWidget, APIDisplay)
        **kwargs: Arguments to pass to widget constructor
        
    Returns:
        Dict with test results
    """
    results = {
        "widget_class": widget_class.__name__,
        "construction": {"success": False, "error": None},
        "debug_info": {"success": False, "error": None},
        "server_methods": {"success": False, "error": None}
    }
    
    try:
        # Test widget construction
        widget = widget_class(**kwargs)
        results["construction"]["success"] = True
        
        # Test debug info
        try:
            if hasattr(widget, 'get_debug_info'):
                debug_info = widget.get_debug_info()
                results["debug_info"]["success"] = True
                results["debug_info"]["info"] = debug_info
        except Exception as e:
            results["debug_info"]["error"] = str(e)
        
        # Test server methods
        try:
            server_methods = []
            if hasattr(widget, 'restart_server'):
                server_methods.append("restart_server")
            if hasattr(widget, 'stop_server'):
                server_methods.append("stop_server")
            if hasattr(widget, 'get_server_status'):
                server_methods.append("get_server_status")
            if hasattr(widget, 'get_server_logs'):
                server_methods.append("get_server_logs")
            
            results["server_methods"]["success"] = True
            results["server_methods"]["available_methods"] = server_methods
        except Exception as e:
            results["server_methods"]["error"] = str(e)
            
    except Exception as e:
        results["construction"]["error"] = str(e)
    
    return results


def run_full_diagnostic(widget_obj: Optional[Any] = None) -> Dict[str, Any]:
    """Run a complete diagnostic of the syft-widget system
    
    Args:
        widget_obj: Optional widget object to include in diagnostics
        
    Returns:
        Dict with comprehensive diagnostic information
    """
    diagnostic = {
        "timestamp": None,
        "widget_status": None,
        "dependencies": None,
        "test_results": {}
    }
    
    # Add timestamp
    from datetime import datetime
    diagnostic["timestamp"] = datetime.now().isoformat()
    
    # Get widget status
    try:
        diagnostic["widget_status"] = debug_widget_status(widget_obj)
    except Exception as e:
        diagnostic["widget_status"] = {"error": str(e)}
    
    # Check dependencies
    try:
        diagnostic["dependencies"] = check_dependencies()
    except Exception as e:
        diagnostic["dependencies"] = {"error": str(e)}
    
    # Test widget classes if available
    widget_classes = []
    try:
        from .dynamic_widget import DynamicWidget
        widget_classes.append(DynamicWidget)
    except:
        pass
    
    try:
        from .display_objects import APIDisplay
        widget_classes.append(APIDisplay)
    except:
        pass
    
    for widget_class in widget_classes:
        try:
            # Test with minimal parameters
            if widget_class.__name__ == "APIDisplay":
                test_kwargs = {"endpoints": ["/test"], "start_infra": False}
            else:
                test_kwargs = {"start_infra": False}
            
            results = test_widget_functionality(widget_class, **test_kwargs)
            diagnostic["test_results"][widget_class.__name__] = results
        except Exception as e:
            diagnostic["test_results"][widget_class.__name__] = {"error": str(e)}
    
    return diagnostic


def print_full_diagnostic(widget_obj: Optional[Any] = None):
    """Print a comprehensive diagnostic report
    
    Args:
        widget_obj: Optional widget object to include in diagnostics
    """
    diagnostic = run_full_diagnostic(widget_obj)
    
    print("=== Full syft-widget Diagnostic ===")
    print(f"Timestamp: {diagnostic['timestamp']}")
    
    # Print dependency status
    if diagnostic.get("dependencies"):
        print_dependency_status()
    
    # Print widget status  
    if diagnostic.get("widget_status"):
        print_debug_status(widget_obj)
    
    # Print test results
    if diagnostic.get("test_results"):
        print(f"\n=== Widget Class Tests ===")
        for class_name, results in diagnostic["test_results"].items():
            if "error" in results:
                print(f"❌ {class_name}: {results['error']}")
            else:
                status = "✅" if results["construction"]["success"] else "❌"
                print(f"{status} {class_name}: Construction {'passed' if results['construction']['success'] else 'failed'}")
                
                if results.get("server_methods", {}).get("success"):
                    methods = results["server_methods"]["available_methods"]
                    print(f"   Server methods: {', '.join(methods)}")