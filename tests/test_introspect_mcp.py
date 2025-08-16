from click.testing import CliRunner
from metacoder.metacoder import cli


def test_introspect_mcp_help():
    """Test introspect-mcp help command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["introspect-mcp", "--help"])

    assert result.exit_code == 0
    assert "Introspect an MCP server" in result.output
    assert "MCP_SPEC" in result.output
    assert "--registry" in result.output
    assert "--timeout" in result.output


def test_introspect_mcp_with_invalid_registry():
    """Test introspect-mcp with non-existent registry MCP."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ["introspect-mcp", "nonexistent", "--registry", "metacoder.basics"]
    )

    assert result.exit_code != 0
    assert "not found in registry" in result.output


def test_introspect_mcp_with_registry_no_mcp():
    """Test introspect-mcp with invalid registry."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ["introspect-mcp", "fetch", "--registry", "metacoder.nonexistent"]
    )

    assert result.exit_code != 0
    assert "Registry file not found" in result.output
