from abc import ABC, abstractmethod
from contextlib import contextmanager
import logging
import os
from pathlib import Path
import subprocess
import sys
import threading
from typing import Any
from pydantic import BaseModel, Field, model_validator

from metacoder.configuration import (
    CoderConfig,
    CoderConfigObject,
    ConfigFileRole,
    FileType,
)

logger = logging.getLogger(__name__)


class ToolUse(BaseModel):
    """Tool use from the coder."""
    name: str = Field(..., description="Name of the tool; e.g. mcp.pubmed.get_paper_fulltext")
    arguments: dict[str, Any] = Field(..., description="Arguments to the tool")
    success: bool = Field(..., description="Whether the tool call was successful")
    error: str | None = Field(default=None, description="Error message if the tool call failed")
    result: Any = Field(..., description="Result of the tool")


class CoderOutput(BaseModel):
    """Base class for coder outputs."""

    stdout: str = Field(..., description="Standard output from the coder")
    stderr: str = Field(..., description="Standard error from the coder")
    result_text: str | None = Field(
        default=None, description="Result text from the coder"
    )
    total_cost_usd: float | None = Field(default=None, description="Total cost in USD")
    success: bool | None = Field(
        default=None, description="Whether the coder ran successfully"
    )
    structured_messages: list[dict] | None = Field(
        default=None, description="Messages from the coder, e.g claude json output"
    )
    tool_uses: list[ToolUse] | None = Field(
        default=None, description="Tool uses from the coder"
    )


LOCK_FILE = ".lock"


@contextmanager
def change_directory(path: str):
    """Context manager to temporarily change directory.

    Creates a lock file in the directory to prevent multiple processes from running in the same directory.
    """
    original_dir = os.getcwd()
    Path(path).mkdir(parents=True, exist_ok=True)
    lock_file = Path(path) / LOCK_FILE
    logger.info(f"🔒 Obtaining lock for {path}; current_dir={original_dir}")
    if lock_file.exists():
        print(
            f"🚫 Lock file {lock_file} exists in {path}. If you are SURE no other process is running in this directory, delete the lock file and try again."
        )
        sys.exit(1)
    # write the current process id to the lock file
    lock_file.write_text(str(os.getpid()))
    try:
        os.chdir(path)
        yield
    finally:
        logger.info(f"🔓 Releasing lock for {path}; current_dir={original_dir}")
        os.chdir(original_dir)
        lock_file.unlink()


