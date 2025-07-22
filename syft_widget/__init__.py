"""syft-widget - Create Jupyter widgets with multi-server support"""

__version__ = "0.2.0"

# Check for production mode integration on import
def _check_integration_on_import():
    """Check integration status on import but don't spam"""
    import os
    from pathlib import Path
    
    # Only check if we're in a directory that looks like a package
    cwd = Path.cwd()
    
    # Skip check if we're in the syft-widget directory itself
    if (cwd / "syft_widget").exists():
        return
    
    # Skip check if we're in common non-package directories
    skip_dirs = {"site-packages", "dist-packages", "__pycache__", ".git", "notebooks", "examples"}
    if any(part in skip_dirs for part in cwd.parts):
        return
    
    # Only check if run_widgets.sh exists (production mode enabled)
    run_widgets_sh = cwd / "run_widgets.sh"
    if run_widgets_sh.exists():
        try:
            from .production import check_integration
            check_integration(quiet=False)
        except Exception:
            # Don't break imports if something goes wrong
            pass

# Run the check
_check_integration_on_import()

# Lazy imports to avoid requiring ipywidgets when just using display objects
def __getattr__(name):
    """Lazy import attributes to avoid circular dependencies"""
    
    # Map of attribute names to their modules
    import_map = {
        # Display classes (main public API)
        "APIDisplay": ("display_objects", "APIDisplay"),
        
        # Infrastructure functions
        "start_infrastructure": ("widget_registry", "start_infrastructure"),
        "stop_infrastructure": ("widget_registry", "stop_infrastructure"),
        
        # Advanced API (for creating custom endpoints)
        "register_endpoint": ("endpoints", "register_endpoint"),
        "get_all_endpoints": ("endpoints", "get_all_endpoints"),
        
        # Production mode utilities
        "enable_production_mode": ("production", "enable_production_mode"),
        "check_integration": ("production", "check_integration"),
        "fix_integration": ("production", "fix_integration"),
    }
    
    if name in import_map:
        module_name, attr_name = import_map[name]
        import importlib
        module = importlib.import_module(f".{module_name}", package=__name__)
        return getattr(module, attr_name)
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    # Display classes (main public API)
    "APIDisplay",
    # Infrastructure management
    "start_infrastructure", "stop_infrastructure",
    # Advanced API
    "register_endpoint", "get_all_endpoints",
    # Production mode
    "enable_production_mode", "check_integration", "fix_integration"
]