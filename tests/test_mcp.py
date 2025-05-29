"""
Tests for MCP (Model Context Protocol) functionality.
"""

import json
import pytest
from pathlib import Path
from friendly_computing_machine.mcp.server import MCPServer, load_mcp_config


class TestMCPServer:
    """Test MCP server basic functionality."""
    
    def test_mcp_server_creation(self):
        """Test that MCP server can be created."""
        server = MCPServer("test-server", "1.0.0")
        assert server.name == "test-server"
        assert server.version == "1.0.0"
        assert server.tools == {}
        assert server.resources == {}
    
    def test_add_tool(self):
        """Test adding tools to MCP server."""
        server = MCPServer("test-server")
        tool_config = {"name": "test_tool", "description": "A test tool"}
        server.add_tool("test_tool", tool_config)
        assert "test_tool" in server.tools
        assert server.tools["test_tool"] == tool_config
    
    def test_add_resource(self):
        """Test adding resources to MCP server."""
        server = MCPServer("test-server")
        resource_config = {"name": "test_resource", "type": "database"}
        server.add_resource("test_resource", resource_config)
        assert "test_resource" in server.resources
        assert server.resources["test_resource"] == resource_config


class TestMCPConfig:
    """Test MCP configuration loading."""
    
    def test_load_mcp_config_missing_file(self, tmp_path):
        """Test loading config when file doesn't exist."""
        config_path = tmp_path / "missing.json"
        config = load_mcp_config(config_path)
        assert config == {}
    
    def test_load_mcp_config_valid_file(self, tmp_path):
        """Test loading valid config file."""
        config_path = tmp_path / "test_mcp.json"
        test_config = {
            "mcpServers": {
                "test_server": {
                    "command": "echo",
                    "args": ["hello"]
                }
            }
        }
        config_path.write_text(json.dumps(test_config))
        
        config = load_mcp_config(config_path)
        assert config == test_config
    
    def test_load_mcp_config_invalid_json(self, tmp_path):
        """Test loading invalid JSON file."""
        config_path = tmp_path / "invalid.json"
        config_path.write_text("invalid json content")
        
        config = load_mcp_config(config_path)
        assert config == {}


class TestMCPIntegration:
    """Test MCP integration with the project."""
    
    def test_mcp_config_exists(self):
        """Test that the main MCP config file exists."""
        # Look for mcp.json in the project root (tests/ is one level down from project root)
        config_path = Path(__file__).parent.parent / "mcp.json"
        assert config_path.exists(), "mcp.json should exist in project root"
    
    def test_mcp_config_is_valid_json(self):
        """Test that the main MCP config is valid JSON."""
        config_path = Path(__file__).parent.parent / "mcp.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Should have mcpServers section
        assert "mcpServers" in config
        
        # Should have comment/sample fields but no active servers
        mcp_servers = config["mcpServers"]
        active_servers = {k: v for k, v in mcp_servers.items() if not k.startswith("_")}
        assert len(active_servers) == 0, "No active servers should be configured"