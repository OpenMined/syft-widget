import os
import subprocess
import threading
import time
import json
import requests
import shutil
from pathlib import Path
from typing import Optional, Callable


class SyftBoxManager:
    def __init__(
        self, 
        app_name: str = "syft-widget",
        repo_url: str = "https://github.com/OpenMined/syft-widget",
        discovery_port: int = 62050,
        check_interval: float = 1.0
    ):
        self.app_name = app_name
        self.repo_url = repo_url
        self.discovery_port = discovery_port
        self.check_interval = check_interval
        self.syftbox_path = None
        self.app_path = None
        self.syftbox_server_url = None
        self.is_syftbox_running = False
        self._check_thread = None
        self._checking = False
        self._clone_attempts = 0
        self._max_clone_attempts = 3
        self._repo_not_found = False
        
    def get_syftbox_path(self) -> Optional[Path]:
        """Get SyftBox path from syft_core client"""
        try:
            import syft_core as sc
            c = sc.Client.load()
            return c.sync_folder.parent
        except Exception as e:
            print(f"Could not load SyftBox path: {e}")
            return None
    
    def check_app_exists(self) -> bool:
        """Check if the app already exists in SyftBox/apps"""
        # print(f"Checking if app exists at {self.app_path}")
        # print(f"SyftBox path: {self.syftbox_path}")
        # print(f"App path: {self.app_path}")
        # print(f"App path exists: {self.app_path.exists()}")
        if not self.syftbox_path:
            return False
        return self.app_path.exists()
    
    def get_app_version(self) -> Optional[str]:
        """Get the version of the installed SyftBox app"""
        if not self.check_app_exists():
            return None
        
        try:
            # Try to read version from the app's __init__.py
            init_file = self.app_path / "syft_widget" / "__init__.py"
            if init_file.exists():
                with open(init_file, 'r') as f:
                    content = f.read()
                    # Look for __version__ = "x.x.x"
                    import re
                    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                    if match:
                        return match.group(1)
        except Exception as e:
            print(f"Error reading app version: {e}")
        
        return None
    
    def get_current_version(self) -> str:
        """Get the version of the current syft_widget package"""
        try:
            import syft_widget
            return syft_widget.__version__
        except Exception as e:
            print(f"Error getting current version: {e}")
            return "0.0.0"
    
    def remove_app(self) -> bool:
        """Remove the existing app directory"""
        if not self.app_path or not self.app_path.exists():
            return True
        
        try:
            print(f"Removing existing app at {self.app_path}...")
            shutil.rmtree(self.app_path)
            print("App removed successfully")
            return True
        except Exception as e:
            print(f"Error removing app: {e}")
            return False
    
    def clone_app(self) -> bool:
        """Clone the app repository to SyftBox/apps"""
        if not self.syftbox_path:
            print("SyftBox path not available")
            return False
            
        # Check if we've already determined the repo doesn't exist
        if self._repo_not_found:
            return False
            
        # Check if we've exceeded max attempts
        if self._clone_attempts >= self._max_clone_attempts:
            if not self._repo_not_found:
                print(f"\n⚠️  Max clone attempts ({self._max_clone_attempts}) reached for {self.repo_url}")
                print("   This may indicate:")
                print("   - The repository doesn't exist yet")
                print("   - The repository is private")
                print("   - Network connectivity issues")
                print("\n   To fix this, either:")
                print("   1. Create and push your repository to GitHub")
                print("   2. Check your network connection")
                print("   3. Restart the infrastructure after fixing the issue\n")
                self._repo_not_found = True
            return False
            
        apps_dir = self.syftbox_path / "apps"
        apps_dir.mkdir(exist_ok=True)
        
        try:
            self._clone_attempts += 1
            print(f"Cloning {self.repo_url} to {self.app_path}... (attempt {self._clone_attempts}/{self._max_clone_attempts})")
            result = subprocess.run(
                ["git", "clone", self.repo_url, str(self.app_path)],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"Successfully cloned {self.app_name}")
            self._clone_attempts = 0  # Reset on success
            return True
        except subprocess.CalledProcessError as e:
            error_output = e.stderr if hasattr(e, 'stderr') else str(e)
            
            # Check for specific error messages
            if "Repository not found" in error_output or "does not exist" in error_output:
                print(f"\n❌ Repository not found: {self.repo_url}")
                print("   Please ensure the repository exists and is public.")
                self._repo_not_found = True
            elif "Could not resolve host" in error_output:
                print(f"\n❌ Network error: Could not resolve github.com")
                print("   Please check your internet connection.")
            else:
                print(f"Failed to clone repository: {e}")
                
            return False
    
    def get_syftbox_server_url(self) -> Optional[str]:
        """Get the SyftBox app server URL from discovery service"""
        try:
            response = requests.get(f"http://localhost:{self.discovery_port}", timeout=0.5)
            if response.status_code == 200:
                data = response.json()
                port = data.get('main_server_port')
                if port:
                    return f"http://localhost:{port}"
        except:
            pass
        return None
    
    def check_syftbox_server(self) -> bool:
        """Check if SyftBox server is running"""
        if not self.syftbox_server_url:
            self.syftbox_server_url = self.get_syftbox_server_url()
            
        if self.syftbox_server_url:
            try:
                response = requests.get(f"{self.syftbox_server_url}/health", timeout=0.5)
                return response.status_code == 200
            except requests.exceptions.RequestException:
                # Connection failed, but don't clear the URL yet
                # It might be a temporary network issue
                pass
        return False
    
    def _monitor_syftbox(self, on_ready_callback: Optional[Callable] = None):
        """Monitor for SyftBox app to become available"""
        just_cloned = False
        import time as time_module
        while self._checking:
            loop_start = time_module.time()
            current_version = self.get_current_version()
            
            if self.check_app_exists():
                # App exists, check version
                app_version = self.get_app_version()
                
                if app_version and app_version != current_version:
                    print(f"App version ({app_version}) differs from current version ({current_version})")
                    print("Updating app to latest version...")
                    
                    # Remove old version and clone new one
                    if self.remove_app():
                        if self.clone_app():
                            print(f"App updated to version {current_version}")
                        else:
                            print("Failed to clone updated app")
                            continue
                    else:
                        print("Failed to remove old app version")
                        continue
                
                # Check if server is running
                if self.check_syftbox_server():
                    # Double-check version via API if possible
                    try:
                        version_response = requests.get(f"{self.syftbox_server_url}/version", timeout=0.5)
                        if version_response.status_code == 200:
                            server_version = version_response.json().get("version", "unknown")
                            if server_version != current_version:
                                print(f"Running server version ({server_version}) differs from current ({current_version})")
                                print("Server needs to be restarted with new version...")
                                # The server will be restarted by SyftBox when we update the app
                                continue
                    except:
                        # Version endpoint might not exist, continue anyway
                        pass
                    
                    self.is_syftbox_running = True
                    print(f"SyftBox app server is running at {self.syftbox_server_url} (version {current_version})")
                    if on_ready_callback:
                        on_ready_callback(self.syftbox_server_url)
                    break
            else:
                # App doesn't exist, clone it
                if not self._repo_not_found and self._clone_attempts < self._max_clone_attempts:
                    if self.clone_app():
                        print(f"App cloned (version {current_version}), waiting for SyftBox to start it...")
                        just_cloned = True
                    else:
                        if not self._repo_not_found:
                            print("Failed to clone app, will retry...")
                        time_module.sleep(2)  # Wait a bit before retrying
                    
            # Don't sleep - let the timeout be our rate limiter
            # The 0.5s timeout on HTTP requests provides natural pacing
            loop_time = time_module.time() - loop_start
            if loop_time > 1.0:
                print(f"[SyftBoxManager] Loop took {loop_time:.2f}s")
    
    def start_monitoring(self, on_ready_callback: Optional[Callable] = None):
        """Start monitoring for SyftBox app"""
        self.syftbox_path = self.get_syftbox_path()
        if not self.syftbox_path:
            print("Warning: Could not determine SyftBox path")
            return False
            
        self.app_path = self.syftbox_path / "apps" / self.app_name
        
        self._checking = True
        self._check_thread = threading.Thread(
            target=self._monitor_syftbox,
            args=(on_ready_callback,),
            daemon=True
        )
        self._check_thread.start()
        return True
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self._checking = False
        if self._check_thread:
            self._check_thread.join()