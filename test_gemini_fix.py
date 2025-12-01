#!/usr/bin/env python3
"""
Test script to verify the GeminiCoder fix works correctly.
This tests that gemini CLI is invoked with positional arguments instead of stdin piping.
"""

import tempfile
import shutil
from pathlib import Path
import sys
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from metacoder.coders.gemini import GeminiCoder
from metacoder.configuration import RunConfig, MCPConfig, MCPType


def test_gemini_simple_prompt():
    """Test that gemini can handle a simple prompt correctly."""
    print("=" * 60)
    print("TEST 1: Simple arithmetic prompt")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workdir = Path(tmpdir) / "gemini_test"
        workdir.mkdir()

        # Create minimal config
        config = RunConfig(
            workdir=workdir,
            extensions=[],
        )

        coder = GeminiCoder(config=config, workdir=workdir)

        # Test with simple prompt
        result = coder.run("What is 2+2? Just give the number.")

        print(f"Success: {result.success}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        print(f"Result text: {result.result_text}")

        if not result.success:
            print("❌ TEST FAILED: Command did not succeed")
            return False

        if "4" not in result.result_text:
            print(f"❌ TEST FAILED: Expected '4' in result, got: {result.result_text}")
            return False

        print("✅ TEST PASSED: Simple prompt works")
        return True


def test_gemini_with_mcp():
    """Test that gemini works with MCP server configured."""
    print("\n" + "=" * 60)
    print("TEST 2: Gemini with MCP server (artl)")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workdir = Path(tmpdir) / "gemini_mcp_test"
        workdir.mkdir()

        # Create config with MCP
        mcp = MCPConfig(
            name="artl",
            type=MCPType.STDIO,
            command="uvx",
            args=["artl-mcp"],
            enabled=True,
        )

        config = RunConfig(
            workdir=workdir,
            extensions=[mcp],
        )

        coder = GeminiCoder(config=config, workdir=workdir)

        # Verify settings.json was created
        settings_file = workdir / ".gemini" / "settings.json"
        if not settings_file.exists():
            print(f"❌ TEST FAILED: settings.json not created at {settings_file}")
            return False

        with open(settings_file) as f:
            settings = json.load(f)

        if "mcpServers" not in settings:
            print(f"❌ TEST FAILED: mcpServers not in settings.json: {settings}")
            return False

        if "artl" not in settings["mcpServers"]:
            print(f"❌ TEST FAILED: artl server not configured: {settings}")
            return False

        print(f"✅ MCP configuration verified: {json.dumps(settings, indent=2)}")

        # Test with simple prompt (MCP may not be available in test env, but command should work)
        result = coder.run("What is 3+3? Just give the number.")

        print(f"Success: {result.success}")
        print(f"Stdout: {result.stdout}")

        if not result.success:
            print("❌ TEST FAILED: Command with MCP config did not succeed")
            return False

        print("✅ TEST PASSED: Gemini works with MCP configuration")
        return True


def test_gemini_special_characters():
    """Test that gemini handles prompts with special characters correctly."""
    print("\n" + "=" * 60)
    print("TEST 3: Prompt with special characters")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workdir = Path(tmpdir) / "gemini_special_test"
        workdir.mkdir()

        config = RunConfig(
            workdir=workdir,
            extensions=[],
        )

        coder = GeminiCoder(config=config, workdir=workdir)

        # Test with special characters that would break shell escaping
        test_prompt = 'Say "Hello!" with quotes and $special chars'
        result = coder.run(test_prompt)

        print(f"Success: {result.success}")
        print(f"Stdout: {result.stdout[:200]}")  # First 200 chars

        if not result.success:
            print("❌ TEST FAILED: Special characters broke the command")
            return False

        print("✅ TEST PASSED: Special characters handled correctly")
        return True


def main():
    # Check if gemini is available
    if not shutil.which("gemini"):
        print(
            "⚠️  WARNING: gemini CLI not found. Install with: npm install -g @google/gemini-cli"
        )
        sys.exit(1)

    print("Testing GeminiCoder fix...\n")

    tests = [
        test_gemini_simple_prompt,
        test_gemini_with_mcp,
        test_gemini_special_characters,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ TEST FAILED with exception: {e}")
            import traceback

            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if all(results):
        print("\n✅ ALL TESTS PASSED - Fix is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - Fix needs more work")
        sys.exit(1)


if __name__ == "__main__":
    main()
