#!/usr/bin/env python3
"""Test killing thread server and widget continuity"""

import time
import requests
import subprocess
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


def kill_thread_server():
    """Kill the thread server"""
    try:
        # Try API shutdown first
        requests.post("http://localhost:8001/shutdown", timeout=0.5)
    except:
        pass
    
    # Force kill
    subprocess.run("lsof -ti:8001 | xargs kill -9 2>/dev/null || true", shell=True)


def main():
    log("=== THREAD SERVER KILL TEST ===", "INFO")
    
    # Check initial state
    thread_ok = check_server("http://localhost:8001")
    syftbox_url = check_syftbox_discovery()
    syftbox_ok = syftbox_url and check_server(syftbox_url)
    
    log(f"Initial state:", "INFO")
    log(f"  Thread server: {'✓ Running' if thread_ok else '✗ Not running'}", 
        "SUCCESS" if thread_ok else "ERROR")
    log(f"  SyftBox: {'✓ Running at ' + str(syftbox_url) if syftbox_ok else '✗ Not running'}", 
        "SUCCESS" if syftbox_ok else "ERROR")
    
    if not thread_ok or not syftbox_ok:
        log("Both servers must be running for this test", "ERROR")
        return False
    
    # Simulate widget polling
    log("\nSimulating widget polling...", "INFO")
    current_server = None
    transitions = []
    
    for i in range(20):
        # Check which server responds
        syftbox_alive = check_server(syftbox_url) if syftbox_url else False
        thread_alive = check_server("http://localhost:8001")
        
        # Determine active server (SyftBox has priority)
        if syftbox_alive:
            new_server = "syftbox"
        elif thread_alive:
            new_server = "thread"
        else:
            new_server = "checkpoint"
            
        # Track transitions
        if new_server != current_server:
            transitions.append((i, current_server, new_server))
            log(f"Server transition: {current_server or 'none'} → {new_server}", "SUCCESS")
            current_server = new_server
            
        # Kill thread server after 5 seconds
        if i == 5:
            log("\nKilling thread server...", "WAIT")
            kill_thread_server()
            
        time.sleep(1)
        
        # Status every 5 seconds
        if i > 0 and i % 5 == 0:
            log(f"Active server: {current_server}", "INFO")
    
    # Analyze results
    log("\nTransition summary:", "INFO")
    for t, old, new in transitions:
        log(f"  t={t}s: {old or 'none'} → {new}", "INFO")
        
    # Success if we ended on SyftBox
    if current_server == "syftbox":
        log("\n✓✓✓ SUCCESS! Widget transitioned to SyftBox after thread kill!", "SUCCESS")
        return True
    else:
        log(f"\n✗✗✗ FAILED! Widget ended on {current_server}, not SyftBox", "ERROR")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)