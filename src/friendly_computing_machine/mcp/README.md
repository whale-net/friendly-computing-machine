# MCP (Model Context Protocol) Setup

This directory contains the MCP (Model Context Protocol) implementation for the Friendly Computing Machine project.

## Overview

MCP is a protocol that allows AI assistants to securely connect to and interact with various tools and data sources. This setup provides the foundation for exposing the application's capabilities to AI assistants through standardized interfaces.

## Current Status

🚧 **Basic Setup Only** - This is currently a minimal configuration with no active tools enabled.

## Files

- `__init__.py` - Package initialization and documentation
- `server.py` - Base MCP server implementation (framework only)

## Configuration

The main MCP configuration is in the project root at `mcp.json`. This file contains:

- Empty active configuration (no servers enabled)
- Sample configurations in comments showing how various tools could be configured
- Examples for filesystem, git, database, and Slack integrations

## CLI Commands

Use the following commands to manage MCP configuration:

```bash
# Check MCP status and configuration
fcm mcp status

# Validate MCP configuration file
fcm mcp validate

# Initialize MCP configuration (placeholder)
fcm mcp init

# Start MCP server (not implemented yet)
fcm mcp serve
```

## Sample Configurations (Disabled)

The `mcp.json` file includes commented examples for:

- **Filesystem Server**: Provides secure file system access
- **Git Server**: Enables Git repository operations  
- **PostgreSQL Server**: Allows database queries and operations
- **Slack Server**: Custom integration with the application's Slack functionality

## Future Development

When ready to enable MCP tools:

1. Uncomment desired server configurations in `mcp.json`
2. Install required MCP server packages
3. Configure environment variables as needed
4. Use `fcm mcp validate` to check configuration
5. Start servers with `fcm mcp serve` (when implemented)

## Security Considerations

- MCP servers should only expose necessary functionality
- Use read-only access where possible
- Validate all inputs and limit access to sensitive resources
- Environment variables should be used for sensitive configuration