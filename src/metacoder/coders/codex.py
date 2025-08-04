import json
from pathlib import Path
import subprocess
import time
import logging
import shutil

from metacoder.coders.base_coder import BaseCoder, CoderConfigObject, CoderOutput, FileType, change_directory



logger = logging.getLogger(__name__)

class CodexCoder(BaseCoder):
    """
    For AWS bedrock, you may need to copy ~/.aws/

    """
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if codex command is available."""
        return shutil.which('codex') is not None
    
    def instruction_files(self) -> dict[str, str]:
        """Return instruction files as a dictionary of filename to content."""
        return {}

    @property
    def instructions_path(self) -> Path:
        return Path("AGENTS.md")

    def default_config_objects(self) -> list[CoderConfigObject]:
        """
        extensions:
            developer:
                bundled: true
                display_name: Developer
                enabled: true
                name: developer
                timeout: 300
                type: builtin
            pdfreader:
                args:
                - mcp-read-pdf
                bundled: null
                cmd: uvx
                description: Read large and complex PDF documents
                enabled: true
                env_keys: []
                envs: {}
                name: pdfreader
                timeout: 300
                type: stdio
        """
        return [
            CoderConfigObject(
                file_type=FileType.YAML,
                relative_path=".config/goose/config.yaml",
                content={
                    "GOOSE_MODEL": "gpt-4o",
                    "GOOSE_PROVIDER": "openai",
                    "extensions": {
                        "developer": {
                            "bundled": True,
                            "display_name": "Developer",
                            "enabled": True,
                            "name": "developer",
                            "timeout": 300,
                            "type": "builtin",
                        },
                        "pdfreader": {
                            "args": ["mcp-read-pdf"],
                            "bundled": None,
                            "cmd": "uvx",
                            "description": "Read large and complex PDF documents",
                            "enabled": True,
                            "env_keys": [],
                            "envs": {},
                            "name": "pdfreader",
                            "timeout": 300,
                            "type": "stdio",
                        }
                    }
                }
            )
        ]
    
    def run(self, input_text: str) -> CoderOutput:
        """
        Run claude code with the given input text.
        """
        env = self.expand_env(self.env)
        # important - ensure that only local config files are used
        # we assue chdir has been called beforehand
        env["HOME"] = "."
        text = self.expand_prompt(input_text)
        command = ["claude", "-p", "--verbose", "--output-format", "stream-json", text]

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