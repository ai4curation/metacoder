import json
from pathlib import Path
import subprocess
import time

from coders.base_coder import BaseCoder, CoderConfigObject, CoderOutput

class DummyCoder(BaseCoder):
    """
    For testing
    """

    def instruction_files(self) -> dict[str, str]:
        return {
            k: v for k, v in self.file_contents.items() if k.endswith(".dummyhints")
        }
    
    def default_config_objects(self) -> list[CoderConfigObject]:
        return []

    def run(self, input_text: str) -> CoderOutput:
        
        return CoderOutput(stdout="you said: " + input_text, stderr="")