"""syft-widget - Create Jupyter widgets with automatic server management via syft-serve"""

__version__ = "0.3.1"

# Import DynamicWidget directly for the public API
from .dynamic_widget import DynamicWidget

# That's it! Just one clean public API
__all__ = ["DynamicWidget"]