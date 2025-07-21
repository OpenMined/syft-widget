"""Demo endpoints showcasing data sources for syft-widget"""

import time
import random
from .endpoints import register_endpoint


# Time API endpoints
@register_endpoint("/time/current")
def get_current_time():
    """Get current time with timestamp"""
    return {
        "timestamp": int(time.time()),
        "formatted": time.strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": time.tzname[0]
    }


@register_endpoint("/time/uptime")
def get_uptime():
    """Get system uptime (simulated)"""
    import os
    # Simulate uptime
    boot_time = time.time() - (random.randint(1, 30) * 86400)  # 1-30 days ago
    uptime_seconds = int(time.time() - boot_time)
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    
    return {
        "uptime_seconds": uptime_seconds,
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "formatted": f"{days}d {hours}h {minutes}m"
    }


# System API endpoints
@register_endpoint("/system/cpu")
def get_cpu_stats():
    """Get CPU statistics"""
    # Simulate CPU data
    usage = random.randint(10, 90)
    cores = 8  # Typical modern CPU
    
    return {
        "usage_percent": usage,
        "cores": cores,
        "load_average": [
            round(random.uniform(0.5, 3.0), 2),
            round(random.uniform(0.5, 3.0), 2),
            round(random.uniform(0.5, 3.0), 2)
        ],
        "temperature": random.randint(40, 80)
    }


@register_endpoint("/system/memory")
def get_memory_stats():
    """Get memory statistics"""
    total_gb = 16.0
    used_gb = round(random.uniform(4.0, 14.0), 1)
    free_gb = round(total_gb - used_gb, 1)
    
    return {
        "total_gb": total_gb,
        "used_gb": used_gb,
        "free_gb": free_gb,
        "percent": round((used_gb / total_gb) * 100, 1),
        "available_gb": round(free_gb * 0.8, 1)  # Some memory is reserved
    }


@register_endpoint("/system/disk")
def get_disk_stats():
    """Get disk statistics"""
    total_gb = 512.0
    used_gb = round(random.uniform(100.0, 400.0), 1)
    free_gb = round(total_gb - used_gb, 1)
    
    return {
        "total_gb": total_gb,
        "used_gb": used_gb,
        "free_gb": free_gb,
        "percent": round((used_gb / total_gb) * 100, 1)
    }


# Network API endpoints
@register_endpoint("/network/status")
def get_network_status():
    """Get network status"""
    return {
        "connected": True,
        "interface": "en0",
        "ip_address": f"192.168.1.{random.randint(100, 200)}",
        "download_mbps": round(random.uniform(50, 200), 1),
        "upload_mbps": round(random.uniform(10, 50), 1),
        "latency_ms": random.randint(5, 50)
    }