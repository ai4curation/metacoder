
from typing import Any
from pydantic import BaseModel


class ToolExtension(BaseModel):
    """
    A tool extension is a tool extension for a coder.
    """
    name: str
    display_name: str | None = None
    description: str | None = None
    enabled: bool = True
    bundled: bool | None = None
    cmd: str | None = None
    args: list[str] | None = None
    env_keys: list[str] | None = None
    type: str | None = None
    timeout: int | None = None


class AIModelProvider(BaseModel):
    """
    An AI model provider is a provider of an AI model.
    """
    name: str
    api_key: str | None = None
    metadata: dict[str, Any] = {}

class AIModelConfig(BaseModel):
    """
    A specification of an AI model and how to run it
    """
    name: str
    provider: AIModelProvider | None = None

class CoderConfig(BaseModel):
    """
    A coder config is a config for a coder.
    """
    ai_model: AIModelConfig
    extensions: list[ToolExtension]