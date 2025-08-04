import subprocess
import time
import logging
import shutil
import os

from metacoder.coders.base_coder import (
    BaseCoder,
    CoderConfigObject,
    CoderOutput,
    change_directory,
)


logger = logging.getLogger(__name__)


class QwenCoder(BaseCoder):
    """
    Qwen AI assistant integration via qwen-code CLI.

    Requires the @qwen-code/qwen-code npm package to be installed globally:
    npm i -g @qwen-code/qwen-code

    Environment variables needed:
    - OPENAI_API_KEY (set to your DASHSCOPE_API_KEY)
    - OPENAI_BASE_URL (defaults to https://dashscope-intl.aliyuncs.com/compatible-mode/v1)
    - OPENAI_MODEL (defaults to qwen3-coder-plus)
    """

    @classmethod
    def is_available(cls) -> bool:
        """Check if qwen command is available."""
        return shutil.which("qwen") is not None

    def instruction_files(self) -> dict[str, str]:
        """Return instruction files as a dictionary of filename to content."""
        return {}

    def default_config_objects(self) -> list[CoderConfigObject]:
        """Default configuration for Qwen."""
        # Qwen doesn't need config files in workdir like Gemini
        # It uses environment variables instead
        return []

    def run(self, input_text: str) -> CoderOutput:
        """
        Run qwen with the given input text.
        """
        env = self.expand_env(self.env)
        self.prepare_workdir()

        with change_directory(self.workdir):
            # Set default values if not provided
            if "OPENAI_BASE_URL" not in env:
                env["OPENAI_BASE_URL"] = (
                    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
                )
            if "OPENAI_MODEL" not in env:
                env["OPENAI_MODEL"] = "qwen3-coder-plus"

            # Validate required environment variables
            if not env.get("OPENAI_API_KEY"):
                # Check if it's in the regular environment
                if "DASHSCOPE_API_KEY" in os.environ:
                    env["OPENAI_API_KEY"] = os.environ["DASHSCOPE_API_KEY"]
                else:
                    raise ValueError(
                        "OPENAI_API_KEY environment variable is required "
                        "(set to your DASHSCOPE_API_KEY)"
                    )

            text = self.expand_prompt(input_text)
            command = ["qwen", "-p", text]

            logger.info("🤖 Running command: qwen -p <prompt>")
            start_time = time.time()

            try:
                result = self.run_process(command, env)
            except subprocess.CalledProcessError as e:
                # Capture any error output
                stdout = ""
                stderr = str(e)
                if hasattr(e, "stdout") and e.stdout:
                    stdout = e.stdout
                if hasattr(e, "stderr") and e.stderr:
                    stderr = e.stderr
                return CoderOutput(
                    stdout=stdout,
                    stderr=stderr,
                    result_text=f"Error: {str(e)}",
                    success=False,
                )

            end_time = time.time()
            print(f"🤖 Command took {end_time - start_time} seconds")

            # Create output - Qwen CLI doesn't provide structured output
            ao = CoderOutput(
                stdout=result.stdout,
                stderr=result.stderr,
                result_text=result.stdout,  # The entire stdout is the result
                success=True,
                total_cost_usd=None,  # No cost information from CLI
                structured_messages=[],  # No structured messages from CLI
            )

            return ao
