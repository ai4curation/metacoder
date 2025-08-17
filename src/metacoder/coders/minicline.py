import logging
import os
import sys
import time
from io import StringIO
from typing import Any

from metacoder.coders.base_coder import (
    BaseCoder,
    CoderConfigObject,
    CoderOutput,
    change_directory,
)

logger = logging.getLogger(__name__)


class MiniclineCoder(BaseCoder):
    """
    Minicline AI assistant integration using direct Python API.
    
    Minicline is a lightweight, secure AI coding assistant that runs code
    in containerized environments by default.
    
    Requires:
    - minicline package to be installed: pip install minicline
    - OPENROUTER_API_KEY environment variable
    
    Environment variables:
    - OPENROUTER_API_KEY (required): API key for OpenRouter
    - MINICLINE_MODEL (optional): Model to use (defaults to openai/gpt-4.1-mini)
    
    Note: Minicline does not support MCP extensions.
    """

    @classmethod
    def is_available(cls) -> bool:
        """Check if minicline package is available."""
        try:
            import minicline  # noqa: F401
            return True
        except ImportError:
            return False

    @classmethod
    def supports_mcp(cls) -> bool:
        """Minicline does not support MCP extensions."""
        return False

    def default_config_objects(self) -> list[CoderConfigObject]:
        """Default configuration for Minicline."""
        # Minicline doesn't need config files in workdir
        # It uses environment variables and direct API calls
        return []

    def run(self, input_text: str) -> CoderOutput:
        """
        Run minicline with the given input text.
        """
        env = self.expand_env(self.env)
        self.prepare_workdir()

        with change_directory(self.workdir):
            # Validate required environment variables
            api_key = env.get("OPENROUTER_API_KEY")
            if not api_key:
                # Check if it's in the regular environment
                api_key = os.environ.get("OPENROUTER_API_KEY")
                if not api_key:
                    raise ValueError(
                        "OPENROUTER_API_KEY environment variable is required"
                    )

            # Get model from environment or use default
            model = env.get("MINICLINE_MODEL", "openai/gpt-4.1-mini")

            text = self.expand_prompt(input_text)
            logger.info(f"🤖 Running minicline with model: {model}")
            
            start_time = time.time()
            
            try:
                # Import minicline here to allow for dynamic availability checking
                from minicline import perform_task
                
                # We'll capture stdout/stderr by temporarily redirecting them
                
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                stdout_capture = StringIO()
                stderr_capture = StringIO()
                
                try:
                    sys.stdout = stdout_capture
                    sys.stderr = stderr_capture
                    
                    # Set environment variable for minicline
                    os.environ["OPENROUTER_API_KEY"] = api_key
                    
                    # Call minicline with the correct API
                    result = perform_task(
                        instructions=text,
                        cwd=".",  # Use current working directory
                        model=model,
                        auto=True,  # Enable automatic mode for non-interactive use
                    )
                    
                    success = True
                    result_text = str(result) if result else ""
                    
                except Exception as e:
                    success = False
                    result_text = f"Error: {str(e)}"
                    logger.error(f"Minicline execution failed: {e}")
                
                finally:
                    # Restore stdout/stderr
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
                
                stdout_text = stdout_capture.getvalue()
                stderr_text = stderr_capture.getvalue()
                
            except ImportError as e:
                return CoderOutput(
                    stdout="",
                    stderr=f"Failed to import minicline: {e}",
                    result_text="Error: minicline package not available",
                    success=False,
                )
            except Exception as e:
                return CoderOutput(
                    stdout="",
                    stderr=str(e),
                    result_text=f"Error: {str(e)}",
                    success=False,
                )

            end_time = time.time()
            logger.info(f"🤖 Minicline execution took {end_time - start_time} seconds")

            # Create output - Minicline provides direct Python API results
            ao = CoderOutput(
                stdout=stdout_text,
                stderr=stderr_text,
                result_text=result_text,
                success=success,
                total_cost_usd=None,  # No cost information available
                structured_messages=[],  # No structured messages from direct API
            )

            return ao