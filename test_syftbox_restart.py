#!/usr/bin/env python3
"""Monitor SyftBox restart with new endpoints"""

import time
import requests
from datetime import datetime


def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {message}")


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


def check_endpoint(url, path):
    """Check if endpoint works"""
    try:
        resp = requests.get(url + path, timeout=1)
        return resp.status_code == 200, resp.json() if resp.status_code == 200 else None
    except:
        return False, None


def main():
    log("=== Monitoring for SyftBox restart ===")
    
    last_url = None
    endpoints_working = False
    
    for i in range(60):  # Monitor for up to 60 seconds
        syftbox_url = check_syftbox_discovery()
        
        if syftbox_url and syftbox_url != last_url:
            log(f"✓ SyftBox discovered at {syftbox_url}")
            last_url = syftbox_url
            
            # Test endpoints
            time.sleep(1)  # Give server a moment to fully start
            log("Testing endpoints...")
            
            success, data = check_endpoint(syftbox_url, "/time/current")
            if success:
                log(f"✓ /time/current: {data.get('formatted', 'N/A')}")
                endpoints_working = True
            else:
                log("✗ /time/current: Failed")
                
            success, data = check_endpoint(syftbox_url, "/system/cpu")
            if success:
                log(f"✓ /system/cpu: {data.get('usage_percent', 'N/A')}%")
            else:
                log("✗ /system/cpu: Failed")
                
            if endpoints_working:
                log("\n✓✓✓ SUCCESS! SyftBox app is serving the correct endpoints!")
                return True
        elif not syftbox_url and last_url:
            log("SyftBox disappeared")
            last_url = None
            
        if i % 5 == 0:
            log(f"Waiting... ({i}s)")
            
        time.sleep(1)
    
    log("\n✗✗✗ TIMEOUT: SyftBox did not come back with correct endpoints")
    return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)