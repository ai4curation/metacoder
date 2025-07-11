from abc import ABC, abstractmethod
from contextlib import contextmanager
from enum import Enum
import logging
import os
from pathlib import Path
import subprocess
import sys
import threading
from typing import Any, Callable
from pydantic import BaseModel, Field

from coders.config import CoderConfig

logger = logging.getLogger(__name__)

class FileType(str, Enum):
    """File type of the config object."""
    TEXT = "text"
    YAML = "yaml"
    JSON = "json"
    

class CoderConfigObject(BaseModel):
    """Base class for coder config objects."""
    file_type: FileType = Field(FileType.TEXT, description="File type of the config object")
    relative_path: str = Field(..., description="Path to the file relative to the workdir")
    content: Any = Field(..., description="Content of the file")

class CoderOutput(BaseModel):
    """Base class for coder outputs."""
    stdout: str = Field(..., description="Standard output from the coder")
    stderr: str = Field(..., description="Standard error from the coder")
    result_text: str | None = Field(None, description="Result text from the coder")
    total_cost_usd: float | None = Field(None, description="Total cost in USD")
    success: bool | None = Field(None, description="Whether the coder ran successfully")
    structured_messages: list[dict] | None = Field(None, description="Messages from the coder, e.g claude json output")


LOCK_FILE = ".lock"
    
@contextmanager
def change_directory(path: str):
    """Context manager to temporarily change directory."""
    original_dir = os.getcwd()
    Path(path).mkdir(parents=True, exist_ok=True)
    lock_file = Path(path) / LOCK_FILE
    logger.info(f"🔒 Obtaining lock for {path}; current_dir={original_dir}")
    if lock_file.exists():
        print(f"🚫 Lock file {lock_file} exists in {path}. If you are SURE no other process is running in this directory, delete the lock file and try again.")
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
    workdir: str = Field("workdir", description="Working dir ")
    config: CoderConfig | None = Field(None, description="Config for the coder")
    params: dict | None = Field(None, description="Parameters for the coder")
    env: dict[str, str] | None = Field(None, description="Environment variables for the coder")
    prompt: str | None = Field(None, description="Prompt for the coder")
    config_objects: list[CoderConfigObject] | None = Field(None, description="Config objects (native) for the coder")

    @property
    def instructions_path(self) -> Path:
        raise NotImplementedError

    @abstractmethod
    def run(self, input_text: str) -> CoderOutput:
        pass
    
    def run_process(self, command: list[str], env: dict[str, str] | None = None) -> CoderOutput:
        """Run a process and return the output.
        
        Args:
            command: Command to run
            env: Environment variables to use
        
        Returns:
            Tuple of stdout and stderr

        Example:
            >>> from coders.dummy import DummyCoder
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
            universal_newlines=True
        )
        
        stdout_lines = []
        stderr_lines = []
        
        def stream_output(pipe, output_lines, stream):
            for line in iter(pipe.readline, ''):
                print(line.rstrip(), file=stream)
                output_lines.append(line)
            pipe.close()
        
        # Start threads for both stdout and stderr
        stdout_thread = threading.Thread(
            target=stream_output, 
            args=(process.stdout, stdout_lines, sys.stdout)
        )
        stderr_thread = threading.Thread(
            target=stream_output, 
            args=(process.stderr, stderr_lines, sys.stderr)
        )
        
        stdout_thread.start()
        stderr_thread.start()
        
        # Wait for process and threads to complete
        return_code = process.wait()
        stdout_thread.join()
        stderr_thread.join()
        
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, command)
        
        return CoderOutput(stdout="\n".join(stdout_lines), stderr="\n".join(stderr_lines))
    
    
    def all_instructions(self) -> str:
        """
        Get all instructions from the instruction files.
        
        Args:
            None

        Returns:
            A string of all instruction files concatenated together
        """
        return "\n\n".join(self.instruction_files().values())
    
    def expand_env(self, env: dict[str, str] | None = None) -> dict[str, str]:
        """
        Expand environment variables in the coder config.

        Example:

            >>> from coders.dummy import DummyCoder
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
                expanded_env[key] = os.getenv(value[1:])
            else:
                expanded_env[key] = value
        return expanded_env
    
    def expand_prompt(self, input_text: str) -> str:
        """Expand environment variables in the prompt."""
        if not self.prompt:
            return input_text
        return self.prompt.format(input_text=input_text)
    
    @abstractmethod
    def default_config_objects(self) -> list[CoderConfigObject]:
        """Default config objects for the coder."""
        raise NotImplementedError("default_config_objects is not implemented")
    
    def prepare_workdir(self):
        """Prepare the workdir for the coder."""
        if self.config_objects is None:
            self.config_objects = self.default_config_objects()
        print(f"🦆 Preparing workdir: {self.workdir}")
        with change_directory(self.workdir):
            for config_object in self.config_objects:
                path = Path(config_object.relative_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                print(f"🦆 Writing config object: {config_object.relative_path} type={config_object.file_type}")
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

