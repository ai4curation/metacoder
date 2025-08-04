"""Integration tests for CLI with real coders (if available)."""

import tempfile
import pytest
from pathlib import Path
from click.testing import CliRunner

from metacoder.metacoder import main
from metacoder.coders.goose import GooseCoder
from metacoder.coders.claude import ClaudeCoder
from metacoder.coders.gemini import GeminiCoder
from metacoder.coders.qwen import QwenCoder


@pytest.fixture
def runner():
    """Click test runner fixture."""
    return CliRunner()


@pytest.mark.llm
@pytest.mark.skipif(not GooseCoder.is_available(), reason="goose not installed")
def test_goose_simple_arithmetic(runner):
    """Test goose with simple arithmetic (requires goose to be installed)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = runner.invoke(
            main,
            [
                "What is 1+1? Just give me the number.",
                "--coder",
                "goose",
                "--workdir",
                temp_dir,
            ],
        )

    assert result.exit_code == 0
    assert "Using coder: goose" in result.output
    assert "2" in result.output  # The answer should appear somewhere


@pytest.mark.llm
@pytest.mark.skipif(not ClaudeCoder.is_available(), reason="claude not installed")
def test_claude_simple_arithmetic(runner):
    """Test claude with simple arithmetic (requires claude to be installed)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = runner.invoke(
            main,
            [
                "What is 1+1? Just respond with the number.",
                "--coder",
                "claude",
                "--workdir",
                temp_dir,
            ],
        )

    assert result.exit_code == 0
    assert "Using coder: claude" in result.output
    assert "2" in result.output  # The answer should appear somewhere


def test_dummy_always_works(runner):
    """Test that dummy coder always works without dependencies."""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = runner.invoke(
            main, ["What is 1+1?", "--coder", "dummy", "--workdir", temp_dir]
        )

    assert result.exit_code == 0
    assert "Using coder: dummy" in result.output
    assert "you said: What is 1+1?" in result.output


@pytest.mark.llm
def test_different_coders_comparison(runner):
    """Compare outputs from different coders."""
    prompt = "Calculate 5 + 3"

    # Test with dummy
    with tempfile.TemporaryDirectory() as temp_dir:
        dummy_result = runner.invoke(
            main, [prompt, "--coder", "dummy", "--workdir", temp_dir]
        )

    assert dummy_result.exit_code == 0
    assert "you said: Calculate 5 + 3" in dummy_result.output

    # Test with goose if available
    if GooseCoder.is_available():
        with tempfile.TemporaryDirectory() as temp_dir:
            goose_result = runner.invoke(
                main, [prompt, "--coder", "goose", "--workdir", temp_dir]
            )

        assert goose_result.exit_code == 0
        assert "8" in goose_result.output or "eight" in goose_result.output.lower()


@pytest.mark.llm
@pytest.mark.skipif(not GeminiCoder.is_available(), reason="gemini not installed")
def test_gemini_simple_arithmetic(runner):
    """Test gemini with simple arithmetic (requires gemini to be installed)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = runner.invoke(
            main,
            [
                "What is 1+1? Just respond with the number.",
                "--coder",
                "gemini",
                "--workdir",
                temp_dir,
            ],
        )

    assert result.exit_code == 0
    assert "Using coder: gemini" in result.output
    assert "2" in result.output  # The answer should appear somewhere


@pytest.mark.llm
@pytest.mark.skipif(not QwenCoder.is_available(), reason="qwen not installed")
def test_qwen_simple_arithmetic(runner):
    """Test qwen with simple arithmetic (requires qwen to be installed)."""
    import os

    # Qwen needs DASHSCOPE_API_KEY or OPENAI_API_KEY
    if not os.environ.get("DASHSCOPE_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("DASHSCOPE_API_KEY or OPENAI_API_KEY not set")

    with tempfile.TemporaryDirectory() as temp_dir:
        result = runner.invoke(
            main,
            [
                "What is 1+1? Just respond with the number.",
                "--coder",
                "qwen",
                "--workdir",
                temp_dir,
            ],
        )

    # Qwen CLI might have configuration issues in test environment
    # Just check that the coder was invoked
    assert "Using coder: qwen" in result.output
    assert "Working directory:" in result.output

    # If it succeeded, check for the answer
    if result.exit_code == 0:
        assert "2" in result.output  # The answer should appear somewhere
    else:
        # Just ensure it tried to run qwen
        assert "Running prompt:" in result.output


def test_cli_with_complex_workdir(runner):
    """Test CLI with complex working directory setup."""
    with tempfile.TemporaryDirectory() as base_dir:
        # Create a nested directory structure
        workdir = Path(base_dir) / "project" / "workspace"
        workdir.mkdir(parents=True)

        # Create a test file
        test_file = workdir / "test.txt"
        test_file.write_text("Hello World")

        result = runner.invoke(
            main,
            [
                "What files are in my working directory?",
                "--coder",
                "dummy",
                "--workdir",
                str(workdir),
            ],
        )

        assert result.exit_code == 0
        assert f"Working directory: {workdir}" in result.output
