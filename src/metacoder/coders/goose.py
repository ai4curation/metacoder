import json
import os
import platform
from pathlib import Path
import time
import logging
import shutil
from typing import Optional, Any

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


def find_goose() -> Path:
    loc = shutil.which("goose")
    if not loc:
        raise FileNotFoundError("goose not found on PATH")
    return Path(loc).resolve()


def get_home_env_var() -> str:
    """
    Determine the environment variable Goose should treat as "home"
    for locating configuration files.

    Windows:
        Goose expects its configuration under:
            %APPDATA%\\Block\\goose\\config\\
        Therefore, we override APPDATA to point into the working directory.

    Unix-like (Linux, macOS):
        Goose follows the XDG Base Directory spec:
            - If $XDG_CONFIG_HOME is set, config goes under:
                  $XDG_CONFIG_HOME/goose/config.yaml
            - Otherwise it falls back to:
                  $HOME/.config/goose/config.yaml

        We mirror this behavior by checking whether XDG_CONFIG_HOME is set
        in the environment. If it is set, return "XDG_CONFIG_HOME";
        otherwise, return "HOME".

    Returns:
        str: The environment variable name that should be overridden to
             redirect Goose’s config into the working directory.
    """
    if platform.system().lower().startswith("win"):
        return "APPDATA"

    if "XDG_CONFIG_HOME" in os.environ and os.environ["XDG_CONFIG_HOME"]:
        return "XDG_CONFIG_HOME"
    return "HOME"


def get_goose_config_path() -> Path:
    """
    Get the relative config path (from the simulated home directory)
    where Goose expects its configuration, based on the home
    environment variable chosen by get_home_env_var().

    Returns:
        pathlib.Path: The relative config directory path.

    Behavior:
        - If get_home_env_var() == "APPDATA":
            Path -> "Block/goose/config/"
            (matches %APPDATA%\\Block\\goose\\config\\ on Windows)

        - If get_home_env_var() == "HOME":
            Path -> ".config/goose/"
            (matches $HOME/.config/goose/ on Unix-like systems)

        - If get_home_env_var() == "XDG_CONFIG_HOME":
            Path -> "goose/"
            (matches $XDG_CONFIG_HOME/goose/ on Unix-like systems)
    """
    home_env_var = get_home_env_var()

    if home_env_var == "APPDATA":
        return Path("Block/goose/config/")
    elif home_env_var == "HOME":
        return Path(".config/goose/")
    elif home_env_var == "XDG_CONFIG_HOME":
        return Path("goose/")
    else:
        raise RuntimeError(f"Unhandled home env var: {home_env_var}")


