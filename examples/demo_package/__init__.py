"""Demo package showing how to use syft-widget"""

from .widgets import TimeDisplay, CPUDisplay, SystemDashboard, NetworkMonitor
from .endpoints import get_time, get_cpu, get_memory, get_disk, get_network

__all__ = [
    "TimeDisplay", "CPUDisplay", "SystemDashboard", "NetworkMonitor",
    "get_time", "get_cpu", "get_memory", "get_disk", "get_network"
]