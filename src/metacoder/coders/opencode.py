import logging
import shutil
import subprocess
import time
from pathlib import Path

from metacoder.coders.base_coder import (
    BaseCoder,
    CoderOutput,
    change_directory,
)
from metacoder.configuration import ConfigFileRole

logger = logging.getLogger(__name__)


class OpencodeCoder(BaseCoder):
    """
    OpenCode.ai AI assistant integration.

    Note: Requires opencode CLI to be installed.
    """

    @classmethod
    def is_available(cls) -> bool:
        """Check if opencode command is available."""
        return shutil.which("opencode") is not None

    @classmethod
    def supports_mcp(cls) -> bool:
        return False

    @classmethod
    def default_config_paths(cls) -> dict[Path, ConfigFileRole]:
        return {
            Path("AGENTS.md"): ConfigFileRole.PRIMARY_INSTRUCTION,
        }

    def run(self, input_text: str) -> CoderOutput:
        """
        Run opencode with the given input text.
        """
        self.prepare_workdir()
        with change_directory(self.workdir):
            command = ["opencode", "run", self.expand_prompt(input_text)]
            if self.params and self.params.get("model"):
                command.extend(["--model", self.params["model"]])

            logger.info(f"Running command: {' '.join(command)}")
            start_time = time.time()

            try:
                result = self.run_process(command)
            except subprocess.CalledProcessError as e:
                return CoderOutput(
                    stdout=e.stdout or "",
                    stderr=str(e),
                    result_text=f"Error: {str(e)}",
                    success=False,
                )

            end_time = time.time()
            logger.info(f"Command took {end_time - start_time:.2f} seconds")

            return CoderOutput(
                stdout=result.stdout,
                stderr=result.stderr,
                result_text=result.stdout,
                success=True,
            )

    def default_config_objects(self):
        return []
