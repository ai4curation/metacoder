"""Tests for MCP collection CLI functionality."""

import pytest
from pathlib import Path
from click.testing import CliRunner

from metacoder.metacoder import cli, load_mcp_collection, merge_mcp_extensions
from metacoder.configuration import CoderConfig, MCPCollectionConfig, MCPConfig, AIModelConfig, MCPType


def test_load_mcp_collection():
    """Test loading MCP collection from YAML."""
    collection_path = Path("tests/input/example_mcp_collection.yaml")
    collection = load_mcp_collection(collection_path)
    
    assert collection.name == "example_mcp_collection"
    assert len(collection.servers) == 1
    assert collection.servers[0].name == "pubmed"
    assert collection.servers[0].command == "uvx"
    assert collection.servers[0].args == ["mcp-simple-pubmed"]
    assert collection.servers[0].enabled is True


def test_load_mcp_collection_multi():
    """Test loading MCP collection with multiple servers."""
    collection_path = Path("tests/input/example_mcp_collection_multi.yaml")
    collection = load_mcp_collection(collection_path)
    
    assert collection.name == "multi_mcp_collection"
    assert len(collection.servers) == 4
    
    # Check server names
    server_names = {s.name for s in collection.servers}
    assert server_names == {"pubmed", "arxiv", "filesystem", "github"}
    
    # Check enabled status
    enabled_servers = {s.name for s in collection.servers if s.enabled}
    assert enabled_servers == {"pubmed", "arxiv", "github"}


def test_merge_mcp_extensions_no_config():
    """Test merging MCPs when no coder config exists."""
    collection = MCPCollectionConfig(
        name="test",
        servers=[
            MCPConfig(name="test1", command="test", enabled=True),
            MCPConfig(name="test2", command="test", enabled=False),
        ]
    )
    
    result = merge_mcp_extensions(None, collection)
    
    assert result is not None
    assert len(result.extensions) == 1
    assert result.extensions[0].name == "test1"


def test_merge_mcp_extensions_with_config():
    """Test merging MCPs with existing coder config."""
    config = CoderConfig(
        ai_model=AIModelConfig(name="gpt-4"),
        extensions=[
            MCPConfig(name="existing", command="existing", enabled=True)
        ]
    )
    
    collection = MCPCollectionConfig(
        name="test",
        servers=[
            MCPConfig(name="test1", command="test", enabled=True),
            MCPConfig(name="existing", command="duplicate", enabled=True),  # Should not be added
        ]
    )
    
    result = merge_mcp_extensions(config, collection)
    
    assert len(result.extensions) == 2
    extension_names = {e.name for e in result.extensions}
    assert extension_names == {"existing", "test1"}
    
    # Ensure original "existing" is preserved
    existing = next(e for e in result.extensions if e.name == "existing")
    assert existing.command == "existing"


def test_merge_mcp_extensions_selective():
    """Test merging MCPs with selective enabling."""
    collection = MCPCollectionConfig(
        name="test",
        servers=[
            MCPConfig(name="test1", command="test1", enabled=True),
            MCPConfig(name="test2", command="test2", enabled=True),
            MCPConfig(name="test3", command="test3", enabled=False),
        ]
    )
    
    result = merge_mcp_extensions(None, collection, enabled_mcps=["test2", "test3"])
    
    assert len(result.extensions) == 2
    extension_names = {e.name for e in result.extensions}
    assert extension_names == {"test2", "test3"}


def test_cli_run_with_mcp_collection(tmp_path):
    """Test CLI run command with MCP collection."""
    runner = CliRunner()
    
    # Create a test MCP collection file
    mcp_yaml = tmp_path / "test_mcps.yaml"
    mcp_yaml.write_text("""
name: test_collection
servers:
  - name: test_mcp
    command: echo
    args: ["test"]
    enabled: true
    type: stdio
""")
    
    # Test with dummy coder (doesn't require external tools)
    result = runner.invoke(cli, [
        "run",
        "Test prompt",
        "--coder", "dummy",
        "--mcp-collection", str(mcp_yaml),
        "--workdir", str(tmp_path / "work")
    ])
    
    assert result.exit_code == 0
    assert "Loading MCP collection from:" in result.output
    assert "Available MCPs: test_mcp" in result.output
    assert "Enabling MCPs: test_mcp" in result.output


def test_cli_run_with_selective_mcp(tmp_path):
    """Test CLI run command with selective MCP enabling."""
    runner = CliRunner()
    
    # Create a test MCP collection file with multiple MCPs
    mcp_yaml = tmp_path / "test_mcps.yaml"
    mcp_yaml.write_text("""
name: test_collection
servers:
  - name: mcp1
    command: echo
    args: ["test1"]
    enabled: true
    type: stdio
  - name: mcp2
    command: echo
    args: ["test2"]
    enabled: true
    type: stdio
  - name: mcp3
    command: echo
    args: ["test3"]
    enabled: false
    type: stdio
""")
    
    # Test enabling specific MCPs
    result = runner.invoke(cli, [
        "run",
        "Test prompt",
        "--coder", "dummy",
        "--mcp-collection", str(mcp_yaml),
        "--enable-mcp", "mcp2",
        "--enable-mcp", "mcp3",
        "--workdir", str(tmp_path / "work")
    ])
    
    assert result.exit_code == 0
    assert "Available MCPs: mcp1, mcp2, mcp3" in result.output
    assert "Enabling MCPs: mcp2, mcp3" in result.output


def test_cli_run_help():
    """Test that help text includes new options."""
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "--help"])
    
    assert result.exit_code == 0
    assert "--mcp-collection" in result.output
    assert "-m" in result.output
    assert "--enable-mcp" in result.output
    assert "-e" in result.output
    assert "MCPCollectionConfig YAML file" in result.output
    assert "Enable specific MCP by name" in result.output