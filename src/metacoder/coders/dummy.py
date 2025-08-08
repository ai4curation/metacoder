from pathlib import Path
from metacoder.coders.base_coder import BaseCoder, CoderConfigObject, CoderOutput, ToolUse
from metacoder.configuration import ConfigFileRole


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

    @classmethod
    def default_config_paths(cls) -> dict[Path, ConfigFileRole]:
        return {
            Path("INSTRUCTIONS.md"): ConfigFileRole.PRIMARY_INSTRUCTION,
        }

    def default_config_objects(self) -> list[CoderConfigObject]:
        return []

    def run(self, input_text: str) -> CoderOutput:
        # Check if instructions were set
        instructions_content = None
        if self.config_objects:
            for obj in self.config_objects:
                if obj.relative_path == "INSTRUCTIONS.md" or obj.relative_path == str(Path("INSTRUCTIONS.md")):
                    instructions_content = obj.content
                    break
        
        # Create response based on whether instructions exist
        if instructions_content:
            response = f"Instructions loaded: {instructions_content}\nProcessing: {input_text}"
        else:
            response = f"you said: {input_text}"
            
        output = CoderOutput(
            stdout=response,
            stderr="",
            result_text=response,
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
