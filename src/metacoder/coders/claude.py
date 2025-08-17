import json
from pathlib import Path
import time
import logging
import shutil
import subprocess
from typing import Any

from metacoder.coders.base_coder import (
    BaseCoder,
    CoderConfigObject,
    CoderOutput,
    FileType,
    ToolUse,
    change_directory,
)
from metacoder.configuration import ConfigFileRole, MCPConfig, MCPType


logger = logging.getLogger(__name__)


class ClaudeCoder(BaseCoder):
    """
    Runs claude code over a task.

    Claude-specific configuration:

    You can provide the following files in your configuration directory:

    - `CLAUDE.md`
    - `.claude.json``
    - `.claude/settings.json`

    For AWS bedrock, you may need to copy or symlink your ~/.aws/ credentials to `.aws/` in
    the configuration directory.

    Outputs:

    - includes `total_cost_usd` in the structured messages
    - includes `tool_uses` with parsed tool invocations and their results

    TODO: support sub-agents

    """

    @classmethod
    def is_available(cls) -> bool:
        """Check if claude command is available."""
        return shutil.which("claude") is not None

    @classmethod
    def supports_mcp(cls) -> bool:
        """ClaudeCoder supports MCP extensions."""
        return True

    @classmethod
    def default_config_paths(cls) -> dict[Path, ConfigFileRole]:
        return {
            Path("CLAUDE.md"): ConfigFileRole.PRIMARY_INSTRUCTION,
            Path(".claude.json"): ConfigFileRole.CONFIG,
            Path(".mcp.json"): ConfigFileRole.CONFIG,
            Path(".claude"): ConfigFileRole.CONFIG,
            Path(".claude/settings.json"): ConfigFileRole.CONFIG,
            Path(".claude/agents"): ConfigFileRole.AGENTS,
        }

    def mcp_config_to_claude_format(self, mcp: MCPConfig) -> dict[str, Any]:
        """Convert MCPConfig to Claude's MCP server format."""
        server_config: dict[str, Any] = {}

        # For stdio type MCPs
        if mcp.type == MCPType.STDIO and mcp.command:
            server_config["command"] = mcp.command
            if mcp.args:
                server_config["args"] = mcp.args
            if mcp.env:
                server_config["env"] = mcp.env

        # For HTTP type MCPs
        elif mcp.type == MCPType.HTTP:
            raise NotImplementedError(
                "HTTP MCPs are not supported for this wrapper yet"
            )

        return server_config

    def default_config_objects(self) -> list[CoderConfigObject]:
        """Generate config objects including MCP configuration."""
        config_objects = []

        # Create .mcp.json if we have MCP extensions
        if self.config and self.config.extensions:
            mcp_servers = {}
            for mcp in self.config.extensions:
                if mcp.enabled:
                    mcp_servers[mcp.name] = self.mcp_config_to_claude_format(mcp)

            if mcp_servers:
                # copy MCP configs to .mcp.json
                config_objects.append(
                    CoderConfigObject(
                        file_type=FileType.JSON,
                        relative_path=".mcp.json",
                        content={"mcpServers": mcp_servers},
                    )
                )

        # Add any default instruction files
        # CLAUDE.md can be added here if needed

        return config_objects

    def run(self, input_text: str) -> CoderOutput:
        """
        Run claude code with the given input text.
        """
        env = self.expand_env(self.env)
        self.prepare_workdir()

        with change_directory(self.workdir):
            # important - ensure that only local config files are used
            env["HOME"] = "."
            text = self.expand_prompt(input_text)
            logger.debug(f"🤖 Running claude with input: {text}")

            danger = False
            extra_options = []
            if self.config and self.config.extensions:
                extra_options.append("--mcp-config")
                extra_options.append(".mcp.json")
                danger = True

            if danger:
                extra_options.append("--dangerously-skip-permissions")

            command = [
                "claude",
                "-p",
                "--verbose",
                "--output-format",
                "stream-json",
            ]
            command.extend(extra_options)
            command.append(text)

            logger.info(f"🤖 Running command: {' '.join(command)}")
            # time the command
            start_time = time.time()
            
            # Catch CalledProcessError to handle Claude CLI non-zero exit codes
            # Claude CLI can return non-zero exit codes even for successful operations
            try:
                ao = self.run_process(command, env)
            except subprocess.CalledProcessError as e:
                # Extract stdout and stderr from the exception
                stdout_text = e.stdout if e.stdout else ""
                stderr_text = e.stderr if e.stderr else ""
                # Create CoderOutput manually so we can process the JSON output
                ao = CoderOutput(stdout=stdout_text, stderr=stderr_text)

            # parse the jsonl output
            def parse_jsonl_line(text: str) -> dict[str, Any]:
                try:
                    result: dict[str, Any] = json.loads(text)
                    return result
                except json.JSONDecodeError:
                    return {"original": text, "error": "JSONDecodeError"}

            ao.structured_messages = [
                parse_jsonl_line(line) for line in ao.stdout.split("\n") if line
            ]
            ao.structured_messages = [
                m for m in ao.structured_messages if m is not None
            ]
            total_cost_usd = None
            is_error = None

            # Extract tool uses
            tool_uses = []
            pending_tool_uses = {}  # Map tool_use_id to tool data

            for message in ao.structured_messages:
                if "total_cost_usd" in message:
                    total_cost_usd = message["total_cost_usd"]
                if "is_error" in message:
                    is_error = message["is_error"]
                if "result" in message:
                    ao.result_text = message["result"]

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
                                    "success": False,  # Default to False until we see result
                                    "error": None,
                                    "result": None,
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
                                    tool_data["result"] = content_item.get(
                                        "content", ""
                                    )

                                    if is_tool_error:
                                        tool_data["error"] = content_item.get(
                                            "content", "Tool error occurred"
                                        )

                                    # Create ToolUse object
                                    tool_use = ToolUse(**tool_data)
                                    tool_uses.append(tool_use)

                                    # Remove from pending
                                    del pending_tool_uses[tool_id]

            # Add any remaining pending tool uses (shouldn't happen in normal flow)
            for tool_data in pending_tool_uses.values():
                tool_data["error"] = "No result received for tool call"
                tool_use = ToolUse(**tool_data)
                tool_uses.append(tool_use)

            if tool_uses:
                ao.tool_uses = tool_uses

            end_time = time.time()
            logger.info(f"🤖 Command took {end_time - start_time} seconds")
            ao.total_cost_usd = total_cost_usd
            ao.success = not is_error
            if not ao.success:
                raise ValueError(f"Claude failed with error: {ao.stderr} // {ao}")
            return ao
