"""
MCP (Model Context Protocol) CLI commands.

Provides command-line interface for MCP server management and configuration.
"""

import logging
from pathlib import Path
from typing import Annotated

import typer

from friendly_computing_machine.mcp.server import MCPServer, load_mcp_config

logger = logging.getLogger(__name__)
app = typer.Typer(help="MCP (Model Context Protocol) commands")


@app.command()
def status():
    """
    Show MCP server status and configuration.
    """
    typer.echo("MCP Server Status")
    typer.echo("=================")
    
    # Load and display configuration
    config = load_mcp_config()
    if not config:
        typer.echo("❌ No MCP configuration found")
        typer.echo("\nTo get started, see the sample configuration in mcp.json")
        return
    
    mcp_servers = config.get("mcpServers", {})
    
    # Filter out comment keys
    active_servers = {k: v for k, v in mcp_servers.items() if not k.startswith("_")}
    
    if not active_servers:
        typer.echo("✅ MCP configuration found but no servers configured")
        typer.echo("\nSample configurations are available in mcp.json as comments")
    else:
        typer.echo(f"✅ Found {len(active_servers)} configured MCP server(s)")
        for name, config in active_servers.items():
            typer.echo(f"  - {name}: {config.get('description', 'No description')}")
    
    typer.echo("\n💡 Use 'fcm mcp validate' to check configuration validity")


@app.command()
def validate():
    """
    Validate MCP configuration file.
    """
    typer.echo("Validating MCP Configuration")
    typer.echo("============================")
    
    config = load_mcp_config()
    if not config:
        typer.echo("❌ No MCP configuration found")
        raise typer.Exit(1)
    
    mcp_servers = config.get("mcpServers", {})
    active_servers = {k: v for k, v in mcp_servers.items() if not k.startswith("_")}
    
    if not active_servers:
        typer.echo("✅ Configuration file is valid (no active servers)")
        return
    
    # Basic validation of server configurations
    errors = []
    for name, server_config in active_servers.items():
        if not isinstance(server_config, dict):
            errors.append(f"Server '{name}' configuration must be an object")
            continue
            
        # Check required fields
        if "command" not in server_config:
            errors.append(f"Server '{name}' missing required 'command' field")
        
        if "args" in server_config and not isinstance(server_config["args"], list):
            errors.append(f"Server '{name}' 'args' field must be a list")
    
    if errors:
        typer.echo("❌ Configuration validation failed:")
        for error in errors:
            typer.echo(f"  - {error}")
        raise typer.Exit(1)
    else:
        typer.echo(f"✅ Configuration is valid ({len(active_servers)} server(s) configured)")


@app.command()
def init():
    """
    Initialize MCP configuration file if it doesn't exist.
    """
    config_path = Path("mcp.json")
    
    if config_path.exists():
        typer.echo("❌ MCP configuration file already exists")
        typer.echo("Use 'fcm mcp status' to view current configuration")
        return
    
    # This would copy the default configuration
    typer.echo("❌ MCP configuration initialization not implemented yet")
    typer.echo("Please manually copy mcp.json to your project root")
    typer.echo("\nThe configuration file contains sample configurations as comments")


@app.command()
def serve(
    config_path: Annotated[Path, typer.Option(help="Path to MCP configuration file")] = Path("mcp.json"),
    server_name: Annotated[str, typer.Option(help="Name of specific server to run")] = None,
):
    """
    Start MCP server (not implemented - placeholder for future functionality).
    """
    typer.echo("MCP Server")
    typer.echo("==========")
    typer.echo("❌ MCP server execution not implemented yet")
    typer.echo("\nThis command would start the MCP server with the specified configuration.")
    typer.echo("Currently, only configuration management is available.")
    
    if server_name:
        typer.echo(f"\nTarget server: {server_name}")
    
    typer.echo(f"\nConfiguration file: {config_path}")


if __name__ == "__main__":
    app()