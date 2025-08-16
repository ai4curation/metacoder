"""Test the --instructions command line option."""

import tempfile
from pathlib import Path
from click.testing import CliRunner
import pytest

from metacoder.metacoder import main


@pytest.fixture
def runner():
    """Click test runner fixture."""
    return CliRunner()


def test_instructions_option_with_dummy_coder(runner):
    """Test that --instructions option loads and passes instructions to coder."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create an instructions file
        instructions_file = Path(temp_dir) / "test_instructions.md"
        instructions_content = "# Test Instructions\n\nBe helpful and concise."
        instructions_file.write_text(instructions_content)

        # Run with instructions
        result = runner.invoke(
            main,
            [
                "run",
                "Hello",
                "--coder",
                "dummy",
                "--instructions",
                str(instructions_file),
                "--workdir",
                temp_dir,
            ],
        )

        # Check that instructions were loaded
        assert result.exit_code == 0
        assert "Loaded instructions from:" in result.output
        assert "Instructions loaded:" in result.output
        assert instructions_content in result.output


def test_no_instructions_still_works(runner):
    """Test that coder still works without --instructions option."""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = runner.invoke(
            main,
            [
                "run",
                "Hello",
                "--coder",
                "dummy",
                "--workdir",
                temp_dir,
            ],
        )

        assert result.exit_code == 0
        assert "you said: Hello" in result.output
        assert "Instructions loaded:" not in result.output


def test_instructions_file_not_found(runner):
    """Test error handling when instructions file doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = runner.invoke(
            main,
            [
                "run",
                "Hello",
                "--coder",
                "dummy",
                "--instructions",
                "/nonexistent/file.md",
                "--workdir",
                temp_dir,
            ],
        )

        # Should fail with appropriate error
        assert result.exit_code != 0
        assert "does not exist" in result.output


def test_instructions_with_config(runner):
    """Test that --instructions works alongside --config."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create config file
        config_file = Path(temp_dir) / "config.yaml"
        config_content = """
ai_model:
  name: gpt-4
  provider: openai
extensions: []
"""
        config_file.write_text(config_content)

        # Create instructions file
        instructions_file = Path(temp_dir) / "instructions.md"
        instructions_file.write_text("Custom instructions")

        result = runner.invoke(
            main,
            [
                "run",
                "Test",
                "--coder",
                "dummy",
                "--config",
                str(config_file),
                "--instructions",
                str(instructions_file),
                "--workdir",
                temp_dir,
            ],
        )

        assert result.exit_code == 0
        assert "Loaded instructions from:" in result.output
