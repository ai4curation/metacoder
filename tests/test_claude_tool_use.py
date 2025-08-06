"""Test ClaudeCoder tool use extraction."""
from metacoder.coders.base_coder import CoderOutput, ToolUse


def test_claude_tool_use_extraction():
    """Test that ClaudeCoder correctly extracts tool uses from structured messages."""
    
    # Create a mock output with tool use in structured messages
    output = CoderOutput(
        stdout="",
        stderr="",
        structured_messages=[
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "toolu_019mJqdgpJSP1Z6UcfsMhx7s",
                            "name": "mcp__pubmed__get_paper_fulltext",
                            "input": {"pmid": "35743164"}
                        }
                    ]
                }
            },
            {
                "type": "user", 
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "content": "Paper content here...",
                            "is_error": False,
                            "tool_use_id": "toolu_019mJqdgpJSP1Z6UcfsMhx7s"
                        }
                    ]
                }
            }
        ]
    )
    
    # Process structured messages to extract tool uses
    tool_uses = []
    pending_tool_uses = {}
    
    for message in output.structured_messages:
        # Check for tool_use in assistant messages
        if message.get("type") == "assistant" and message.get("message"):
            msg_content = message["message"].get("content", [])
            if isinstance(msg_content, list):
                for content_item in msg_content:
                    if content_item.get("type") == "tool_use":
                        tool_id = content_item.get("id")
                        tool_name = content_item.get("name", "")
                        tool_input = content_item.get("input", {})
                        
                        # Store pending tool use
                        pending_tool_uses[tool_id] = {
                            "name": tool_name,
                            "arguments": tool_input,
                            "success": False,
                            "error": None,
                            "result": None
                        }
        
        # Check for tool_result in user messages
        elif message.get("type") == "user" and message.get("message"):
            msg_content = message["message"].get("content", [])
            if isinstance(msg_content, list):
                for content_item in msg_content:
                    if content_item.get("type") == "tool_result":
                        tool_id = content_item.get("tool_use_id")
                        if tool_id in pending_tool_uses:
                            tool_data = pending_tool_uses[tool_id]
                            
                            # Update with result
                            is_tool_error = content_item.get("is_error", False)
                            tool_data["success"] = not is_tool_error
                            tool_data["result"] = content_item.get("content", "")
                            
                            if is_tool_error:
                                tool_data["error"] = content_item.get("content", "Tool error occurred")
                            
                            # Create ToolUse object
                            tool_use = ToolUse(**tool_data)
                            tool_uses.append(tool_use)
                            
                            # Remove from pending
                            del pending_tool_uses[tool_id]
    
    # Verify extraction
    assert len(tool_uses) == 1
    tool_use = tool_uses[0]
    assert tool_use.name == "mcp__pubmed__get_paper_fulltext"
    assert tool_use.arguments == {"pmid": "35743164"}
    assert tool_use.success is True
    assert tool_use.error is None
    assert tool_use.result == "Paper content here..."


def test_claude_tool_use_error():
    """Test that ClaudeCoder correctly handles tool errors."""
    
    # Create a mock output with tool error
    output = CoderOutput(
        stdout="",
        stderr="",
        structured_messages=[
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "toolu_test",
                            "name": "mcp__pubmed__get_paper_fulltext",
                            "input": {"pmid": "invalid"}
                        }
                    ]
                }
            },
            {
                "type": "user", 
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "content": "MCP tool response exceeds maximum allowed tokens",
                            "is_error": True,
                            "tool_use_id": "toolu_test"
                        }
                    ]
                }
            }
        ]
    )
    
    # Process structured messages to extract tool uses
    tool_uses = []
    pending_tool_uses = {}
    
    for message in output.structured_messages:
        # Check for tool_use in assistant messages
        if message.get("type") == "assistant" and message.get("message"):
            msg_content = message["message"].get("content", [])
            if isinstance(msg_content, list):
                for content_item in msg_content:
                    if content_item.get("type") == "tool_use":
                        tool_id = content_item.get("id")
                        tool_name = content_item.get("name", "")
                        tool_input = content_item.get("input", {})
                        
                        # Store pending tool use
                        pending_tool_uses[tool_id] = {
                            "name": tool_name,
                            "arguments": tool_input,
                            "success": False,
                            "error": None,
                            "result": None
                        }
        
        # Check for tool_result in user messages
        elif message.get("type") == "user" and message.get("message"):
            msg_content = message["message"].get("content", [])
            if isinstance(msg_content, list):
                for content_item in msg_content:
                    if content_item.get("type") == "tool_result":
                        tool_id = content_item.get("tool_use_id")
                        if tool_id in pending_tool_uses:
                            tool_data = pending_tool_uses[tool_id]
                            
                            # Update with result
                            is_tool_error = content_item.get("is_error", False)
                            tool_data["success"] = not is_tool_error
                            tool_data["result"] = content_item.get("content", "")
                            
                            if is_tool_error:
                                tool_data["error"] = content_item.get("content", "Tool error occurred")
                            
                            # Create ToolUse object
                            tool_use = ToolUse(**tool_data)
                            tool_uses.append(tool_use)
                            
                            # Remove from pending
                            del pending_tool_uses[tool_id]
    
    # Verify error handling
    assert len(tool_uses) == 1
    tool_use = tool_uses[0]
    assert tool_use.name == "mcp__pubmed__get_paper_fulltext"
    assert tool_use.arguments == {"pmid": "invalid"}
    assert tool_use.success is False
    assert tool_use.error == "MCP tool response exceeds maximum allowed tokens"
    assert tool_use.result == "MCP tool response exceeds maximum allowed tokens"