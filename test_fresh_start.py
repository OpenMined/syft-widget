#!/usr/bin/env python3
"""Test fresh infrastructure start"""

import time
import sys
import requests
import subprocess
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, '.')

from syft_widget.widget_registry import start_infrastructure, stop_infrastructure
from syft_widget.display_objects import TimeDisplay, CPUDisplay


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
    except:
        pass
    return False, None


def kill_all_servers():
    """Kill all known servers"""
    log("Killing any existing servers...")
    
    # Kill thread servers
    for port in [8000, 8001, 8002]:
        subprocess.run(f"lsof -ti:{port} | xargs kill -9 2>/dev/null || true", shell=True)
    
    # Kill discovery service
    subprocess.run("lsof -ti:62050 | xargs kill -9 2>/dev/null || true", shell=True)
    
    # Kill any SyftBox app on various ports
    for port in range(53000, 58000, 100):
        subprocess.run(f"lsof -ti:{port} | xargs kill -9 2>/dev/null || true", shell=True)
    
    time.sleep(2)
    log("Cleanup complete")


def main():
    log("=== Fresh Infrastructure Test ===")
    
    # Clean start
    kill_all_servers()
    
    # Start fresh infrastructure
    log("\nStarting fresh infrastructure...")
    start_infrastructure()
    
    # Give it time to start
    log("Waiting for infrastructure to start...")
    time.sleep(5)
    
    # Check thread server
    thread_ok = check_server("http://localhost:8001")
    log(f"Thread server: {'✓ RUNNING' if thread_ok else '✗ NOT RUNNING'}")
    
    if thread_ok:
        # Test thread server endpoints
        log("\nTesting thread server endpoints:")
        success, data = test_endpoint("http://localhost:8001", "/time/current")
        if success:
            log(f"✓ /time/current: {data.get('formatted', 'N/A')}")
        else:
            log("✗ /time/current: Failed")
            
        success, data = test_endpoint("http://localhost:8001", "/system/cpu")
        if success:
            log(f"✓ /system/cpu: {data.get('usage_percent', 'N/A')}%")
        else:
            log("✗ /system/cpu: Failed")
    
    # Monitor for SyftBox
    log("\nMonitoring for SyftBox app...")
    syftbox_found = False
    
    for i in range(30):
        syftbox_url = check_syftbox_discovery()
        if syftbox_url:
            log(f"\n✓ SyftBox discovered at {syftbox_url}")
            
            # Test endpoints
            time.sleep(2)
            log("Testing SyftBox endpoints:")
            
            success, data = test_endpoint(syftbox_url, "/time/current")
            if success:
                log(f"✓ /time/current: {data.get('formatted', 'N/A')}")
                syftbox_found = True
            else:
                log("✗ /time/current: Failed")
                
            success, data = test_endpoint(syftbox_url, "/system/cpu")
            if success:
                log(f"✓ /system/cpu: {data.get('usage_percent', 'N/A')}%")
            else:
                log("✗ /system/cpu: Failed")
                
            if syftbox_found:
                log("\n✓✓✓ SUCCESS! SyftBox is serving correct endpoints!")
                
                # Wait for thread server to shut down
                log("\nWaiting for thread server to shut down...")
                for j in range(20):
                    if not check_server("http://localhost:8001"):
                        log("✓ Thread server shut down")
                        break
                    time.sleep(1)
                
                return True
            break
            
        if i % 5 == 0 and i > 0:
            log(f"Still waiting for SyftBox... ({i}s)")
        time.sleep(1)
    
    log("\n✗✗✗ FAILED: SyftBox did not start with correct endpoints")
    return False


if __name__ == "__main__":
    try:
        success = main()
    finally:
        log("\nCleaning up...")
        try:
            stop_infrastructure()
        except:
            pass
    
    sys.exit(0 if success else 1)