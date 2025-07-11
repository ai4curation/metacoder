import json
from pathlib import Path
import subprocess
import time
import logging

from coders.base_coder import BaseCoder, CoderConfigObject, CoderOutput, FileType, change_directory



logger = logging.getLogger(__name__)

class GooseCoder(BaseCoder):
    """
    Note that running goose involves simulating a home directory in
    the working directory

    For AWS bedrock, you may need to copy ~/.aws/

    """

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
            session_file = None
            for line in result.stdout.split("\n"):
                if "logging to" in line:
                    session_file = line.split("logging to ")[1]
                    break
            if session_file:
                session_file = Path(session_file)
                if session_file.exists():
                    with open(session_file, "r") as f:
                        ao.structured_messages = [json.loads(line) for line in f]
            if ao.structured_messages:
                for message in ao.structured_messages:
                    if "content" in message:
                        for content in message["content"]:
                            if "text" in content:
                                ao.result_text = content["text"]
            if not ao.result_text:
                raise ValueError("No result text found in goose output")
            return ao