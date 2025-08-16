"""Test that DummyCoder properly captures tool calls in CoderOutput."""

from metacoder.coders.dummy import DummyCoder
from metacoder.coders.base_coder import CoderOutput, ToolUse


def test_dummy_coder_captures_tool_calls():
    """Test that DummyCoder captures tool calls in the CoderOutput."""
    coder = DummyCoder(workdir="test")

    # Run with input that triggers tool use
    output = coder.run("Use MCP to search PubMed for cancer research")

    # Verify output is a CoderOutput instance
    assert isinstance(output, CoderOutput)

    # Verify basic output fields
    assert output.stdout == "you said: Use MCP to search PubMed for cancer research"
    assert output.stderr == ""
    assert (
        output.result_text == "you said: Use MCP to search PubMed for cancer research"
    )

    # Verify tool_uses is populated
    assert output.tool_uses is not None
    assert isinstance(output.tool_uses, list)
    assert len(output.tool_uses) == 1

    # Verify the tool use is properly structured
    tool_use = output.tool_uses[0]
    assert isinstance(tool_use, ToolUse)
    assert tool_use.name == "mcp__pubmed__search_papers"
    assert tool_use.arguments == {"query": "test query", "limit": 10}
    assert tool_use.success is True
    assert tool_use.error is None
    assert tool_use.result == {"papers": ["paper1", "paper2"], "count": 2}


def test_dummy_coder_captures_multiple_tools():
    """Test that DummyCoder can capture multiple tool calls."""
    coder = DummyCoder(workdir="test")

    # Run with input that triggers multiple tools
    output = coder.run("Search PubMed and then cause an error")

    # Verify multiple tools are captured
    assert output.tool_uses is not None
    assert len(output.tool_uses) == 2

    # Verify each tool is a proper ToolUse instance
    for tool in output.tool_uses:
        assert isinstance(tool, ToolUse)
        assert hasattr(tool, "name")
        assert hasattr(tool, "arguments")
        assert hasattr(tool, "success")
        assert hasattr(tool, "error")
        assert hasattr(tool, "result")

    # Check first tool (PubMed search)
    assert output.tool_uses[0].name == "mcp__pubmed__search_papers"
    assert output.tool_uses[0].success is True

    # Check second tool (error)
    assert output.tool_uses[1].name == "mcp__test__failing_tool"
    assert output.tool_uses[1].success is False
    assert output.tool_uses[1].error is not None


def test_dummy_coder_no_tools_when_not_triggered():
    """Test that DummyCoder doesn't add tools when not triggered."""
    coder = DummyCoder(workdir="test")

    # Run with input that doesn't trigger tools
    output = coder.run("What is the weather today?")

    # Verify output structure
    assert isinstance(output, CoderOutput)
    assert output.stdout == "you said: What is the weather today?"

    # Verify no tools are added
    assert output.tool_uses is None


def test_dummy_coder_tool_error_capture():
    """Test that DummyCoder properly captures tool errors."""
    coder = DummyCoder(workdir="test")

    # Run with input that triggers an error
    output = coder.run("Use tool with error")

    # Verify error tool is captured
    assert output.tool_uses is not None
    assert len(output.tool_uses) == 1

    error_tool = output.tool_uses[0]
    assert error_tool.name == "mcp__test__failing_tool"
    assert error_tool.success is False
    assert error_tool.error == "Simulated tool error for testing"
    assert error_tool.result is None
    assert error_tool.arguments == {"param": "value"}


def test_dummy_coder_tool_serialization():
    """Test that tool uses can be serialized properly."""
    coder = DummyCoder(workdir="test")

    # Run with tool trigger
    output = coder.run("Use MCP tool")

    # Verify tool uses can be converted to dict (for serialization)
    assert output.tool_uses is not None
    tool_dict = output.tool_uses[0].model_dump()

    assert isinstance(tool_dict, dict)
    assert "name" in tool_dict
    assert "arguments" in tool_dict
    assert "success" in tool_dict
    assert "error" in tool_dict
    assert "result" in tool_dict

    # Verify values
    assert tool_dict["name"] == "mcp__dummy__test_tool"
    assert tool_dict["success"] is True
    assert tool_dict["error"] is None
