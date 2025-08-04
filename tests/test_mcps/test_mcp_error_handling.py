"""Test error handling for MCP configuration with unsupported coders."""
import tempfile
import pytest
from pathlib import Path
from click.testing import CliRunner

from metacoder.metacoder import main
from metacoder.coders.dummy import DummyCoder
from metacoder.coders.qwen import QwenCoder
from metacoder.coders.gemini import GeminiCoder
from metacoder.coders.codex import CodexCoder


@pytest.fixture
def runner():
    """Click test runner fixture."""
    return CliRunner()


@pytest.fixture
def mcp_config_file(tmp_path):
    """Create a temporary MCP config file for testing."""
    config_content = f"""
ai_model:
  name: gpt-4
  provider: openai

extensions:
  - name: test-mcp
    description: Test MCP extension
    command: echo
    args: ["test"]
    type: stdio
    enabled: true
"""
    config_file = tmp_path / "mcp_error_test_config.yaml"
    config_file.write_text(config_content)
    return str(config_file)


@pytest.mark.parametrize("coder_name", ["qwen", "gemini", "codex"])
def test_mcp_not_supported_error(runner, mcp_config_file, coder_name):
    """Test that coders without MCP support raise an error when MCP is configured."""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = runner.invoke(main, [
            'Hello',
            '--coder', coder_name,
            '--config', mcp_config_file,
            '--workdir', temp_dir
        ])
    
    # Debug output
    if result.exit_code != 1:
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        print(f"Exception: {result.exception}")
    
    # Should fail with exit code 1
    assert result.exit_code == 1
    
    # Should contain error message about MCP not being supported
    assert "MCP extensions are configured but" in result.output
    assert "does not support MCP" in result.output
    assert "Found 1 enabled MCP extension(s)" in result.output


def test_no_mcp_config_works(runner):
    """Test that coders without MCP support work fine when no MCP is configured."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a config without MCP extensions
        config_content = """
ai_model:
  name: gpt-4
  provider: openai
extensions: []
"""
        config_file = Path(temp_dir) / "no_mcp_config.yaml"
        config_file.write_text(config_content)
        
        result = runner.invoke(main, [
            'Hello',
            '--coder', 'dummy',
            '--config', str(config_file),
            '--workdir', temp_dir
        ])
    
    # Debug output
    if result.exit_code != 0:
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        print(f"Exception: {result.exception}")
    
    # Should succeed
    assert result.exit_code == 0
    assert "you said: Hello" in result.output


def test_disabled_mcp_extension_works(runner):
    """Test that disabled MCP extensions don't trigger the error."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a config with disabled MCP extension
        config_content = """
ai_model:
  name: gpt-4
  provider: openai

extensions:
  - name: test-mcp
    description: Test MCP extension
    command: echo
    args: ["test"]
    type: stdio
    enabled: false
"""
        config_file = Path(temp_dir) / "disabled_mcp_config.yaml"
        config_file.write_text(config_content)
        
        result = runner.invoke(main, [
            'Hello',
            '--coder', 'dummy',
            '--config', str(config_file),
            '--workdir', temp_dir
        ])
    
    # Should succeed since MCP is disabled
    assert result.exit_code == 0
    assert "you said: Hello" in result.output