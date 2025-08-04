"""Integration tests for MCP functionality with different coders."""

import tempfile
import pytest
import json
from pathlib import Path
from click.testing import CliRunner

from metacoder.metacoder import main
from metacoder.coders.claude import ClaudeCoder
from metacoder.coders.goose import GooseCoder


@pytest.fixture
def runner():
    """Click test runner fixture."""
    return CliRunner()


@pytest.fixture
def mcp_config_file(tmp_path):
    """Create a temporary MCP config file for testing."""
    config_content = f"""
ai_model:
  name: claude-3-sonnet
  provider: anthropic

extensions:
  - name: acme-lookup
    description: ACME store product lookup service
    command: uv
    args: ["run", "python", "{Path(__file__).parent.parent}/src/metacoder/mcps/demo_lookup.py"]
    type: stdio
    enabled: true
"""
    config_file = tmp_path / "mcp_test_config.yaml"
    config_file.write_text(config_content)
    return str(config_file)


@pytest.fixture
def goose_mcp_config_file(tmp_path):
    """Create a temporary MCP config file for Goose testing with GPT-4."""
    config_content = f"""
ai_model:
  name: gpt-4o
  provider: openai

extensions:
  - name: acme-lookup
    description: ACME store product lookup service
    command: uv
    args: ["run", "python", "{Path(__file__).parent.parent}/src/metacoder/mcps/demo_lookup.py"]
    type: stdio
    enabled: true
"""
    config_file = tmp_path / "goose_mcp_test_config.yaml"
    config_file.write_text(config_content)
    return str(config_file)


@pytest.mark.llm
@pytest.mark.parametrize(
    "coder_name,coder_class",
    [
        ("claude", ClaudeCoder),
        ("goose", GooseCoder),
    ],
)
@pytest.mark.parametrize(
    "product_id,expected_product",
    [
        (1, "chocolate chip cookies"),  # odd number
        (2, "salt and vinegar potato chips"),  # even number
    ],
)
def test_coder_mcp_product_lookup(
    runner,
    mcp_config_file,
    goose_mcp_config_file,
    coder_name,
    coder_class,
    product_id,
    expected_product,
):
    """Test that coders can use MCP tool to look up products."""
    if not coder_class.is_available():
        pytest.skip(f"{coder_name} not installed")

    # Use appropriate config for each coder
    config_file = goose_mcp_config_file if coder_name == "goose" else mcp_config_file

    with tempfile.TemporaryDirectory() as temp_dir:
        result = runner.invoke(
            main,
            [
                f"What is product number {product_id}? Just give me the product name only.",
                "--coder",
                coder_name,
                "--config",
                config_file,
                "--workdir",
                temp_dir,
            ],
        )

    if result.exit_code != 0:
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        print(f"Exception: {result.exception}")
    assert result.exit_code == 0

    # Debug: Check config file was created
    if coder_name == "goose":
        import yaml

        config_path = Path(temp_dir) / ".config/goose/config.yaml"
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f)
                print(f"Goose config: {json.dumps(config, indent=2)}")

    assert expected_product in result.output.lower()


@pytest.mark.llm
@pytest.mark.parametrize(
    "coder_name,coder_class",
    [
        ("claude", ClaudeCoder),
        ("goose", GooseCoder),
    ],
)
def test_coder_mcp_multiple_lookups(
    runner, mcp_config_file, goose_mcp_config_file, coder_name, coder_class
):
    """Test that coders can use MCP tool multiple times in one session."""
    if not coder_class.is_available():
        pytest.skip(f"{coder_name} not installed")

    # Use appropriate config for each coder
    config_file = goose_mcp_config_file if coder_name == "goose" else mcp_config_file

    with tempfile.TemporaryDirectory() as temp_dir:
        result = runner.invoke(
            main,
            [
                "What are products 1 and 2? List just the product names.",
                "--coder",
                coder_name,
                "--config",
                config_file,
                "--workdir",
                temp_dir,
            ],
        )

    assert result.exit_code == 0
    assert "chocolate chip cookies" in result.output.lower()
    assert "salt and vinegar potato chips" in result.output.lower()
