"""Test MCP support in GeminiCoder."""

import pytest
from metacoder.coders.gemini import GeminiCoder
from metacoder.configuration import CoderConfig, MCPConfig, MCPType, AIModelConfig


def test_gemini_supports_mcp():
    """Test that GeminiCoder reports MCP support."""
    assert GeminiCoder.supports_mcp() is True


def test_gemini_mcp_config_conversion():
    """Test conversion of MCPConfig to Gemini format."""
    coder = GeminiCoder(workdir="/tmp/test")

    # Test stdio MCP
    mcp = MCPConfig(
        name="test_server",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-test"],
        env={"API_KEY": "${TEST_KEY}"},
        enabled=True,
        type=MCPType.STDIO,
    )

    result = coder.mcp_config_to_gemini_format(mcp)

    assert result["command"] == "npx"
    assert result["args"] == ["-y", "@modelcontextprotocol/server-test"]
    assert result["env"] == {"API_KEY": "${TEST_KEY}"}
    assert result["timeout"] == 30000


def test_gemini_http_mcp_not_supported():
    """Test that HTTP MCPs raise NotImplementedError."""
    coder = GeminiCoder(workdir="/tmp/test")

    mcp = MCPConfig(name="http_server", enabled=True, type=MCPType.HTTP)

    with pytest.raises(NotImplementedError, match="HTTP MCPs are not supported"):
        coder.mcp_config_to_gemini_format(mcp)


def test_gemini_mcp_settings_generation():
    """Test that MCP settings are properly generated."""
    config = CoderConfig(
        ai_model=AIModelConfig(name="gemini-2.0-flash-exp", provider="google"),
        extensions=[
            MCPConfig(
                name="filesystem",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem"],
                enabled=True,
                type=MCPType.STDIO,
            ),
            MCPConfig(
                name="github",
                command="uvx",
                args=["mcp-github"],
                env={"GITHUB_TOKEN": "${GITHUB_TOKEN}"},
                enabled=True,
                type=MCPType.STDIO,
            ),
            MCPConfig(
                name="disabled_server",
                command="uvx",
                args=["mcp-disabled"],
                enabled=False,
                type=MCPType.STDIO,
            ),
        ],
    )

    coder = GeminiCoder(workdir="/tmp/test", config=config)
    config_objects = coder.default_config_objects()

    # Should have created settings.json
    assert len(config_objects) == 1
    settings_obj = config_objects[0]

    assert settings_obj.relative_path == ".gemini/settings.json"
    assert "mcpServers" in settings_obj.content

    mcp_servers = settings_obj.content["mcpServers"]

    # Should only include enabled servers
    assert "filesystem" in mcp_servers
    assert "github" in mcp_servers
    assert "disabled_server" not in mcp_servers

    # Check filesystem server config
    fs_config = mcp_servers["filesystem"]
    assert fs_config["command"] == "npx"
    assert fs_config["args"] == ["-y", "@modelcontextprotocol/server-filesystem"]
    assert fs_config["timeout"] == 30000

    # Check github server config
    gh_config = mcp_servers["github"]
    assert gh_config["command"] == "uvx"
    assert gh_config["args"] == ["mcp-github"]
    assert gh_config["env"] == {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}
    assert gh_config["timeout"] == 30000


def test_gemini_no_mcp_no_settings():
    """Test that no settings.json is created when no MCPs are configured."""
    coder = GeminiCoder(workdir="/tmp/test")
    config_objects = coder.default_config_objects()

    # Should not create any config files when no MCPs
    assert len(config_objects) == 0
