#!/usr/bin/env python3
import requests
import time

print("Testing syft-widget server...")

# Test main server
try:
    response = requests.get("http://localhost:8006/health")
    print(f"✓ Main server health check: {response.status_code}")
    
    response = requests.get("http://localhost:8006/time")
    print(f"✓ Time endpoint: {response.json()}")
except Exception as e:
    print(f"✗ Main server error: {e}")

# Test discovery server
try:
    response = requests.get("http://localhost:62050")
    print(f"✓ Discovery server: {response.json()}")
except Exception as e:
    print(f"✗ Discovery server error: {e}")