class BaseCoder(BaseModel, ABC):
    """
    Base class for all AI coding assistants.

    This class provides a base class for all coders. It provides a common interface for all coders,
    and implements common functionality for all coders.

    Subclasses should implement the following methods:
    - run(self, input_text: str) -> CoderOutput: Run the coder on the input text
    """
    workdir: str = Field(default="workdir", description="Working dir ")
    config: CoderConfig | None = Field(default=None, description="Config for the coder")
    params: dict | None = Field(default=None, description="Parameters for the coder")
    env: dict[str, str] | None = Field(
        default=None, description="Environment variables for the coder"
    )
    prompt: str | None = Field(default=None, description="Prompt for the coder")
    config_objects: list[CoderConfigObject] | None = Field(
        default=None, description="Config objects (native) for the coder"
    )

    @model_validator(mode="after")
    def validate_mcp_support(self):
        """Validate that MCP extensions are only used with coders that support them."""
        if self.config and self.config.extensions:
            mcp_extensions = [
                ext
                for ext in self.config.extensions
                if hasattr(ext, "enabled") and ext.enabled
            ]
            if mcp_extensions and not self.supports_mcp():
                raise ValueError(
                    f"MCP extensions are configured but {self.__class__.__name__} does not support MCP. "
                    f"Found {len(mcp_extensions)} enabled MCP extension(s). "
                    f"Please use a coder that supports MCP (e.g., ClaudeCoder, GooseCoder) or remove MCP extensions from the configuration."
                )
        return self



    @abstractmethod
    def run(self, input_text: str) -> CoderOutput:
        """Run the coder on the input text.

        Args:
            input_text: The input text to run the coder on

        Returns:
            CoderOutput: The output of the coder
        """
        raise NotImplementedError


    @classmethod
    def default_config_paths(cls) -> dict[Path, ConfigFileRole]:
        """Return config files as a dictionary of filename/dirname to role."""
        return {}

    @classmethod
    def is_available(cls) -> bool:
        """Check if this coder is available/installed on the system."""
        return True  # Default to True, subclasses can override

    @classmethod
    def supports_mcp(cls) -> bool:
        """Check if this coder supports MCP extensions.
        Default to False, subclasses that support MCP should override.
        """
        return False  # Default to False, subclasses that support MCP should override

    def run_process(
        self, command: list[str], env: dict[str, str] | None = None
    ) -> CoderOutput:
        """Run a process and return the output.

        Args:
            command: Command to run
            env: Environment variables to use

        Returns:
            Tuple of stdout and stderr

        Example:
            >>> from metacoder.coders.dummy import DummyCoder
            >>> coder = DummyCoder(workdir="tmp")
            >>> output = coder.run("hello")
            >>> output.stdout
            'you said: hello'


        """
        if env is None:
            env = self.expand_env(self.env)
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            bufsize=1,
            universal_newlines=True,
        )

        stdout_lines: list[str] = []
        stderr_lines: list[str] = []

        # check verbosity level
        quiet_mode = logger.getEffectiveLevel() <= logging.INFO

        def stream_output(pipe, output_lines, stream):
            for line in iter(pipe.readline, ""):
                if not quiet_mode:
                    print(line.rstrip(), file=stream)
                output_lines.append(line)
            pipe.close()

        # Start threads for both stdout and stderr
        stdout_thread = threading.Thread(
            target=stream_output, args=(process.stdout, stdout_lines, sys.stdout)
        )
        stderr_thread = threading.Thread(
            target=stream_output, args=(process.stderr, stderr_lines, sys.stderr)
        )

        stdout_thread.start()
        stderr_thread.start()

        # Wait for process and threads to complete
        return_code = process.wait()
        stdout_thread.join()
        stderr_thread.join()

        stdout_text = "\n".join(stdout_lines)
        stderr_text = "\n".join(stderr_lines)

        if return_code != 0:
            error = subprocess.CalledProcessError(return_code, command)
            error.stdout = stdout_text
            error.stderr = stderr_text
            raise error

        return CoderOutput(stdout=stdout_text, stderr=stderr_text)


    def expand_env(self, env: dict[str, str] | None = None) -> dict[str, str]:
        """
        Expand environment variables in the coder config.

        Example:

            >>> from metacoder.coders.dummy import DummyCoder
            >>> coder = DummyCoder(workdir="tmp")
            >>> import os
            >>> # unset all environment variables
            >>> os.environ.clear()
            >>> coder.expand_env({"HOME": "."})
            {'HOME': '.'}
            >>> os.environ["TEST"] = "test"
            >>> expanded = coder.expand_env({"HOME": "."})
            >>> expanded["HOME"]
            '.'
            >>> expanded["TEST"]
            'test'
            >>> coder.expand_env({"HOME": "$TEST"})["HOME"]
            'test'
        """
        if env is None:
            env = {}
        expanded_env = os.environ.copy()
        for key, value in env.items():
            if value.startswith("$"):
                env_value = os.getenv(value[1:])
                if env_value is not None:
                    expanded_env[key] = env_value
            else:
                expanded_env[key] = value
        return expanded_env

    def expand_prompt(self, input_text: str) -> str:
        """Expand environment variables in the prompt.
        
        Typically this just returns the prompt as is:

        Example:
            >>> from metacoder.coders.dummy import DummyCoder
            >>> coder = DummyCoder(workdir="tmp")
            >>> coder.expand_prompt("hello")
            'hello'

            >>> coder.prompt = "hello {input_text}"
            >>> coder.expand_prompt("Claude")
            'hello Claude'
        """
        if not self.prompt:
            return input_text
        return self.prompt.format(input_text=input_text)

    @abstractmethod
    def default_config_objects(self) -> list[CoderConfigObject]:
        """Default config objects for the coder."""
        raise NotImplementedError("default_config_objects is not implemented")
    
    def set_instructions(self, instructions: str):
        """Set the instructions for the coder.

        These are copied into the coder-specific instruction file; for example,
        the Claude instruction file is ./CLAUDE.md

        Example:
            >>> from metacoder.coders.claude import ClaudeCoder
            >>> coder = ClaudeCoder(workdir="tmp")
            >>> coder.set_instructions("you are an awesome coder")
            >>> coder.config_objects
            [CoderConfigObject(file_type=<FileType.TEXT: 'text'>, relative_path='CLAUDE.md', content='you are an awesome coder')]
        
        Args:
            instructions: The instructions to set
        """
        for path, typ in self.default_config_paths().items():
            if typ == ConfigFileRole.PRIMARY_INSTRUCTION:
                if not self.config_objects:
                    self.config_objects = []
                for obj in self.config_objects:
                    if obj.relative_path == str(path) or obj.relative_path == str(path.name):
                        obj.content = instructions
                        return
                else:
                    self.config_objects.append(CoderConfigObject(relative_path=str(path), content=instructions, file_type=FileType.TEXT))
                    return
            else:
                raise ValueError(f"Cannot set instructions for {typ}")
        raise ValueError(f"No primary instruction file found for {self.__class__.__name__}")
            

    def prepare_workdir(self):
        """Prepare the workdir for the coder.

        This method is called before the coder is run. It prepares the workdir for the coder,
        including clearing old config objects and writing new config objects.

        Config objects are either
        - compiled from config objects
        - copied from the config file

        Args:
            None

        Returns:

        """
        # Check if MCP extensions are configured but not supported
        if self.config and self.config.extensions:
            logger.debug(f"🔧 Checking MCP extensions: {self.config.extensions}")
            mcp_extensions = [
                ext
                for ext in self.config.extensions
                if ext.enabled
            ]
            if mcp_extensions and not self.supports_mcp():
                raise ValueError(
                    f"MCP extensions are configured but {self.__class__.__name__} does not support MCP. "
                    f"Found {len(mcp_extensions)} enabled MCP extension(s). "
                    f"Please use a coder that supports MCP (e.g., ClaudeCoder, GooseCoder) or remove MCP extensions from the configuration."
                )
            logger.debug(f"🔧 MCP extensions: {[e.name for e in mcp_extensions]}")

        if self.config_objects is None:
            self.config_objects = self.default_config_objects()
        logger.info(f"📁 Preparing workdir: {self.workdir}")
        with change_directory(self.workdir):
            # clear old config objects
            for path, _type in self.default_config_paths().items():
                if path.exists():
                    logger.debug(f" 🗑️ Removing old config object: {path}")
                    if path.is_dir():
                        import shutil
                        shutil.rmtree(path)
                    else:
                        path.unlink()
            logger.debug(f"🔧 Writing config objects: {self.config_objects}")
            for config_object in self.config_objects:
                path = Path(config_object.relative_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                logger.info(
                    f"🔧 Writing config object: {config_object.relative_path} type={config_object.file_type}"
                )
                if config_object.file_type == FileType.TEXT:
                    path.write_text(config_object.content)
                elif config_object.file_type == FileType.YAML:
                    import yaml

                    path.write_text(yaml.dump(config_object.content))
                elif config_object.file_type == FileType.JSON:
                    import json

                    path.write_text(json.dumps(config_object.content))
                else:
                    raise ValueError(f"Unknown file type: {config_object.file_type}")
