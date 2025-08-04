"""Test declarative MCP configuration for ClaudeCoder."""
import json
from pathlib import Path
import tempfile
import pytest

from metacoder.coders.claude import ClaudeCoder
from metacoder.configuration import CoderConfig, AIModelConfig, MCPConfig, MCPType, AIModelProvider


def test_claude_mcp_config():
    """Test that ClaudeCoder correctly generates .mcp.json from MCPConfig objects."""
    
    # Create MCP configurations declaratively
    mcp_configs = [
        MCPConfig(
            name="pubmed",
            description="Access PubMed articles",
            command="uvx",
            args=["mcp-simple-pubmed"],
            env={"PUBMED_EMAIL": "test@example.com"},
            type=MCPType.STDIO,
            enabled=True
        ),
        MCPConfig(
            name="filesystem",
            description="File system access",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
            type=MCPType.STDIO,
            enabled=True
        ),
        MCPConfig(
            name="disabled-mcp",
            description="This should not appear",
            command="test",
            enabled=False
        )
    ]
    
    # Create AI model config
    ai_model = AIModelConfig(
        name="claude-3-sonnet",
        provider="anthropic"
    )
    
    # Create coder config with MCPs
    coder_config = CoderConfig(
        ai_model=ai_model,
        extensions=mcp_configs
    )
    
    # Create ClaudeCoder with config
    with tempfile.TemporaryDirectory() as tmpdir:
        coder = ClaudeCoder(
            workdir=tmpdir,
            config=coder_config
        )
        
        # Generate config objects
        config_objects = coder.default_config_objects()
        
        # Should have one .mcp.json file
        mcp_json_configs = [obj for obj in config_objects if obj.relative_path == ".mcp.json"]
        assert len(mcp_json_configs) == 1
        
        mcp_json = mcp_json_configs[0]
        assert mcp_json.file_type.value == "json"
        
        # Verify content
        content = mcp_json.content
        assert "mcpServers" in content
        servers = content["mcpServers"]
        
        # Should have 2 enabled servers
        assert len(servers) == 2
        assert "pubmed" in servers
        assert "filesystem" in servers
        assert "disabled-mcp" not in servers
        
        # Verify pubmed server config
        pubmed_config = servers["pubmed"]
        assert pubmed_config["command"] == "uvx"
        assert pubmed_config["args"] == ["mcp-simple-pubmed"]
        assert pubmed_config["env"] == {"PUBMED_EMAIL": "test@example.com"}
        
        # Verify filesystem server config
        fs_config = servers["filesystem"]
        assert fs_config["command"] == "npx"
        assert fs_config["args"] == ["-y", "@modelcontextprotocol/server-filesystem"]


def test_claude_no_mcp_config():
    """Test that ClaudeCoder works without MCP configurations."""
    
    ai_model = AIModelConfig(
        name="claude-3-sonnet",
        provider="anthropic"
    )
    
    # Create coder config without MCPs
    coder_config = CoderConfig(
        ai_model=ai_model,
        extensions=[]
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        coder = ClaudeCoder(
            workdir=tmpdir,
            config=coder_config
        )
        
        # Generate config objects
        config_objects = coder.default_config_objects()
        
        # Should have no .mcp.json file
        mcp_json_configs = [obj for obj in config_objects if obj.relative_path == ".mcp.json"]
        assert len(mcp_json_configs) == 0


def test_claude_mcp_conversion():
    """Test the MCP config to Claude format conversion."""
    coder = ClaudeCoder(workdir="test")
    
    # Test STDIO type
    mcp = MCPConfig(
        name="test",
        command="uvx",
        args=["test-mcp"],
        env={"TEST": "value"},
        type=MCPType.STDIO
    )
    
    result = coder.mcp_config_to_claude_format(mcp)
    assert result["command"] == "uvx"
    assert result["args"] == ["test-mcp"]
    assert result["env"] == {"TEST": "value"}
    
    # Test minimal config
    mcp_minimal = MCPConfig(
        name="minimal",
        command="test",
        type=MCPType.STDIO
    )
    
    result_minimal = coder.mcp_config_to_claude_format(mcp_minimal)
    assert result_minimal["command"] == "test"
    assert "args" not in result_minimal
    assert "env" not in result_minimal