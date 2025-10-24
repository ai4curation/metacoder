import logging
import os
import shutil
from pathlib import Path
from typing import Any

from metacoder.coders.base_coder import (
    BaseCoder,
    CoderConfigObject,
    CoderOutput,
    change_directory,
)
from metacoder.configuration import ConfigFileRole


logger = logging.getLogger(__name__)


class MiniclineCoder(BaseCoder):
    """
    Runs minicline over a task.

    Minicline is a lightweight, secure command-line interface for AI coding
    tasks via OpenRouter API. It provides containerized execution by default
    for enhanced security.

    Configuration:
    - Requires OPENROUTER_API_KEY environment variable
    - Optional model parameter (defaults to openai/gpt-4.1-mini)
    - Uses Docker for containerized execution

    Note: Minicline does not support MCP extensions.
    """

    model: str = "openai/gpt-4.1-mini"

    @classmethod
    def is_available(cls) -> bool:
        """Check if minicline is available."""
        try:
            import minicline  # noqa: F401
            return True
        except ImportError:
            return False

    @classmethod
    def supports_mcp(cls) -> bool:
        """MiniclineCoder does not support MCP extensions."""
        return False

    @classmethod
    def default_config_paths(cls) -> dict[Path, ConfigFileRole]:
        return {
            Path("MINICLINE.md"): ConfigFileRole.PRIMARY_INSTRUCTION,
        }

    def default_config_objects(self) -> list[CoderConfigObject]:
        """Default config objects for MiniclineCoder."""
        return []

    def run(self, input_text: str) -> CoderOutput:
        """
        Run minicline with the given input text.
        """
        if not self.is_available():
            raise ImportError(
                "minicline is not installed. Install it with: pip install minicline"
            )

        try:
            from minicline import perform_task
        except ImportError as e:
            raise ImportError(
                f"Failed to import minicline: {e}. Install it with: pip install minicline"
            )

        # Check for required environment variable
        env = self.expand_env(self.env)
        if "OPENROUTER_API_KEY" not in env:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable is required for minicline. "
                "Set it in your environment or pass it via the env parameter."
            )

        self.prepare_workdir()

        with change_directory(self.workdir):
            text = self.expand_prompt(input_text)
            logger.debug(f"🤖 Running minicline with input: {text}")

            # Determine model to use
            model = self.model
            if self.params and "model" in self.params:
                model = self.params["model"]

            logger.info(f"🤖 Running minicline with model: {model}")
            logger.info(f"🤖 Working directory: {os.getcwd()}")

            try:
                # Set environment for the subprocess
                original_env = os.environ.copy()
                os.environ.update(env)

                # Run minicline perform_task
                result = perform_task(
                    instructions=text,
                    cwd=os.getcwd(),
                    model=model
                )

                # Restore original environment
                os.environ.clear()
                os.environ.update(original_env)

                # Create CoderOutput from result
                # minicline's perform_task doesn't return structured output,
                # so we'll capture what we can
                output = CoderOutput(
                    stdout=f"Minicline task completed with model {model}",
                    stderr="",
                    result_text=f"Task executed successfully with minicline",
                    success=True,
                )

                logger.info("🤖 Minicline task completed successfully")
                return output

            except Exception as e:
                logger.error(f"🚫 Minicline failed: {e}")
                # Restore original environment in case of error
                os.environ.clear()
                os.environ.update(original_env)

                return CoderOutput(
                    stdout="",
                    stderr=str(e),
                    result_text=None,
                    success=False,
                )