class GooseCoder(BaseCoder):
    """
    Note that running goose involves simulating a home directory in
    the working directory

    For AWS bedrock, you may need to copy ~/.aws/

    ```

    """

    @classmethod
    def is_available(cls) -> bool:
        """Check if goose command is available."""
        return shutil.which("goose") is not None

    @classmethod
    def supports_mcp(cls) -> bool:
        """GooseCoder supports MCP extensions."""
        return True

    def mcp_config_to_goose_extension(self, mcp: MCPConfig) -> dict:
        """Convert an MCPConfig to Goose extension format."""
        extension = {
            "name": mcp.name,
            "enabled": mcp.enabled,
            "timeout": 300,  # Default timeout
            "type": "stdio" if mcp.type == MCPType.STDIO else mcp.type.value,
        }

        is_stdio = mcp.type == MCPType.STDIO

        if is_stdio and not mcp.command:
            raise ValueError("STDIO MCP configuration requires 'command'.")

        if mcp.description:
            extension["description"] = mcp.description

        if mcp.command:
            extension["cmd"] = mcp.command

        if mcp.args:
            extension["args"] = mcp.args

        if mcp.env:
            extension["envs"] = mcp.env
            extension["env_keys"] = list(mcp.env.keys())
        else:
            extension["envs"] = {}
            extension["env_keys"] = []

        extension["bundled"] = None

        return extension

    @classmethod
    def default_config_paths(cls) -> dict[Path, ConfigFileRole]:
        return {
            Path(".goosehints"): ConfigFileRole.PRIMARY_INSTRUCTION,
            Path(".settings/goose"): ConfigFileRole.CONFIG,
            Path(".settings/goose/config.yaml"): ConfigFileRole.CONFIG,
        }

    def default_config_objects(self) -> list[CoderConfigObject]:
        """Generate default config objects including MCP extensions."""
        config_content: dict[str, Any] = {}

        # Map AI model configuration to Goose format
        if self.config and self.config.ai_model:
            model = self.config.ai_model
            # Get provider as string
            if isinstance(model.provider, str):
                provider_str = model.provider
            elif model.provider and hasattr(model.provider, "name"):
                provider_str = model.provider.name
            else:
                provider_str = "openai"  # default

            # Map provider names
            if provider_str == "proxy":
                # TODO: this is the proxy route...
                config_content["GOOSE_PROVIDER"] = "openai"
                # Map Anthropic models to their full names
                if "claude" in model.name:
                    config_content["GOOSE_MODEL"] = f"anthropic/{model.name}"
                else:
                    config_content["GOOSE_MODEL"] = model.name
            else:
                config_content["GOOSE_PROVIDER"] = provider_str
                config_content["GOOSE_MODEL"] = model.name
        else:
            # Default values
            config_content["GOOSE_MODEL"] = "gpt-4o"
            config_content["GOOSE_PROVIDER"] = "openai"

        # Start with built-in extensions
        extensions = {
            "developer": {
                "bundled": True,
                "display_name": "Developer",
                "enabled": True,
                "name": "developer",
                "timeout": 300,
                "type": "builtin",
            }
        }

        # Add MCP extensions if configured
        if self.config and self.config.extensions:
            for mcp in self.config.extensions:
                if isinstance(mcp, MCPConfig) and mcp.enabled:
                    extensions[mcp.name] = self.mcp_config_to_goose_extension(mcp)

        config_content["extensions"] = extensions

        cfg_rel = get_goose_config_path() / "config.yaml"

        return [
            CoderConfigObject(
                file_type=FileType.YAML,
                relative_path=str(cfg_rel),
                content=config_content,
            )
        ]

    def run(self, input_text: str) -> CoderOutput:
        """
        Run goose with the given input text.
        """

        env = self.expand_env(self.env)
        self.prepare_workdir()
        with change_directory(self.workdir):
            goose_path = find_goose()
            logger.debug(f"Using goose executable at: {goose_path}")

            # Build environment with redirected config

            # disable keyring (prevents errors on MacOS and Linux)
            env["GOOSE_DISABLE_KEYRING"] = "1"

            # Important:
            # (1) ensure that only local config files are used;
            # (2) assume chdir has been called beforehand.
            cwd = os.getcwd()
            local_home_path = Path(cwd)

            # OS-specific config layout
            home_env_var = get_home_env_var()
            env[home_env_var] = str(local_home_path)

            goose_config_dir = local_home_path / get_goose_config_path()
            goose_cfg_path = goose_config_dir / "config.yaml"
            logger.info(f"Goose home var: {home_env_var} -> {env[home_env_var]}")
            logger.info(f"Goose config (expected at): {goose_cfg_path}")

            text = self.expand_prompt(input_text)
            command = [str(goose_path), "run", "-t", text]
            logger.info(f"🦆 Running command: {' '.join(command)}")
            # time the command
            start_time = time.time()
            result = self.run_process(command, env)
            end_time = time.time()
            ao = CoderOutput(stdout=result.stdout, stderr=result.stderr)
            logger.info(f"🦆 Command took {end_time - start_time:.2f} seconds")
            # look in output text for a file like: logging to ./.local/share/goose/sessions/20250613_120403.jsonl
            session_file: Optional[Path] = None
            for line in result.stdout.split("\n"):
                if "logging to" in line:
                    session_file_str = line.split("logging to ")[1]
                    session_file = Path(session_file_str)
                    break
            if session_file and session_file.exists():
                with open(session_file, "r", encoding="utf-8") as f:
                    ao.structured_messages = [
                        json.loads(line) for line in f if line.strip()
                    ]

            # Extract result text from structured messages
            if ao.structured_messages:
                # Look for assistant messages
                for message in ao.structured_messages:
                    if message.get("role") == "assistant" and "content" in message:
                        for content in message["content"]:
                            if isinstance(content, dict) and "text" in content:
                                if ao.result_text:
                                    ao.result_text += "\n" + content["text"]
                                else:
                                    ao.result_text = content["text"]
                            elif isinstance(content, str):
                                if ao.result_text:
                                    ao.result_text += "\n" + content
                                else:
                                    ao.result_text = content

            # If no result text found in messages, use stdout as fallback
            if not ao.result_text:
                ao.result_text = ao.stdout

            # Extract tool uses from structured messages
            if ao.structured_messages:
                tool_uses = []
                pending_tool_uses = {}  # Map tool request id to tool data

                for message in ao.structured_messages:
                    # Check for tool requests in assistant messages
                    if message.get("role") == "assistant" and "content" in message:
                        for content in message.get("content", []):
                            if (
                                isinstance(content, dict)
                                and content.get("type") == "toolRequest"
                            ):
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
                                        "success": False,  # Default until we see result
                                        "error": None,
                                        "result": None,
                                    }

                    # Check for tool responses in user messages
                    elif message.get("role") == "user" and "content" in message:
                        for content in message.get("content", []):
                            if (
                                isinstance(content, dict)
                                and content.get("type") == "toolResponse"
                            ):
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
                                                    result_texts.append(
                                                        item.get("text", "")
                                                    )
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

                # Add any remaining pending tool uses (shouldn't happen in normal flow)
                for tool_data in pending_tool_uses.values():
                    tool_data["error"] = "No result received for tool call"
                    tool_use = ToolUse(**tool_data)
                    tool_uses.append(tool_use)

                if tool_uses:
                    ao.tool_uses = tool_uses

            return ao
