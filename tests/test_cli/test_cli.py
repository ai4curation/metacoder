import tempfile
import pytest
from pathlib import Path
from click.testing import CliRunner

from metacoder.metacoder import main


@pytest.fixture
def runner():
    """Click test runner fixture."""
    return CliRunner()


def test_cli_help(runner):
    """Test CLI help output."""
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Metacoder - Pick a coder and run commands" in result.output
    assert "Commands:" in result.output
    assert "list-coders" in result.output
    assert "run" in result.output


def test_run_help(runner):
    """Test run subcommand help output."""
    result = runner.invoke(main, ["run", "--help"])
    assert result.exit_code == 0
    assert "--coder" in result.output
    assert "--config" in result.output
    assert "--workdir" in result.output
    assert "--verbose" in result.output


def test_cli_version(runner):
    """Test CLI version output."""
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0


def test_dummy_coder_simple(runner):
    """Test dummy coder with simple input."""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = runner.invoke(
            main, ["What is 1+1?", "--coder", "dummy", "--workdir", temp_dir]
        )

    assert result.exit_code == 0
    assert "Using coder: dummy" in result.output
    assert "you said: What is 1+1?" in result.output


def test_all_coders_available(runner):
    """Test that all coders are listed in run help."""
    result = runner.invoke(main, ["run", "--help"])
    assert result.exit_code == 0
    assert "goose" in result.output
    assert "claude" in result.output
    assert "codex" in result.output
    assert "gemini" in result.output
    assert "qwen" in result.output
    assert "dummy" in result.output


def test_verbose_mode_dummy(runner):
    """Test verbose mode with dummy coder."""
    result = runner.invoke(main, ["What is 1+1?", "--coder", "dummy", "--verbose"])

    assert result.exit_code == 0
    assert "you said: What is 1+1?" in result.output


def test_custom_workdir_dummy(runner):
    """Test custom working directory with dummy coder."""
    with tempfile.TemporaryDirectory() as temp_dir:
        custom_dir = Path(temp_dir) / "my_custom_dir"
        result = runner.invoke(
            main, ["test prompt", "--coder", "dummy", "--workdir", str(custom_dir)]
        )

    assert result.exit_code == 0
    assert f"Working directory: {custom_dir}" in result.output
    assert "you said: test prompt" in result.output


def test_with_config_file_dummy(runner):
    """Test loading configuration from file with dummy coder."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create config file
        config_path = Path(temp_dir) / "config.yaml"
        config_data = """
ai_model:
  name: gpt-4o
  provider:
    name: openai
    api_key: test-key
extensions: []
"""
        config_path.write_text(config_data)

        result = runner.invoke(
            main, ["test with config", "--coder", "dummy", "--config", str(config_path)]
        )

    assert result.exit_code == 0
    assert f"Loading config from: {config_path}" in result.output
    assert "you said: test with config" in result.output


def test_missing_prompt(runner):
    """Test error when prompt is missing from run command."""
    result = runner.invoke(main, ["run"])
    assert result.exit_code != 0
    assert "Missing argument" in result.output


def test_invalid_coder(runner):
    """Test error with invalid coder name."""
    result = runner.invoke(main, ["test prompt", "--coder", "invalid_coder"])
    assert result.exit_code != 0
    assert "Invalid value" in result.output


def test_nonexistent_config_file(runner):
    """Test error with non-existent config file."""
    result = runner.invoke(
        main, ["test prompt", "--config", "/nonexistent/config.yaml"]
    )
    assert result.exit_code != 0
    assert "does not exist" in result.output.lower()


def test_multiple_arithmetic_with_dummy(runner):
    """Test multiple arithmetic questions with dummy coder."""
    test_cases = ["What is 2+2?", "Calculate 10*5", "What is 100/4?", "Compute 7-3"]

    for prompt in test_cases:
        result = runner.invoke(main, [prompt, "--coder", "dummy"])

        assert result.exit_code == 0
        assert f"you said: {prompt}" in result.output


def test_complex_prompt_dummy(runner):
    """Test with a complex prompt using dummy coder."""
    complex_prompt = """
    Please help me with the following tasks:
    1. Calculate the sum of numbers from 1 to 10
    2. Explain the result
    3. Write a Python function to do this
    """

    result = runner.invoke(main, [complex_prompt, "--coder", "dummy"])

    assert result.exit_code == 0
    assert "you said:" in result.output
    assert "Calculate the sum" in result.output


def test_dummy_verbose_mode(runner):
    """Test dummy coder in verbose mode shows all output."""
    result = runner.invoke(main, ["test prompt", "--coder", "dummy", "--verbose"])

    assert result.exit_code == 0
    assert "you said: test prompt" in result.output
    assert "Result:" in result.output
    assert "Standard Output:" in result.output


def test_invalid_config_yaml(runner):
    """Test error with invalid YAML in config file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "bad_config.yaml"
        config_path.write_text("invalid: yaml: [[[")

        result = runner.invoke(main, ["test", "--config", str(config_path)])

        assert result.exit_code != 0
        assert "Invalid YAML" in result.output


def test_invalid_config_structure(runner):
    """Test error with invalid config structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "bad_structure.yaml"
        config_path.write_text('ai_model: "should be dict not string"')

        result = runner.invoke(main, ["test", "--config", str(config_path)])

        assert result.exit_code != 0
        assert "Invalid config format" in result.output


def test_list_coders_subcommand(runner):
    """Test list-coders subcommand."""
    result = runner.invoke(main, ["list-coders"])

    assert result.exit_code == 0
    assert "Available coders:" in result.output
    assert "goose" in result.output
    assert "claude" in result.output
    assert "codex" in result.output
    assert "gemini" in result.output
    assert "qwen" in result.output
    assert "dummy" in result.output
    # Should have checkmarks or X marks
    assert "✅" in result.output or "❌" in result.output


def test_run_subcommand_explicit(runner):
    """Test explicit run subcommand."""
    result = runner.invoke(main, ["run", "test prompt", "--coder", "dummy"])

    assert result.exit_code == 0
    assert "you said: test prompt" in result.output


def test_missing_prompt_shows_help(runner):
    """Test that no arguments shows help."""
    result = runner.invoke(main, [])

    assert result.exit_code == 0
    assert "Commands:" in result.output
    assert "list-coders" in result.output
    assert "run" in result.output
