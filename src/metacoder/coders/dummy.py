from metacoder.coders.base_coder import BaseCoder, CoderConfigObject, CoderOutput, ToolUse


class DummyCoder(BaseCoder):
    """
    Dummy coder for testing.
    
    Simulates tool use when input contains keywords:
    - "tool" or "mcp": Adds a generic test tool
    - "search" or "pubmed": Simulates a PubMed search tool
    - "error": Simulates a tool failure
    
    Multiple keywords can trigger multiple tools.
    """

    @classmethod
    def supports_mcp(cls) -> bool:
        """DummyCoder supports MCP for testing purposes."""
        return True

    def default_config_objects(self) -> list[CoderConfigObject]:
        return []

    def run(self, input_text: str) -> CoderOutput:
        output = CoderOutput(
            stdout="you said: " + input_text,
            stderr="",
            result_text="you said: " + input_text,
        )
        
        # Add fake tool uses if input mentions tools, MCP, or specific services
        if any(keyword in input_text.lower() for keyword in ["tool", "mcp", "pubmed", "search"]):
            # Create some fake tool uses for testing
            tool_uses = []
            
            # Simulate a successful tool call
            if "search" in input_text.lower() or "pubmed" in input_text.lower():
                tool_uses.append(ToolUse(
                    name="mcp__pubmed__search_papers",
                    arguments={"query": "test query", "limit": 10},
                    success=True,
                    error=None,
                    result={"papers": ["paper1", "paper2"], "count": 2}
                ))
            
            # Simulate a tool with an error
            if "error" in input_text.lower():
                tool_uses.append(ToolUse(
                    name="mcp__test__failing_tool", 
                    arguments={"param": "value"},
                    success=False,
                    error="Simulated tool error for testing",
                    result=None
                ))
            
            # Default tool if no specific keywords but general tool/mcp mentioned
            if not tool_uses:
                tool_uses.append(ToolUse(
                    name="mcp__dummy__test_tool",
                    arguments={"input": input_text},
                    success=True,
                    error=None,
                    result="Test tool executed successfully"
                ))
            
            if tool_uses:
                output.tool_uses = tool_uses
        
        return output
