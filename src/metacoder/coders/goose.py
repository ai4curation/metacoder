import json
from pathlib import Path
import subprocess
import time
import logging
import shutil
from typing import Optional, Any

from metacoder.coders.base_coder import BaseCoder, CoderConfigObject, CoderOutput, FileType, change_directory
from metacoder.configuration import MCPConfig, MCPType



logger = logging.getLogger(__name__)

class GooseCoder(BaseCoder):
    """
    Note that running goose involves simulating a home directory in
    the working directory

    For AWS bedrock, you may need to copy ~/.aws/

    """
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if goose command is available."""
        return shutil.which('goose') is not None
    
    @classmethod
    def supports_mcp(cls) -> bool:
        """GooseCoder supports MCP extensions."""
        return True
    
    def instruction_files(self) -> dict[str, str]:
        """Return instruction files as a dictionary of filename to content."""
        return {}
    
    def mcp_config_to_goose_extension(self, mcp: MCPConfig) -> dict:
        """Convert an MCPConfig to Goose extension format."""
        extension = {
            "name": mcp.name,
            "enabled": mcp.enabled,
            "timeout": 300,  # Default timeout
            "type": "stdio" if mcp.type == MCPType.STDIO else mcp.type.value,
        }
        
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

    def default_config_objects(self) -> list[CoderConfigObject]:
        """Generate default config objects including MCP extensions."""
        config_content: dict[str, Any] = {}
        
        # Map AI model configuration to Goose format
        if self.config and self.config.ai_model:
            model = self.config.ai_model
            # Get provider as string
            if isinstance(model.provider, str):
                provider_str = model.provider
            elif model.provider and hasattr(model.provider, 'name'):
                provider_str = model.provider.name
            else:
                provider_str = "openai"  # default
            
            # Map provider names
            if provider_str == "anthropic":
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
        
        return [
            CoderConfigObject(
                file_type=FileType.YAML,
                relative_path=".config/goose/config.yaml",
                content=config_content
            )
        ]
    
    def run(self, input_text: str) -> CoderOutput:
        """
        Run goose with the given input text.
        """
        
        env = self.expand_env(self.env)
        self.prepare_workdir()
        with change_directory(self.workdir):
            # important - ensure that only local config files are used
            # we assue chdir has been called beforehand
            env["HOME"] = "."
            text = self.expand_prompt(input_text)
            command = ["goose", "run", "-t", text]
            logger.info(f"🦆 Running command: {' '.join(command)}")
            # time the command
            start_time = time.time()
            result = self.run_process(command, env)
            end_time = time.time()
            ao = CoderOutput(stdout=result.stdout, stderr=result.stderr)
            print(f"🦆 Command took {end_time - start_time} seconds")
            # look in output text for a file like: logging to ./.local/share/goose/sessions/20250613_120403.jsonl
            session_file: Optional[Path] = None
            for line in result.stdout.split("\n"):
                if "logging to" in line:
                    session_file_str = line.split("logging to ")[1]
                    session_file = Path(session_file_str)
                    break
            if session_file and session_file.exists():
                    with open(session_file, "r") as f:
                        ao.structured_messages = [json.loads(line) for line in f if line.strip()]
            
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
                
            return ao