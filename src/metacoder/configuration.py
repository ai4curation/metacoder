from enum import Enum
from pathlib import Path
from typing import Any, Optional

import click
import yaml
from pydantic import BaseModel, Field, ValidationError


class FileType(str, Enum):
    """File type of the config object.

    TODO: consider renaming since a directory is not a file type
    """

    TEXT = "text"
    YAML = "yaml"
    JSON = "json"
    DIRECTORY = "directory"


class ConfigFileRole(str, Enum):
    """Role of a config file."""

    PRIMARY_INSTRUCTION = "primary_instruction"  # e.g. CLAUDE.md
    SECONDARY_INSTRUCTION = "secondary_instruction"  # e.g. sub-agent files
    CONFIG = "config"
    AGENTS = "agents"
    DATA = "data"
    METADATA = "metadata"


class CoderConfigObject(BaseModel):
    """Base class for coder config objects.

    A coder can be configured with a list of files in a configuration directory.
    This class represents a single file in the configuration directory.
    """

    file_type: FileType = Field(
        FileType.TEXT, description="File type of the config object"
    )
    relative_path: str = Field(
        ..., description="Path to the file relative to the workdir"
    )
    content: Any = Field(..., description="Content of the file")


class AIModelProvider(BaseModel):
    """
    An AI model provider is a provider of an AI model.
    """

    name: str = Field(..., description="Name of the model provider")
    api_key: str | None = Field(None, description="API key for the model provider")
    metadata: dict[str, Any] = Field({}, description="Metadata for the model provider")
    base_url: str | None = Field(None, description="Base URL for the model provider")


class AIModelConfig(BaseModel):
    """
    A specification of an AI model and how to run it
    """

    name: str
    provider: str | AIModelProvider | None = None


class MCPType(str, Enum):
    """
    A MCP type is a type of MCP.
    """

    STDIO = "stdio"
    HTTP = "http"
    BUILTIN = "builtin"


class MCPConfig(BaseModel):
    """
    A MCP config is a config for a MCP.
    """

    name: str = Field(..., description="Name of the MCP")
    description: str | None = Field(None, description="Description of the MCP")
    command: str | None = Field(
        None, description="Command to run the MCP (e.g. npx, uvx)"
    )
    args: list[str] | None = Field(None, description="Arguments to pass to the command")
    env: dict[str, str] | None = Field(None, description="Environment variables to set")
    enabled: bool = Field(True, description="Whether the MCP is enabled")
    # type is either stdio or http:
    type: MCPType = Field(MCPType.STDIO, description="Type of MCP")
    timeout: int | None = Field(None, description="Timeout in seconds")


class MCPCollectionConfig(BaseModel):
    """
    A MCP collection config is a config for a MCP collection.
    """

    name: str = Field(..., description="Name of the MCP collection")
    description: str | None = Field(
        None, description="Description of the MCP collection"
    )
    servers: list[MCPConfig] = Field(
        ..., description="Servers to use for the MCP collection"
    )


class CoderConfig(BaseModel):
    """
    A coder config is a config for a coder.
    """

    ai_model: AIModelConfig
    extensions: list[MCPConfig]


def load_coder_config(config_path: Optional[Path]) -> Optional[CoderConfig]:
    """Load CoderConfig from YAML file."""
    if not config_path:
        return None

    if not config_path.exists():
        raise click.ClickException(f"Config file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)

        return CoderConfig.model_validate(config_data)
    except yaml.YAMLError as e:
        raise click.ClickException(f"Invalid YAML in config file: {e}")
    except ValidationError as e:
        raise click.ClickException(f"Invalid config format: {e}")
