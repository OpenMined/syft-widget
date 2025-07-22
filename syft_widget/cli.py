"""Command line interface for syft-widget server"""
import argparse
import sys
from pathlib import Path


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="syft-widget server")
    parser.add_argument("--package-name", required=True, help="Name of the package")
    parser.add_argument("--package-dir", default=".", help="Package directory")
    parser.add_argument("--auto-discover", action="store_true", help="Auto-discover endpoints")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    
    args = parser.parse_args()
    
    # Change to package directory
    package_dir = Path(args.package_dir).resolve()
    sys.path.insert(0, str(package_dir))
    
    # Import and run server
    from .server import create_server
    import uvicorn
    
    # Auto-discover endpoints if requested
    endpoints = {}
    if args.auto_discover:
        try:
            # Try to import the package and get its endpoints
            import importlib
            package = importlib.import_module(args.package_name.replace("-", "_"))
            
            # Look for endpoints in the package
            from .endpoints import get_all_endpoints
            endpoints = get_all_endpoints()
            print(f"Discovered {len(endpoints)} endpoints from {args.package_name}")
        except Exception as e:
            print(f"Warning: Could not auto-discover endpoints: {e}")
    
    # Create and run server
    app = create_server(endpoints=endpoints)
    print(f"Starting server for {args.package_name} on port {args.port}")
    uvicorn.run(app, host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()