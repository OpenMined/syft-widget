# Changelog

All notable changes to syft-widget will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2024-12-XX

### Added

#### Major Features
- **Automatic Server Management**: Every widget automatically spawns its own server process using syft-serve
- **Simplified Architecture**: Single backend system using syft-serve for all server operations
- **Enhanced DynamicWidget**: New server management methods and dependency isolation capabilities
- **Improved APIDisplay**: Updated with backend abstraction and server management features
- **Debug Utilities**: Comprehensive debugging and diagnostic tools (`debug_widget_status`, `print_full_diagnostic`, etc.)
- **Enhanced CLI**: New command-line interface with debug commands (`syft-widget debug`, `syft-widget deps`, etc.)

#### New Parameters
- `server_name`: Named servers for deduplication and management
- `dependencies`: Isolated Python package dependencies per server  
- `force_new_server`: Force creation of new server instances
- `use_syft_serve`: Toggle between syft-serve and legacy backends
- `verbose`: Enhanced logging and status messages

#### New Methods
- `widget.restart_server()`: Restart widget's server
- `widget.stop_server()`: Stop widget's server  
- `widget.get_server_logs()`: Get server logs (syft-serve backend only)
- `widget.get_debug_info()`: Get comprehensive debug information
- `get_infrastructure_status()`: Get global infrastructure status

#### New CLI Commands
- `syft-widget debug`: Debug installation and status
- `syft-widget deps`: Check dependency status
- `syft-widget diagnostic`: Run full system diagnostic
- `syft-widget status`: Show infrastructure status
- `syft-widget server`: Run server (updated with subcommands)

#### Package Features
- **Required Dependencies**: syft-serve and psutil are now required for automatic server management
- **Console Script**: Install creates `syft-widget` command-line tool
- **Automatic Process Spawning**: Widgets automatically create server processes as needed

### Changed

#### Architecture
- **Server Management**: Simplified to single backend using syft-serve for all operations
- **Automatic Process Spawning**: Every widget automatically creates its own server process
- **Legacy Removal**: Removed legacy server management code for cleaner architecture
- **Import Structure**: Added new public APIs while maintaining existing imports
- **Dependency Handling**: Made syft-serve and psutil required dependencies for reliable server management

#### Performance
- **Server Deduplication**: Multiple widgets can share servers when using same configuration
- **Startup Time**: Improved startup performance with automatic server process spawning
- **Resource Usage**: Better resource management with proper server lifecycle handling

### Fixed

#### Stability
- **Process Management**: Improved process cleanup and error handling
- **Cross-Platform**: Better compatibility across different operating systems  
- **Memory Leaks**: Fixed potential memory leaks in server management
- **Error Handling**: More robust error handling and recovery

#### Compatibility
- **Python Versions**: Enhanced compatibility across Python 3.9+
- **Jupyter Environments**: Better handling of different Jupyter setups
- **Network Issues**: Improved handling of network connectivity problems

### Removed

- **Legacy Modules**: Removed legacy server management code and checkpoint fallback system
- **Endpoint Registration**: Removed `register_endpoint()` and `get_all_endpoints()` functions (use DynamicWidget.endpoint decorator)
- **CLI Server**: Removed `syft-widget server` command (use syft-serve directly or DynamicWidget)
- **Optional Backend Selection**: Removed backend selection logic (syft-serve is now always used)

### Security

- **Process Isolation**: Better process isolation with syft-serve backend
- **Dependency Isolation**: Isolated dependency environments prevent conflicts
- **Permission Handling**: Improved permission handling for server operations

## [0.2.0] - Previous Release

### Added
- Basic widget infrastructure
- Multi-server support
- Production mode integration
- SyftBox compatibility

### Changed
- Widget architecture improvements
- Enhanced server discovery

### Fixed
- Various stability improvements
- Cross-platform compatibility fixes

## [0.1.0] - Initial Release

### Added
- Basic DynamicWidget functionality
- APIDisplay base class
- Server infrastructure
- Jupyter integration