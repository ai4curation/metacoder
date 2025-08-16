import pytest
from click.testing import CliRunner
from metacoder.metacoder import cli, load_mcp_registry
from metacoder.configuration import MCPCollectionConfig


def test_load_mcp_registry_basics():
    """Test loading basics registry."""
    collection = load_mcp_registry("metacoder.basics")

    assert isinstance(collection, MCPCollectionConfig)
    assert len(collection.servers) > 0

    # Check that fetch is in basics
    mcp_names = [mcp.name for mcp in collection.servers]
    assert "fetch" in mcp_names
    assert "taskmasterai" in mcp_names

    # Check that all are disabled by default
    for mcp in collection.servers:
        assert not mcp.enabled and mcp.enabled is not None


def test_load_mcp_registry_scilit():
    """Test loading scilit registry."""
    collection = load_mcp_registry("metacoder.scilit")

    assert isinstance(collection, MCPCollectionConfig)
    assert len(collection.servers) > 0

    # Check that scilit MCPs are present
    mcp_names = [mcp.name for mcp in collection.servers]
    assert "pdfreader" in mcp_names
    assert "artl" in mcp_names
    assert "biomcp" in mcp_names


def test_load_mcp_registry_all():
    """Test loading all registries with 'metacoder'."""
    collection = load_mcp_registry("metacoder")

    assert isinstance(collection, MCPCollectionConfig)

    # Should have MCPs from both basics and scilit
    mcp_names = [mcp.name for mcp in collection.servers]
    assert "fetch" in mcp_names  # from basics
    assert "pdfreader" in mcp_names  # from scilit


def test_load_mcp_registry_without_prefix():
    """Test loading registry without metacoder prefix."""
    collection = load_mcp_registry("basics")

    # Should work the same as with prefix
    mcp_names = [mcp.name for mcp in collection.servers]
    assert "fetch" in mcp_names


def test_cli_with_registry():
    """Test CLI with registry option."""
    runner = CliRunner()

    # Test with registry and enable specific MCP
    result = runner.invoke(
        cli,
        [
            "run",
            "test prompt",
            "--coder",
            "dummy",
            "--registry",
            "metacoder.basics",
            "--enable-mcp",
            "fetch",
            "--workdir",
            "test_workdir",
        ],
    )

    assert result.exit_code == 0
    assert "Loading MCPs from registry: metacoder.basics" in result.output
    assert "Registry MCPs:" in result.output
    assert "fetch" in result.output


def test_cli_registry_with_mcp_collection():
    """Test CLI with both registry and MCP collection."""
    runner = CliRunner()

    # Create a temporary MCP collection file
    with runner.isolated_filesystem():
        with open("test_mcps.yaml", "w") as f:
            f.write("""name: test_collection
description: Test MCP collection
servers:
  - name: custom_mcp
    command: echo
    args: ["test"]
    enabled: true
""")

        result = runner.invoke(
            cli,
            [
                "run",
                "test prompt",
                "--coder",
                "dummy",
                "--mcp-collection",
                "test_mcps.yaml",
                "--registry",
                "metacoder.basics",
                "--enable-mcp",
                "fetch",
                "--enable-mcp",
                "custom_mcp",
                "--workdir",
                "test_workdir",
            ],
        )

        assert result.exit_code == 0
        assert "Loading MCP collection from: test_mcps.yaml" in result.output
        assert "Loading MCPs from registry: metacoder.basics" in result.output
        assert "custom_mcp" in result.output


def test_registry_nonexistent():
    """Test loading nonexistent registry."""
    with pytest.raises(Exception) as exc_info:
        load_mcp_registry("metacoder.nonexistent")

    assert "Registry file not found" in str(exc_info.value)
