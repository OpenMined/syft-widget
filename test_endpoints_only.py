#!/usr/bin/env python3
"""Test just the endpoints without widget imports"""

import time
import requests
import subprocess
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


def test_endpoint(url, path):
    """Test an endpoint"""
    try:
        resp = requests.get(url + path, timeout=1)
        if resp.status_code == 200:
            return True, resp.json()
    except Exception as e:
        return False, str(e)
    return False, None


def main():
    log("=== Endpoint Test ===")
    
    # Check if thread server is running
    thread_ok = check_server("http://localhost:8001")
    log(f"Thread server on 8001: {'✓ RUNNING' if thread_ok else '✗ NOT RUNNING'}")
    
    # Check for SyftBox
    syftbox_url = check_syftbox_discovery()
    if syftbox_url:
        log(f"SyftBox discovered at: {syftbox_url}")
        
        # Check if it's alive
        syftbox_ok = check_server(syftbox_url)
        log(f"SyftBox server: {'✓ ALIVE' if syftbox_ok else '✗ DEAD'}")
        
        if syftbox_ok:
            # List all the endpoints we expect
            endpoints = [
                "/health",
                "/version", 
                "/time",  # Old endpoint
                "/time/current",  # New endpoint
                "/time/uptime",
                "/system/cpu",
                "/system/memory",
                "/system/disk",
                "/network/status"
            ]
            
            log("\nTesting all endpoints:")
            for endpoint in endpoints:
                success, data = test_endpoint(syftbox_url, endpoint)
                if success:
                    # Show first 100 chars of response
                    data_str = str(data)[:100] + "..." if len(str(data)) > 100 else str(data)
                    log(f"✓ {endpoint}: {data_str}")
                else:
                    log(f"✗ {endpoint}: {data}")
    else:
        log("No SyftBox discovered")
        
    # Also test thread server if running
    if thread_ok:
        log("\nTesting thread server endpoints:")
        test_endpoints = ["/time/current", "/system/cpu"]
        for endpoint in test_endpoints:
            success, data = test_endpoint("http://localhost:8001", endpoint)
            if success:
                data_str = str(data)[:100] + "..." if len(str(data)) > 100 else str(data)
                log(f"✓ {endpoint}: {data_str}")
            else:
                log(f"✗ {endpoint}: Failed")


if __name__ == "__main__":
    main()