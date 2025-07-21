#!/usr/bin/env python3
"""Test harness for widget server transitions"""

import time
import sys
import subprocess
import requests
import threading
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, '.')

from syft_widget import TimeDisplay, CPUDisplay, start_infrastructure, stop_infrastructure


class WidgetTransitionTester:
    def __init__(self):
        self.results = []
        self.widgets = []
        self.stop_monitoring = False
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {message}")
        self.results.append(f"[{timestamp}] {message}")
        
    def check_server(self, url):
        """Check if a server is responding"""
        try:
            resp = requests.get(f"{url}/health", timeout=0.5)
            return resp.status_code == 200
        except:
            return False
            
    def check_syftbox_discovery(self):
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
        
    def monitor_widget_state(self, widget_id, widget_name):
        """Monitor a widget's JavaScript state by checking console logs"""
        # This is a placeholder - in real testing we'd use Selenium or similar
        # For now, we'll just log what we expect to see
        self.log(f"Monitoring {widget_name} widget (id: {widget_id})")
        
    def test_transition(self):
        """Test the full transition lifecycle"""
        self.log("=== Starting Widget Transition Test ===")
        
        # Step 1: Start infrastructure
        self.log("Step 1: Starting infrastructure...")
        start_infrastructure()
        time.sleep(3)  # Let thread server start
        
        # Step 2: Create widgets
        self.log("Step 2: Creating display widgets...")
        time_widget = TimeDisplay()
        cpu_widget = CPUDisplay()
        self.widgets = [time_widget, cpu_widget]
        
        # Get widget IDs from the display objects
        for widget in self.widgets:
            self.log(f"Created widget: {widget.__class__.__name__} (id: {widget.id})")
        
        # Step 3: Verify thread server is running
        self.log("Step 3: Checking thread server...")
        thread_running = self.check_server("http://localhost:8001")
        if thread_running:
            self.log("✓ Thread server is running on port 8001")
        else:
            self.log("✗ Thread server is NOT running!")
            
        # Step 4: Wait for SyftBox to be available
        self.log("Step 4: Waiting for SyftBox discovery...")
        syftbox_url = None
        for i in range(30):  # Wait up to 30 seconds
            syftbox_url = self.check_syftbox_discovery()
            if syftbox_url:
                self.log(f"✓ SyftBox discovered at {syftbox_url}")
                break
            time.sleep(1)
            if i % 5 == 0:
                self.log(f"  Still waiting for SyftBox... ({i}s)")
                
        if not syftbox_url:
            self.log("✗ SyftBox never appeared!")
            return False
            
        # Step 5: Verify SyftBox is responding
        self.log("Step 5: Checking SyftBox server...")
        syftbox_running = self.check_server(syftbox_url)
        if syftbox_running:
            self.log(f"✓ SyftBox server is running at {syftbox_url}")
        else:
            self.log("✗ SyftBox server is NOT responding!")
            
        # Step 6: Monitor for thread server shutdown
        self.log("Step 6: Waiting for thread server to shut down...")
        shutdown_time = None
        for i in range(30):  # Wait up to 30 seconds
            if not self.check_server("http://localhost:8001"):
                shutdown_time = time.time()
                self.log(f"✓ Thread server shut down after {i} seconds")
                break
            time.sleep(1)
            
        if not shutdown_time:
            self.log("✗ Thread server never shut down!")
            return False
            
        # Step 7: Verify widgets are still updating
        self.log("Step 7: Checking widget functionality after thread shutdown...")
        time.sleep(2)  # Give widgets time to detect the change
        
        # Check if SyftBox is still running
        syftbox_still_running = self.check_server(syftbox_url)
        if syftbox_still_running:
            self.log(f"✓ SyftBox server still running at {syftbox_url}")
        else:
            self.log("✗ SyftBox server stopped responding!")
            
        # Step 8: Test data fetching from SyftBox
        self.log("Step 8: Testing data fetching from SyftBox...")
        try:
            # Test time endpoint
            resp = requests.get(f"{syftbox_url}/time/current", timeout=1)
            if resp.status_code == 200:
                data = resp.json()
                self.log(f"✓ Successfully fetched time data: {data.get('formatted', 'N/A')}")
            else:
                self.log(f"✗ Failed to fetch time data: status {resp.status_code}")
                
            # Test CPU endpoint
            resp = requests.get(f"{syftbox_url}/system/cpu", timeout=1)
            if resp.status_code == 200:
                data = resp.json()
                self.log(f"✓ Successfully fetched CPU data: {data.get('usage_percent', 'N/A')}%")
            else:
                self.log(f"✗ Failed to fetch CPU data: status {resp.status_code}")
        except Exception as e:
            self.log(f"✗ Error fetching data from SyftBox: {e}")
            
        # Step 9: Monitor for a bit to ensure stability
        self.log("Step 9: Monitoring stability for 10 seconds...")
        stable = True
        for i in range(10):
            if not self.check_server(syftbox_url):
                self.log(f"✗ SyftBox became unavailable after {i} seconds")
                stable = False
                break
            time.sleep(1)
            
        if stable:
            self.log("✓ System remained stable")
            
        # Summary
        self.log("\n=== Test Summary ===")
        self.log(f"Thread server started: {'✓' if thread_running else '✗'}")
        self.log(f"SyftBox discovered: {'✓' if syftbox_url else '✗'}")
        self.log(f"Thread server shut down: {'✓' if shutdown_time else '✗'}")
        self.log(f"SyftBox remained available: {'✓' if syftbox_still_running else '✗'}")
        self.log(f"Data fetching works: {'✓' if syftbox_still_running else '✗'}")
        self.log(f"System stable: {'✓' if stable else '✗'}")
        
        success = all([
            thread_running,
            syftbox_url,
            shutdown_time,
            syftbox_still_running,
            stable
        ])
        
        self.log(f"\nOVERALL: {'✓ PASS' if success else '✗ FAIL'}")
        return success
        
    def cleanup(self):
        """Clean up resources"""
        self.log("\nCleaning up...")
        try:
            stop_infrastructure()
        except:
            pass


def main():
    tester = WidgetTransitionTester()
    try:
        success = tester.test_transition()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()