"""syft-widget - Create Jupyter widgets with multi-server support"""

__version__ = "0.2.0"

# Lazy imports to avoid requiring ipywidgets when just using display objects
def __getattr__(name):
    """Lazy import attributes to avoid circular dependencies"""
    
    # Map of attribute names to their modules
    import_map = {
        # Display classes (main public API)
        "APIDisplay": ("display_objects", "APIDisplay"),
        "TimeDisplay": ("demo_widgets", "TimeDisplay"),
        "CPUDisplay": ("demo_widgets", "CPUDisplay"),
        "SystemDashboard": ("demo_widgets", "SystemDashboard"),
        
        # Infrastructure functions
        "start_infrastructure": ("widget_registry", "start_infrastructure"),
        "stop_infrastructure": ("widget_registry", "stop_infrastructure"),
        
        # Advanced API (for creating custom endpoints)
        "register_endpoint": ("endpoints", "register_endpoint"),
        "get_all_endpoints": ("endpoints", "get_all_endpoints"),
    }
    
    if name in import_map:
        module_name, attr_name = import_map[name]
        import importlib
        module = importlib.import_module(f".{module_name}", package=__name__)
        return getattr(module, attr_name)
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    # Display classes (main public API)
    "APIDisplay", "TimeDisplay", "CPUDisplay", "SystemDashboard",
    # Infrastructure management
    "start_infrastructure", "stop_infrastructure",
    # Advanced API
    "register_endpoint", "get_all_endpoints"
]