"""Registry of available coders."""
from typing import Dict, Type

from metacoder.coders.base_coder import BaseCoder
from metacoder.coders.goose import GooseCoder
from metacoder.coders.claude import ClaudeCoder
from metacoder.coders.codex import CodexCoder
from metacoder.coders.dummy import DummyCoder
from metacoder.coders.gemini import GeminiCoder
from metacoder.coders.qwen import QwenCoder


AVAILABLE_CODERS: Dict[str, Type[BaseCoder]] = {
    "goose": GooseCoder,
    "claude": ClaudeCoder,
    "codex": CodexCoder,
    "gemini": GeminiCoder,
    "qwen": QwenCoder,
    "dummy": DummyCoder,
}