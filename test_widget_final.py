#!/usr/bin/env python3
"""Final test of widget transitions"""

import time
import requests
from datetime import datetime


def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    symbol = {"INFO": "ℹ", "SUCCESS": "✓", "ERROR": "✗", "WAIT": "⏳"}.get(level, "•")
    print(f"[{timestamp}] {symbol} {message}")


def check_server(url):
    """Check if a server is responding"""
    try:
        resp = requests.get(f"{url}/health", timeout=0.5)
        return resp.status_code == 200
    except:
        return False


def check_syftbox_discovery():
    """Check SyftBox discovery service"""
    try:
        resp = requests.get("http://localhost:62050", timeout=0.5)
        if resp.status_code == 200:
            data = resp.json()
            port = data.get('main_server_port')
            if port:
                return f"http://localhost:{port}"
    except:
        pass
    return None


def test_endpoint(url, path):
    """Test an endpoint"""
    try:
        resp = requests.get(url + path, timeout=1)
        if resp.status_code == 200:
            return True, resp.json()
    except:
        pass
    return False, None


def simulate_widget_view():
    """Simulate what a widget would see"""
    log("=== Simulating Widget View ===", "INFO")
    
    # Track server states
    current_server = None
    last_data = {}
    
    log("Starting monitoring loop (simulating widget JavaScript)", "INFO")
    
    for i in range(30):  # Monitor for 30 seconds
        # Check for SyftBox first (priority)
        syftbox_url = check_syftbox_discovery()
        if syftbox_url and check_server(syftbox_url):
            if current_server != "syftbox":
                log(f"Switched to SyftBox server at {syftbox_url}", "SUCCESS")
                current_server = "syftbox"
            
            # Fetch data
            success, data = test_endpoint(syftbox_url, "/time/current")
            if success and data != last_data:
                log(f"SyftBox data: {data.get('formatted', 'N/A')}", "INFO")
                last_data = data
                
        # Fall back to thread server
        elif check_server("http://localhost:8001"):
            if current_server != "thread":
                log("Switched to Thread server at localhost:8001", "SUCCESS")
                current_server = "thread"
                
            # Fetch data
            success, data = test_endpoint("http://localhost:8001", "/time/current")
            if success and data != last_data:
                log(f"Thread data: {data.get('formatted', 'N/A')}", "INFO")
                last_data = data
                
        # No servers available
        else:
            if current_server != "checkpoint":
                log("No servers available, using checkpoint data", "ERROR")
                current_server = "checkpoint"
                
        time.sleep(1)
        
        # Status update every 5 seconds
        if i > 0 and i % 5 == 0:
            log(f"Current server: {current_server or 'none'}", "WAIT")
    
    return current_server == "syftbox"


def main():
    log("=== FINAL WIDGET TRANSITION TEST ===", "INFO")
    
    # Initial state check
    log("Checking initial state...", "INFO")
    thread_ok = check_server("http://localhost:8001")
    syftbox_url = check_syftbox_discovery()
    syftbox_ok = syftbox_url and check_server(syftbox_url)
    
    log(f"Thread server: {'✓ Running' if thread_ok else '✗ Not running'}", 
        "SUCCESS" if thread_ok else "ERROR")
    log(f"SyftBox: {'✓ Running at ' + syftbox_url if syftbox_ok else '✗ Not running'}", 
        "SUCCESS" if syftbox_ok else "ERROR")
    
    # Test endpoints if SyftBox is running
    if syftbox_ok:
        log("\nTesting SyftBox endpoints:", "INFO")
        endpoints_ok = True
        
        for endpoint in ["/time/current", "/system/cpu", "/network/status"]:
            success, data = test_endpoint(syftbox_url, endpoint)
            if success:
                log(f"{endpoint}: ✓ Working", "SUCCESS")
            else:
                log(f"{endpoint}: ✗ Failed", "ERROR")
                endpoints_ok = False
        
        if endpoints_ok:
            log("\nAll endpoints working!", "SUCCESS")
            
            # Simulate widget view
            log("\nSimulating widget behavior:", "INFO")
            widget_ok = simulate_widget_view()
            
            if widget_ok:
                log("\n✓✓✓ SUCCESS! Widgets can transition properly!", "SUCCESS")
                return True
            else:
                log("\n✗✗✗ Widget simulation failed", "ERROR")
                return False
    else:
        log("\n✗✗✗ SyftBox not running with endpoints", "ERROR")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)