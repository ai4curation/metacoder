"""Test GooseCoder tool use extraction."""

from metacoder.coders.base_coder import ToolUse


def test_goose_tool_use_extraction():
    """Test that GooseCoder correctly extracts tool uses from structured messages."""
    # Create a mock output with goose-style tool use in structured messages
    structured_messages = [
        {
            "id": None,
            "role": "assistant",
            "created": 1754353029,
            "content": [
                {
                    "type": "text",
                    "text": "I'll help you find information about diseases associated with ITPR1 mutations.",
                },
                {
                    "type": "toolRequest",
                    "id": "toolu_01RbESTBH9tyWu9Q9uAVRjja",
                    "toolCall": {
                        "status": "success",
                        "value": {
                            "name": "pubmed__get_paper_fulltext",
                            "arguments": {"pmid": "35743164"},
                        },
                    },
                },
            ],
        },
        {
            "id": None,
            "role": "user",
            "created": 1754353029,
            "content": [
                {
                    "type": "toolResponse",
                    "id": "toolu_01RbESTBH9tyWu9Q9uAVRjja",
                    "toolResult": {
                        "status": "success",
                        "value": [{"type": "text", "text": "Paper content here..."}],
                    },
                }
            ],
        },
    ]

    # Process structured messages to extract tool uses (mimicking goose logic)
    tool_uses = []
    pending_tool_uses = {}

    for message in structured_messages:
        # Check for tool requests in assistant messages
        if message.get("role") == "assistant" and "content" in message:
            for content in message.get("content", []):
                if isinstance(content, dict) and content.get("type") == "toolRequest":
                    tool_id = content.get("id")
                    tool_call = content.get("toolCall", {})

                    if tool_call.get("status") == "success":
                        tool_value = tool_call.get("value", {})
                        tool_name = tool_value.get("name", "")
                        tool_args = tool_value.get("arguments", {})

                        # Store pending tool use
                        pending_tool_uses[tool_id] = {
                            "name": tool_name,
                            "arguments": tool_args,
                            "success": False,
                            "error": None,
                            "result": None,
                        }

        # Check for tool responses in user messages
        elif message.get("role") == "user" and "content" in message:
            for content in message.get("content", []):
                if isinstance(content, dict) and content.get("type") == "toolResponse":
                    tool_id = content.get("id")
                    if tool_id in pending_tool_uses:
                        tool_data = pending_tool_uses[tool_id]
                        tool_result = content.get("toolResult", {})

                        # Update with result
                        if tool_result.get("status") == "success":
                            tool_data["success"] = True
                            # Extract text from value array
                            result_value = tool_result.get("value", [])
                            if isinstance(result_value, list):
                                result_texts = []
                                for item in result_value:
                                    if (
                                        isinstance(item, dict)
                                        and item.get("type") == "text"
                                    ):
                                        result_texts.append(item.get("text", ""))
                                tool_data["result"] = (
                                    "\n".join(result_texts)
                                    if result_texts
                                    else str(result_value)
                                )
                            else:
                                tool_data["result"] = str(result_value)
                        else:
                            tool_data["success"] = False
                            tool_data["error"] = tool_result.get(
                                "error", "Tool execution failed"
                            )
                            tool_data["result"] = None

                        # Create ToolUse object
                        tool_use = ToolUse(**tool_data)
                        tool_uses.append(tool_use)

                        # Remove from pending
                        del pending_tool_uses[tool_id]

    # Verify extraction
    assert len(tool_uses) == 1
    tool_use = tool_uses[0]
    assert tool_use.name == "pubmed__get_paper_fulltext"
    assert tool_use.arguments == {"pmid": "35743164"}
    assert tool_use.success is True
    assert tool_use.error is None
    assert tool_use.result == "Paper content here..."


