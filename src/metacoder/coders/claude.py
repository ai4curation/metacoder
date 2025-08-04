import json
from pathlib import Path
import subprocess
import time
import logging
import shutil
from typing import Any

from metacoder.coders.base_coder import BaseCoder, CoderConfigObject, CoderOutput, FileType, change_directory
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

    """
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if claude command is available."""
        return shutil.which('claude') is not None
    
    @classmethod
    def supports_mcp(cls) -> bool:
        """ClaudeCoder supports MCP extensions."""
        return True
    
    def instruction_files(self) -> dict[str, str]:
        """Return instruction files as a dictionary of filename to content."""
        return {}
    
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
            raise NotImplementedError("HTTP MCPs are not supported for this wrapper yet")
            
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
                        content={
                            "mcpServers": mcp_servers
                        }
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
                "-p", "--verbose", 
                "--output-format", "stream-json",
            ]
            command.extend(extra_options)
            command.append(text)

            print(f"🤖 Running command: {' '.join(command)}")
            # time the command
            start_time = time.time()
            ao = self.run_process(command, env)
            # parse the jsonl output
            ao.structured_messages = [json.loads(line) for line in ao.stdout.split("\n") if line]
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
            print(f"🤖 Command took {end_time - start_time} seconds")
            ao.total_cost_usd = total_cost_usd
            ao.success = not is_error
            if not ao.success:
                raise ValueError(f"Claude failed with error: {ao.stderr} // {ao}")
            return ao