"""Process tracking for cleanup of orphaned servers"""
import os
import json
import subprocess
import atexit
from pathlib import Path
from typing import Set

TRACKER_FILE = Path.home() / ".syftwidget" / "active_processes.json"

def load_tracked_processes() -> Set[int]:
    """Load tracked process PIDs from file"""
    if TRACKER_FILE.exists():
        try:
            with open(TRACKER_FILE, 'r') as f:
                return set(json.load(f))
        except:
            pass
    return set()

def save_tracked_processes(pids: Set[int]):
    """Save tracked process PIDs to file"""
    TRACKER_FILE.parent.mkdir(exist_ok=True)
    with open(TRACKER_FILE, 'w') as f:
        json.dump(list(pids), f)

def track_process(pid: int):
    """Add a process to tracking"""
    pids = load_tracked_processes()
    pids.add(pid)
    save_tracked_processes(pids)
    print(f"Tracking process {pid}")

def untrack_process(pid: int):
    """Remove a process from tracking"""
    pids = load_tracked_processes()
    pids.discard(pid)
    save_tracked_processes(pids)

def is_process_running(pid: int) -> bool:
    """Check if a process is still running"""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def kill_tracked_process(pid: int):
    """Kill a tracked process"""
    try:
        if is_process_running(pid):
            print(f"Killing tracked process {pid}")
            os.kill(pid, 9)
            return True
    except:
        pass
    return False

def cleanup_orphaned_processes():
    """Clean up any orphaned processes from previous runs"""
    pids = load_tracked_processes()
    alive_pids = set()
    
    for pid in pids:
        if is_process_running(pid):
            # Check if it's actually our process by looking at the command
            try:
                result = subprocess.run(['ps', '-p', str(pid), '-o', 'command='], 
                                      capture_output=True, text=True)
                if result.stdout and 'syft_widget' in result.stdout:
                    print(f"Found orphaned syft_widget process {pid}, killing it")
                    kill_tracked_process(pid)
                else:
                    alive_pids.add(pid)
            except:
                alive_pids.add(pid)
        else:
            # Process is dead, remove from tracking
            print(f"Process {pid} is no longer running, removing from tracking")
    
    save_tracked_processes(alive_pids)

def kill_processes_on_port(port: int):
    """Kill all processes on a specific port and untrack them"""
    try:
        result = subprocess.run(['lsof', '-t', f'-i:{port}'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            tracked_pids = load_tracked_processes()
            
            for pid in pids:
                pid_int = int(pid)
                print(f"Killing process {pid_int} on port {port}")
                subprocess.run(['kill', '-9', pid])
                tracked_pids.discard(pid_int)
            
            save_tracked_processes(tracked_pids)
    except Exception as e:
        print(f"Error killing processes on port {port}: {e}")

# Clean up orphaned processes on import
cleanup_orphaned_processes()

# Register cleanup on exit
atexit.register(cleanup_orphaned_processes)