def test_goose_tool_use_error():
    """Test that GooseCoder correctly handles tool errors."""
    # Create a mock output with tool error
    structured_messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "toolRequest",
                    "id": "toolu_test",
                    "toolCall": {
                        "status": "success",
                        "value": {"name": "test_tool", "arguments": {"param": "value"}},
                    },
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "toolResponse",
                    "id": "toolu_test",
                    "toolResult": {
                        "status": "error",
                        "error": "Tool failed to execute",
                    },
                }
            ],
        },
    ]

    # Process structured messages to extract tool uses
    tool_uses = []
    pending_tool_uses = {}

    for message in structured_messages:
        if message.get("role") == "assistant" and "content" in message:
            for content in message.get("content", []):
                if isinstance(content, dict) and content.get("type") == "toolRequest":
                    tool_id = content.get("id")
                    tool_call = content.get("toolCall", {})

                    if tool_call.get("status") == "success":
                        tool_value = tool_call.get("value", {})
                        tool_name = tool_value.get("name", "")
                        tool_args = tool_value.get("arguments", {})

                        pending_tool_uses[tool_id] = {
                            "name": tool_name,
                            "arguments": tool_args,
                            "success": False,
                            "error": None,
                            "result": None,
                        }

        elif message.get("role") == "user" and "content" in message:
            for content in message.get("content", []):
                if isinstance(content, dict) and content.get("type") == "toolResponse":
                    tool_id = content.get("id")
                    if tool_id in pending_tool_uses:
                        tool_data = pending_tool_uses[tool_id]
                        tool_result = content.get("toolResult", {})

                        if tool_result.get("status") == "success":
                            tool_data["success"] = True
                            result_value = tool_result.get("value", [])
                            if isinstance(result_value, list):
                                result_texts = []
                                for item in result_value:
                                    if (
                                        isinstance(item, dict)
                                        and item.get("type") == "text"
                                    ):
                                        result_texts.append(item.get("text", ""))
                                tool_data["result"] = (
                                    "\n".join(result_texts)
                                    if result_texts
                                    else str(result_value)
                                )
                            else:
                                tool_data["result"] = str(result_value)
                        else:
                            tool_data["success"] = False
                            tool_data["error"] = tool_result.get(
                                "error", "Tool execution failed"
                            )
                            tool_data["result"] = None

                        tool_use = ToolUse(**tool_data)
                        tool_uses.append(tool_use)
                        del pending_tool_uses[tool_id]

    # Verify error handling
    assert len(tool_uses) == 1
    tool_use = tool_uses[0]
    assert tool_use.name == "test_tool"
    assert tool_use.arguments == {"param": "value"}
    assert tool_use.success is False
    assert tool_use.error == "Tool failed to execute"
    assert tool_use.result is None


def test_goose_multiple_tools():
    """Test that GooseCoder correctly handles multiple tool uses."""
    structured_messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "toolRequest",
                    "id": "tool1",
                    "toolCall": {
                        "status": "success",
                        "value": {
                            "name": "search_tool",
                            "arguments": {"query": "test"},
                        },
                    },
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "toolResponse",
                    "id": "tool1",
                    "toolResult": {
                        "status": "success",
                        "value": [{"type": "text", "text": "Search results"}],
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "toolRequest",
                    "id": "tool2",
                    "toolCall": {
                        "status": "success",
                        "value": {
                            "name": "fetch_tool",
                            "arguments": {"url": "http://example.com"},
                        },
                    },
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "toolResponse",
                    "id": "tool2",
                    "toolResult": {
                        "status": "success",
                        "value": [{"type": "text", "text": "Fetched content"}],
                    },
                }
            ],
        },
    ]

    # Process structured messages
    tool_uses = []
    pending_tool_uses = {}

    for message in structured_messages:
        if message.get("role") == "assistant" and "content" in message:
            for content in message.get("content", []):
                if isinstance(content, dict) and content.get("type") == "toolRequest":
                    tool_id = content.get("id")
                    tool_call = content.get("toolCall", {})

                    if tool_call.get("status") == "success":
                        tool_value = tool_call.get("value", {})
                        pending_tool_uses[tool_id] = {
                            "name": tool_value.get("name", ""),
                            "arguments": tool_value.get("arguments", {}),
                            "success": False,
                            "error": None,
                            "result": None,
                        }

        elif message.get("role") == "user" and "content" in message:
            for content in message.get("content", []):
                if isinstance(content, dict) and content.get("type") == "toolResponse":
                    tool_id = content.get("id")
                    if tool_id in pending_tool_uses:
                        tool_data = pending_tool_uses[tool_id]
                        tool_result = content.get("toolResult", {})

                        if tool_result.get("status") == "success":
                            tool_data["success"] = True
                            result_value = tool_result.get("value", [])
                            if isinstance(result_value, list):
                                result_texts = []
                                for item in result_value:
                                    if (
                                        isinstance(item, dict)
                                        and item.get("type") == "text"
                                    ):
                                        result_texts.append(item.get("text", ""))
                                tool_data["result"] = (
                                    "\n".join(result_texts)
                                    if result_texts
                                    else str(result_value)
                                )
                            else:
                                tool_data["result"] = str(result_value)

                        tool_uses.append(ToolUse(**tool_data))
                        del pending_tool_uses[tool_id]

    # Verify multiple tools
    assert len(tool_uses) == 2
    assert tool_uses[0].name == "search_tool"
    assert tool_uses[0].success is True
    assert tool_uses[0].result == "Search results"
    assert tool_uses[1].name == "fetch_tool"
    assert tool_uses[1].success is True
    assert tool_uses[1].result == "Fetched content"
