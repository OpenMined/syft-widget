"""Process management utilities for syft-widget"""
import subprocess
import platform


def kill_processes_on_port(port: int):
    """Kill any processes running on the specified port"""
    try:
        if platform.system() == "Darwin":  # macOS
            # Find processes using the port
            result = subprocess.run(
                ["lsof", "-ti", f"tcp:{port}"],
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    try:
                        subprocess.run(["kill", "-9", pid], check=True)
                        print(f"Killed process {pid} on port {port}")
                    except subprocess.CalledProcessError:
                        pass
        elif platform.system() == "Linux":
            # Use fuser on Linux
            try:
                subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True)
                print(f"Killed processes on port {port}")
            except:
                pass
        else:
            print(f"Platform {platform.system()} not supported for port killing")
    except Exception as e:
        print(f"Error killing processes on port {port}: {e}")