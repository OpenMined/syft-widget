"""Command line interface for syft-widget server"""
import argparse
import sys
from pathlib import Path


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="syft-widget CLI - Server and debugging tools")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Server command (original functionality)
    server_parser = subparsers.add_parser('server', help='Run syft-widget server')
    server_parser.add_argument("--package-name", required=True, help="Name of the package")
    server_parser.add_argument("--package-dir", default=".", help="Package directory")
    server_parser.add_argument("--auto-discover", action="store_true", help="Auto-discover endpoints")
    server_parser.add_argument("--port", type=int, default=8000, help="Server port")
    
    # Debug command
    debug_parser = subparsers.add_parser('debug', help='Debug syft-widget installation')
    debug_parser.add_argument('--detailed', '-d', action='store_true',
                             help='Show detailed debug information')
    
    # Dependencies command  
    deps_parser = subparsers.add_parser('deps', help='Check dependency status')
    
    # Diagnostic command
    diag_parser = subparsers.add_parser('diagnostic', help='Run full diagnostic')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show infrastructure status')
    
    args = parser.parse_args()
    
    if not args.command:
        # Default to showing help
        parser.print_help()
        return
    
    if args.command == 'server':
        run_server(args)
    elif args.command in ['debug', 'deps', 'diagnostic', 'status']:
        run_debug_command(args)


def run_server(args):
    """Run the server with given arguments"""
    print("Note: Legacy server CLI has been removed in v0.3.0")
    print("Use syft-serve directly for advanced server management:")
    print(f"  syft-serve create --name {args.package_name} --port {args.port}")
    print("\nOr use DynamicWidget for integrated server management in Jupyter")
    sys.exit(1)


def run_debug_command(args):
    """Run debug-related commands"""
    # Import debug utilities
    try:
        from .debug_utils import (
            print_debug_status, print_dependency_status, 
            print_full_diagnostic, debug_widget_status
        )
        from .widget_registry import get_infrastructure_status
    except ImportError as e:
        print(f"Error importing debug utilities: {e}")
        sys.exit(1)
    
    if args.command == 'debug':
        print_debug_status(detailed=args.detailed)
    
    elif args.command == 'deps':
        print_dependency_status()
    
    elif args.command == 'diagnostic':
        print_full_diagnostic()
    
    elif args.command == 'status':
        try:
            status = get_infrastructure_status()
            print("=== Infrastructure Status ===")
            print(f"Running: {status.get('running', 'unknown')}")
            print(f"Backend: {status.get('backend', 'unknown')}")
            if status.get('base_url'):
                print(f"Base URL: {status['base_url']}")
            if status.get('server_count'):
                print(f"Active servers: {status['server_count']}")
        except Exception as e:
            print(f"Error getting status: {e}")


if __name__ == "__main__":
    main()