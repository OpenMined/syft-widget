#!/usr/bin/env python3
"""Test server discovery mechanism"""

import time
import requests
from datetime import datetime


def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {message}")


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


def check_data_endpoint(url, endpoint):
    """Check if data endpoint is working"""
    try:
        resp = requests.get(f"{url}{endpoint}", timeout=1)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return None


def main():
    log("=== Server Discovery Test ===")
    
    # Check thread server
    log("Checking thread server on port 8001...")
    thread_alive = check_server("http://localhost:8001")
    log(f"Thread server: {'✓ ALIVE' if thread_alive else '✗ DEAD'}")
    
    # Check SyftBox discovery
    log("\nChecking SyftBox discovery service...")
    syftbox_url = check_syftbox_discovery()
    if syftbox_url:
        log(f"✓ SyftBox discovered at: {syftbox_url}")
        
        # Check if SyftBox server is actually running
        syftbox_alive = check_server(syftbox_url)
        log(f"SyftBox server: {'✓ ALIVE' if syftbox_alive else '✗ DEAD'}")
        
        if syftbox_alive:
            # Test data endpoints
            log("\nTesting SyftBox endpoints:")
            
            time_data = check_data_endpoint(syftbox_url, "/time/current")
            if time_data:
                log(f"✓ /time/current: {time_data.get('formatted', 'N/A')}")
            else:
                log("✗ /time/current: Failed")
                
            cpu_data = check_data_endpoint(syftbox_url, "/system/cpu")
            if cpu_data:
                log(f"✓ /system/cpu: {cpu_data.get('usage_percent', 'N/A')}%")
            else:
                log("✗ /system/cpu: Failed")
    else:
        log("✗ No SyftBox discovered")
    
    # Monitor for changes
    log("\n=== Monitoring for 20 seconds ===")
    log("(Watching for server transitions...)")
    
    last_thread_state = thread_alive
    last_syftbox_url = syftbox_url
    
    for i in range(20):
        time.sleep(1)
        
        # Check thread server
        thread_alive = check_server("http://localhost:8001")
        if thread_alive != last_thread_state:
            log(f"Thread server: {'✓ STARTED' if thread_alive else '✗ STOPPED'}")
            last_thread_state = thread_alive
        
        # Check SyftBox
        current_syftbox_url = check_syftbox_discovery()
        if current_syftbox_url != last_syftbox_url:
            if current_syftbox_url:
                log(f"SyftBox: ✓ DISCOVERED at {current_syftbox_url}")
            else:
                log("SyftBox: ✗ LOST")
            last_syftbox_url = current_syftbox_url
            
        # Show status every 5 seconds
        if i > 0 and i % 5 == 0:
            status = []
            if thread_alive:
                status.append("Thread:✓")
            if current_syftbox_url and check_server(current_syftbox_url):
                status.append(f"SyftBox:✓")
            log(f"Status check: {' | '.join(status) if status else '✗ No servers'}")


if __name__ == "__main__":
    main()