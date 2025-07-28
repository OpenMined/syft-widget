"""syft-widget - Create Jupyter widgets with automatic server management via syft-serve"""

__version__ = "0.3.1"

# syft-serve is a required dependency
import syft_serve
SYFT_SERVE_AVAILABLE = True

# Clean and simple import - no legacy integration checks

# Lazy imports to avoid requiring ipywidgets when just using display objects
def __getattr__(name):
    """Lazy import attributes to avoid circular dependencies"""
    
    # Map of attribute names to their modules
    import_map = {
        # Display classes (main public API)
        "DynamicWidget": ("dynamic_widget", "DynamicWidget"),
        "APIDisplay": ("display_objects", "APIDisplay"),
        
        # Infrastructure functions
        "start_infrastructure": ("widget_registry", "start_infrastructure"),
        "stop_infrastructure": ("widget_registry", "stop_infrastructure"),
        "get_infrastructure_status": ("widget_registry", "get_infrastructure_status"),
        
        # Server backend management
        "get_server_backend": ("server_backends", "get_server_backend"),
        "syft_serve_available": ("server_backends", "syft_serve_available"),
        
        # Debug utilities
        "debug_widget_status": ("debug_utils", "debug_widget_status"),
        "print_debug_status": ("debug_utils", "print_debug_status"),
        "check_dependencies": ("debug_utils", "check_dependencies"),
        "print_dependency_status": ("debug_utils", "print_dependency_status"),
        "run_full_diagnostic": ("debug_utils", "run_full_diagnostic"),
        "print_full_diagnostic": ("debug_utils", "print_full_diagnostic"),
        
        # Advanced API (deprecated - use DynamicWidget instead)
        # "register_endpoint": Removed - use DynamicWidget.endpoint decorator
        # "get_all_endpoints": Removed - use DynamicWidget for endpoint management
        
        # Production mode utilities (deprecated)
        # "enable_production_mode": Removed in cleanup
        # "check_integration": Removed in cleanup  
        # "fix_integration": Removed in cleanup
    }
    
    if name in import_map:
        module_name, attr_name = import_map[name]
        import importlib
        module = importlib.import_module(f".{module_name}", package=__name__)
        return getattr(module, attr_name)
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    # Display classes (main public API)
    "DynamicWidget", "APIDisplay",
    # Infrastructure management
    "start_infrastructure", "stop_infrastructure", "get_infrastructure_status",
    # Server backend management
    "get_server_backend", "syft_serve_available",
    # Debug utilities
    "debug_widget_status", "print_debug_status", "check_dependencies", "print_dependency_status",
    "run_full_diagnostic", "print_full_diagnostic"
]