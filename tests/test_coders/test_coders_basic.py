"""Basic integration tests for all coders.

These tests check that each coder can handle a simple arithmetic question.
"""

import tempfile
import pytest

from metacoder.metacoder import create_coder
from metacoder.coders.claude import ClaudeCoder
from metacoder.coders.goose import GooseCoder
from metacoder.coders.gemini import GeminiCoder
from metacoder.coders.codex import CodexCoder
from metacoder.coders.dummy import DummyCoder
from metacoder.coders.opencode import OpencodeCoder
from metacoder.configuration import CoderConfig, AIModelConfig


# List of all available coders with their classes
ALL_CODERS = [
    ("claude", ClaudeCoder),
    ("goose", GooseCoder),
    ("gemini", GeminiCoder),
    # ("qwen", QwenCoder), ## TODO: fix qwen
    ("codex", CodexCoder),
    ("dummy", DummyCoder),
    ("opencode", OpencodeCoder),
]

# Coders that require LLM access (all except dummy)
LLM_CODERS = [(name, cls) for name, cls in ALL_CODERS if name != "dummy"]


@pytest.mark.integration
@pytest.mark.llm
@pytest.mark.parametrize("coder_name,coder_class", LLM_CODERS)
def test_llm_coder_basic_arithmetic(coder_name, coder_class):
    """Test that each LLM coder can answer a basic arithmetic question.

    This is an integration test that actually runs the coder.
    All LLM coders should include "4" in their response.
    """
    # Skip if coder is not available
    if not coder_class.is_available():
        pytest.skip(f"{coder_name} is not installed/available")

    # Create a simple config
    config = CoderConfig(
        ai_model=AIModelConfig(
            name="gpt-4" if coder_name != "claude" else "claude-3-sonnet",
            provider="openai" if coder_name != "claude" else "anthropic",
        ),
        extensions=[],
    )

    # Create temporary working directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create coder instance
        coder = create_coder(coder_name, temp_dir, config)

        # Run the simple arithmetic question
        try:
            result = coder.run("What is 2+2?")

            # Check result
            assert result is not None
            assert result.stdout or result.result_text, (
                "Coder should produce some output"
            )

            # Get the actual output text
            output_text = result.result_text or result.stdout

            # All LLM coders should include "4" in their answer
            assert "4" in output_text, (
                f"{coder_name} should answer '4' to 'What is 2+2?'"
            )

        except Exception as e:
            pytest.fail(f"Coder {coder_name} failed with error: {e}")


@pytest.mark.integration
def test_dummy_coder_basic_arithmetic():
    """Test that dummy coder works as expected (echoes input).

    This doesn't require LLM access and always runs.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create dummy coder without config
        coder = create_coder("dummy", temp_dir)

        # Run the arithmetic question
        result = coder.run("What is 2+2?")

        # Verify dummy behavior (just echoes)
        assert result is not None
        assert result.result_text == "you said: What is 2+2?"
        assert result.stdout == "you said: What is 2+2?"
        # Dummy coder won't have "4" in the answer
        assert "4" not in result.result_text


@pytest.mark.integration
@pytest.mark.llm
@pytest.mark.parametrize("coder_name,coder_class", LLM_CODERS)
def test_llm_coder_code_generation(coder_name, coder_class):
    """Test that each LLM coder can generate simple code.

    This test is more advanced and only runs on real coders (not dummy).
    """
    # Skip if coder is not available
    if not coder_class.is_available():
        pytest.skip(f"{coder_name} is not installed/available")

    # Create a simple config
    config = CoderConfig(
        ai_model=AIModelConfig(
            name="gpt-4" if coder_name != "claude" else "claude-3-sonnet",
            provider="openai" if coder_name != "claude" else "anthropic",
        ),
        extensions=[],
    )

    # Create temporary working directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create coder instance
        coder = create_coder(coder_name, temp_dir, config)

        # Ask for a simple Python function
        prompt = "Write a Python function that adds two numbers. Just the function, no explanation."

        try:
            result = coder.run(prompt)

            # Check result
            assert result is not None
            output_text = result.result_text or result.stdout
            assert output_text, "Coder should produce some output"

            # Verify the output contains Python code elements
            assert "def" in output_text, (
                f"{coder_name} should generate a Python function"
            )
            assert "return" in output_text or "print" in output_text, (
                f"{coder_name} should have return or print"
            )

        except Exception as e:
            pytest.fail(f"Coder {coder_name} failed with error: {e}")


@pytest.mark.integration
def test_dummy_coder_always_works():
    """Ensure the dummy coder works without any dependencies."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create dummy coder without config
        coder = create_coder("dummy", temp_dir)

        # Run a test
        result = coder.run("Hello, world!")

        # Verify
        assert result is not None
        assert result.result_text == "you said: Hello, world!"
        assert result.stdout == "you said: Hello, world!"
