from pathlib import Path
import subprocess
import time
import logging
import shutil
import re
from typing import Any

from metacoder.coders.base_coder import (
    BaseCoder,
    CoderConfigObject,
    CoderOutput,
    FileType,
    change_directory,
)
from metacoder.configuration import ConfigFileRole, MCPConfig, MCPType


logger = logging.getLogger(__name__)


class GeminiCoder(BaseCoder):
    """
    Google Gemini AI assistant integration.

    Gemini-specific configuration:

    You can provide the following files in your configuration directory:

    - `GEMINI.md` - Primary instructions for the assistant
    - `.gemini/settings.json` - Configuration including MCP servers
    - `.gemini/commands/` - Custom commands directory

    MCP Support:

    Gemini CLI supports MCP (Model Context Protocol) servers through the
    mcpServers configuration in .gemini/settings.json. When MCPs are configured
    through Metacoder, they will be automatically added to the settings file.

    The Gemini CLI expects MCP servers to be configured in the following format:
    {
        "mcpServers": {
            "server_name": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-name"],
                "env": {"API_KEY": "${API_KEY}"},
                "timeout": 30000
            }
        }
    }

    Note: Requires gemini CLI to be installed (npm install -g @google/gemini-cli).
    """

    @classmethod
    def is_available(cls) -> bool:
        """Check if gemini command is available."""
        return shutil.which("gemini") is not None

    @classmethod
    def supports_mcp(cls) -> bool:
        """GeminiCoder supports MCP extensions."""
        return True

    @classmethod
    def default_config_paths(cls) -> dict[Path, ConfigFileRole]:
        return {
            Path("GEMINI.md"): ConfigFileRole.PRIMARY_INSTRUCTION,
            Path(".gemini/settings.json"): ConfigFileRole.CONFIG,
            Path(".gemini/commands"): ConfigFileRole.CONFIG,
        }

    def mcp_config_to_gemini_format(self, mcp: MCPConfig) -> dict[str, Any]:
        """Convert MCPConfig to Gemini's MCP server format."""
        server_config: dict[str, Any] = {}

        # For stdio type MCPs
        if mcp.type == MCPType.STDIO and mcp.command:
            server_config["command"] = mcp.command
            if mcp.args:
                server_config["args"] = mcp.args
            if mcp.env:
                server_config["env"] = mcp.env
            # Add optional timeout if needed
            server_config["timeout"] = 30000  # 30 seconds default

        # For HTTP type MCPs
        elif mcp.type == MCPType.HTTP:
            raise NotImplementedError("HTTP MCPs are not supported for Gemini CLI yet")

        return server_config

    def default_config_objects(self) -> list[CoderConfigObject]:
        """Generate config objects including MCP configuration."""
        config_objects = []

        # Create .gemini/settings.json if we have MCP extensions
        settings_content: dict[str, Any] = {}

        # Add MCP servers configuration if extensions are present
        if self.config and self.config.extensions:
            mcp_servers = {}
            for mcp in self.config.extensions:
                if mcp.enabled:
                    mcp_servers[mcp.name] = self.mcp_config_to_gemini_format(mcp)

            if mcp_servers:
                settings_content["mcpServers"] = mcp_servers

        # Add settings.json if we have content to write
        if settings_content:
            config_objects.append(
                CoderConfigObject(
                    file_type=FileType.JSON,
                    relative_path=".gemini/settings.json",
                    content=settings_content,
                )
            )

        # Add GEMINI.md if present in config
        # This could contain instructions specific to the task

        return config_objects

    def run(self, input_text: str) -> CoderOutput:
        """
        Run gemini with the given input text.
        """
        env = self.expand_env(self.env)
        self.prepare_workdir()

        with change_directory(self.workdir):
            # Gemini expects HOME to be current directory for config
            env["HOME"] = "."

            text = self.expand_prompt(input_text)

            # Build the command
            # The gemini CLI uses conversational interface, so we need to handle it differently
            # For now, we'll use echo to pipe the prompt
            command = ["sh", "-c", f'echo "{text}" | gemini']

            logger.info("💎 Running command: gemini with prompt")
            logger.debug(f"💎 Full command: {' '.join(command)}")
            start_time = time.time()

            try:
                result = self.run_process(command, env)
            except subprocess.CalledProcessError as e:
                # Capture any error output
                return CoderOutput(
                    stdout=e.stdout if hasattr(e, "stdout") else "",
                    stderr=str(e),
                    result_text=f"Error: {str(e)}",
                    success=False,
                )

            end_time = time.time()
            logger.info(f"💎 Command took {end_time - start_time} seconds")

            # Parse the output
            ao = CoderOutput(stdout=result.stdout, stderr=result.stderr)

            # Parse debug output similar to original
            lines = result.stdout.split("\n")
            blocks = []
            block = {"text": ""}

            for line in lines:
                if line.startswith("[DEBUG]"):
                    if block["text"]:
                        blocks.append(block)
                        block = {"text": ""}

                    # Parse debug lines: [DEBUG] [BfsFileSearch] TEXT
                    m = re.match(r"\[DEBUG\] \[(.*)\] (.*)", line)
                    if m:
                        blocks.append({"debug_type": m.group(1), "text": m.group(2)})
                else:
                    block["text"] += line + "\n"

            if block["text"]:
                blocks.append(block)

            ao.structured_messages = blocks
            ao.result_text = blocks[-1]["text"] if blocks else result.stdout
            ao.success = True

            return ao
