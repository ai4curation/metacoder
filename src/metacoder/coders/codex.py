import json
from pathlib import Path
import time
import logging
import shutil
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


class CodexCoder(BaseCoder):
    """
    OpenAI Codex CLI integration.

    Codex-specific configuration:

    You can provide the following files in your configuration directory:

    - `AGENTS.md` - Primary instructions for the assistant
    - `.codex/config.toml` - Configuration including MCP servers

    MCP Support:

    Codex CLI supports MCP (Model Context Protocol) servers through the
    mcp_servers configuration in .codex/config.toml. When MCPs are configured
    through Metacoder, they will be automatically added to the config file.

    The Codex CLI expects MCP servers to be configured in TOML format:

        [mcp_servers.server_name]
        command = "uvx"
        args = ["mcp-server-name"]
        env = { "API_KEY" = "value" }

    Coder Options (passed via coders config in YAML):

        coders:
          codex:
            disable_shell_tool: true  # Disable shell/bash access, MCP-only mode

    Note: Requires codex CLI to be installed.
    """

    # Coder-specific options (set from YAML config)
    disable_shell_tool: bool = False

    @classmethod
    def is_available(cls) -> bool:
        """Check if codex command is available."""
        return shutil.which("codex") is not None

    @classmethod
    def supports_mcp(cls) -> bool:
        """CodexCoder supports MCP extensions."""
        return True

    @classmethod
    def default_config_paths(cls) -> dict[Path, ConfigFileRole]:
        return {
            Path("AGENTS.md"): ConfigFileRole.PRIMARY_INSTRUCTION,
            Path(".codex/config.toml"): ConfigFileRole.CONFIG,
        }

    @property
    def instructions_path(self) -> Path:
        return Path("AGENTS.md")

    def mcp_config_to_codex_format(self, mcp: MCPConfig) -> dict[str, Any]:
        """Convert MCPConfig to Codex's MCP server format."""
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
                "HTTP MCPs are not supported for Codex wrapper yet"
            )

        return server_config

    def _generate_toml_config(self, mcp_servers: dict[str, dict[str, Any]]) -> str:
        """Generate TOML configuration string for Codex config.toml."""
        lines = []

        for server_name, server_config in mcp_servers.items():
            lines.append(f"[mcp_servers.{server_name}]")
            for key, value in server_config.items():
                if key == "command":
                    lines.append(f'command = "{value}"')
                elif key == "args":
                    args_str = ", ".join(f'"{arg}"' for arg in value)
                    lines.append(f"args = [{args_str}]")
                elif key == "env":
                    env_parts = []
                    for env_key, env_val in value.items():
                        env_parts.append(f'"{env_key}" = "{env_val}"')
                    env_str = ", ".join(env_parts)
                    lines.append(f"env = {{ {env_str} }}")
            lines.append("")

        return "\n".join(lines)

    def default_config_objects(self) -> list[CoderConfigObject]:
        """Generate config objects including MCP configuration."""
        config_objects = []

        # Create .codex/config.toml if we have MCP extensions
        if self.config and self.config.extensions:
            mcp_servers = {}
            for mcp in self.config.extensions:
                if mcp.enabled:
                    mcp_servers[mcp.name] = self.mcp_config_to_codex_format(mcp)

            if mcp_servers:
                toml_content = self._generate_toml_config(mcp_servers)
                config_objects.append(
                    CoderConfigObject(
                        file_type=FileType.TEXT,
                        relative_path=".codex/config.toml",
                        content=toml_content,
                    )
                )

        return config_objects

    def run(self, input_text: str) -> CoderOutput:
        """
        Run codex with the given input text.
        """
        env = self.expand_env(self.env)
        self.prepare_workdir()

        with change_directory(self.workdir):
            # Codex reads .codex/config.toml from current directory automatically.
            # Do NOT set HOME=. as this breaks authentication (401 Unauthorized).
            text = self.expand_prompt(input_text)

            # Build command with appropriate flags
            if self.disable_shell_tool:
                # MCP-only mode: disable shell tool to prevent filesystem access
                # This forces Codex to use only MCP tools for retrieving information
                command = [
                    "codex", "exec", "--json", "--full-auto",
                    "--skip-git-repo-check", "--disable", "shell_tool", text
                ]
                logger.info("Running Codex in MCP-only mode (shell_tool disabled)")
            else:
                # Default mode: full access (for general use cases)
                command = ["codex", "exec", "--json", "--dangerously-bypass-approvals-and-sandbox", text]

            print(f"📝 Running command: {' '.join(command)}")
            # time the command
            start_time = time.time()
            ao = self.run_process(command, env)
        # parse the jsonl output
        ao.structured_messages = [
            json.loads(line) for line in ao.stdout.split("\n") if line
        ]
        total_cost_usd = None
        is_error = None
        for message in ao.structured_messages:
            if "total_cost_usd" in message:
                total_cost_usd = message["total_cost_usd"]
            if "is_error" in message:
                is_error = message["is_error"]
            if "result" in message:
                ao.result_text = message["result"]
        end_time = time.time()
        print(f"📝 Command took {end_time - start_time:.2f} seconds")
        ao.total_cost_usd = total_cost_usd
        ao.success = not is_error
        if not ao.success:
            raise ValueError(f"Codex failed with error: {ao.stderr} // {ao}")
        return ao
