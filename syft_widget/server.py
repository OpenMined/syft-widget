from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import threading
import time


def create_server(endpoints=None):
    app = FastAPI()
    
    # Add CORS middleware to allow JavaScript access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify your Jupyter server origin
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/health")
    async def health():
        return {"status": "ok"}
    
    @app.get("/version")
    async def version():
        try:
            import syft_widget
            return {"version": syft_widget.__version__}
        except:
            return {"version": "unknown"}
    
    @app.get("/time")
    async def get_time():
        return {"timestamp": int(time.time()), "formatted": time.strftime("%Y-%m-%d %H:%M:%S")}
    
    @app.post("/action")
    async def perform_action(data: dict = {}):
        # Simulate some server-side action
        timestamp = data.get("timestamp", "No timestamp provided")
        return {"message": f"Action performed successfully at {timestamp}", "server_time": time.strftime("%Y-%m-%d %H:%M:%S")}
    
    @app.post("/shutdown")
    async def shutdown():
        """Endpoint to shutdown the server"""
        import os
        import signal
        # Schedule shutdown after response
        def stop_server():
            import os
            time.sleep(0.5)
            os.kill(os.getpid(), signal.SIGTERM)
        
        thread = threading.Thread(target=stop_server)
        thread.start()
        return {"message": "Server shutting down..."}
    
    @app.post("/kill-syftbox")
    async def kill_syftbox():
        """Endpoint to kill the SyftBox app (if we are the SyftBox app)"""
        import os
        import signal
        # If running as SyftBox app, kill the parent process
        def kill_app():
            time.sleep(0.5)
            # Kill the entire process group to ensure uvicorn and all workers die
            os.killpg(os.getpgid(os.getpid()), signal.SIGTERM)
        
        thread = threading.Thread(target=kill_app)
        thread.start()
        return {"message": "SyftBox app shutting down..."}
    
    # Add custom endpoints if provided
    if endpoints:
        for path, handler in endpoints.items():
            # Create an async wrapper for the sync handler
            async def endpoint_wrapper(handler=handler):
                return handler()
            
            # Register the endpoint
            app.add_api_route(path, endpoint_wrapper, methods=["GET"])
    
    return app


import multiprocessing
from .process_tracker import track_process, untrack_process, kill_processes_on_port

def _run_server_process(port: int, endpoints=None):
    """Top-level function for multiprocessing"""
    # Register signal handlers to clean up on exit
    import signal
    import sys
    import os
    
    def signal_handler(sig, frame):
        print(f"Server process {os.getpid()} received signal {sig}, exiting...")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    app = create_server(endpoints=endpoints)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")

def run_server_in_thread(port: int = 8000, delay: float = 0, endpoints=None):
    if delay > 0:
        time.sleep(delay)
    
    # First kill any existing processes on this port
    kill_processes_on_port(port)
    time.sleep(0.5)  # Give it time to clean up
    
    # Use a process instead of thread so we can actually kill it
    process = multiprocessing.Process(
        target=_run_server_process, 
        args=(port, endpoints),
        daemon=True
    )
    process.start()
    
    # Track the process
    track_process(process.pid)
    print(f"Started and tracking server process {process.pid} on port {port}")
    
    return process


# Make the app available at module level for uvicorn
app = create_server()