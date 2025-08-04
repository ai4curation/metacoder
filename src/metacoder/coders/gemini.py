import json
from pathlib import Path
import subprocess
import time
import logging
import shutil
import re

from metacoder.coders.base_coder import BaseCoder, CoderConfigObject, CoderOutput, FileType, change_directory


logger = logging.getLogger(__name__)


class GeminiCoder(BaseCoder):
    """
    Google Gemini AI assistant integration.
    
    Note: Requires gemini CLI to be installed.
    """
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if gemini command is available."""
        return shutil.which('gemini') is not None
    
    def instruction_files(self) -> dict[str, str]:
        """Return instruction files as a dictionary of filename to content."""
        return {}
    
    def default_config_objects(self) -> list[CoderConfigObject]:
        """Default configuration for Gemini."""
        return [
            CoderConfigObject(
                file_type=FileType.YAML,
                relative_path=".codex/config.yaml",
                content={
                    "model": "gemini-2.5-pro",
                    "provider": "google"
                }
            )
        ]
    
    def run(self, input_text: str) -> CoderOutput:
        """
        Run gemini with the given input text.
        """
        env = self.expand_env(self.env)
        self.prepare_workdir()
        
        with change_directory(self.workdir):
            # Gemini expects HOME to be current directory for config
            env["HOME"] = "."
            
            # Validate required files
            if not Path("./.codex/config.yaml").exists():
                raise ValueError("Codex config.yaml file not found")
            
            text = self.expand_prompt(input_text)
            command = ["gemini", "-d", "-m", "gemini-2.5-pro", "-y", "-p", text]
            
            logger.info(f"🤖 Running command: {' '.join(command)}")
            start_time = time.time()
            
            try:
                result = self.run_process(command, env)
            except subprocess.CalledProcessError as e:
                # Capture any error output
                return CoderOutput(
                    stdout=e.stdout if hasattr(e, 'stdout') else "",
                    stderr=str(e),
                    result_text=f"Error: {str(e)}",
                    success=False
                )
            
            end_time = time.time()
            print(f"🤖 Command took {end_time - start_time} seconds")
            
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