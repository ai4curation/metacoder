"""Test DummyCoder fake tool use generation."""
from metacoder.coders.dummy import DummyCoder


def test_dummy_no_tools():
    """Test that dummy coder doesn't add tools when not mentioned."""
    coder = DummyCoder(workdir="test")
    output = coder.run("What is 2 + 2?")
    
    assert output.stdout == "you said: What is 2 + 2?"
    assert output.tool_uses is None


def test_dummy_default_tool():
    """Test that dummy coder adds default tool when mentioned."""
    coder = DummyCoder(workdir="test")
    output = coder.run("Use a tool to help me")
    
    assert output.tool_uses is not None
    assert len(output.tool_uses) == 1
    
    tool = output.tool_uses[0]
    assert tool.name == "mcp__dummy__test_tool"
    assert tool.arguments == {"input": "Use a tool to help me"}
    assert tool.success is True
    assert tool.error is None
    assert tool.result == "Test tool executed successfully"


def test_dummy_pubmed_search():
    """Test that dummy coder simulates PubMed search."""
    coder = DummyCoder(workdir="test")
    output = coder.run("Search PubMed for papers about cancer")
    
    assert output.tool_uses is not None
    assert len(output.tool_uses) == 1
    
    tool = output.tool_uses[0]
    assert tool.name == "mcp__pubmed__search_papers"
    assert tool.arguments == {"query": "test query", "limit": 10}
    assert tool.success is True
    assert tool.error is None
    assert tool.result == {"papers": ["paper1", "paper2"], "count": 2}


def test_dummy_tool_error():
    """Test that dummy coder simulates tool errors."""
    coder = DummyCoder(workdir="test")
    output = coder.run("Use MCP tool but simulate an error")
    
    assert output.tool_uses is not None
    assert len(output.tool_uses) == 1
    
    tool = output.tool_uses[0]
    assert tool.name == "mcp__test__failing_tool"
    assert tool.arguments == {"param": "value"}
    assert tool.success is False
    assert tool.error == "Simulated tool error for testing"
    assert tool.result is None


def test_dummy_multiple_tools():
    """Test that dummy coder can simulate multiple tools."""
    coder = DummyCoder(workdir="test")
    output = coder.run("Search PubMed and then simulate an error with MCP")
    
    assert output.tool_uses is not None
    assert len(output.tool_uses) == 2
    
    # First tool - PubMed search
    tool1 = output.tool_uses[0]
    assert tool1.name == "mcp__pubmed__search_papers"
    assert tool1.success is True
    
    # Second tool - error simulation
    tool2 = output.tool_uses[1]
    assert tool2.name == "mcp__test__failing_tool"
    assert tool2.success is False


def test_dummy_mcp_keyword():
    """Test that MCP keyword triggers tool use."""
    coder = DummyCoder(workdir="test")
    output = coder.run("Test MCP functionality")
    
    assert output.tool_uses is not None
    assert len(output.tool_uses) == 1
    
    tool = output.tool_uses[0]
    assert tool.name == "mcp__dummy__test_tool"
    assert tool.success is True