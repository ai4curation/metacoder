# metacoder/evals/judges.py

import os

from anthropic import Anthropic
from anthropic.types import MessageParam, TextBlockParam, TextBlock

from deepeval.models.base_model import DeepEvalBaseLLM


class ClaudeJudge(DeepEvalBaseLLM):
    """
    Wraps Anthropic's Claude models so they can be used as
    the `model` parameter to DeepEval metrics like GEval.
    """

    def __init__(
        self,
        model_name: str = "claude-3-5-sonnet-20240620",
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ):
        super().__init__()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set in environment.")
        self.client = Anthropic(api_key=api_key)
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature

    def load_model(self):
        return self

    def generate(self, prompt: str) -> str:
        # Build typed content blocks and messages to satisfy the SDK's type hints
        content: list[TextBlockParam] = [{"type": "text", "text": prompt}]
        messages: list[MessageParam] = [{"role": "user", "content": content}]
        resp = self.client.messages.create(
            model=self.model_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=messages,
        )
        # anthropic returns a list of content blocks; collect only the text blocks.
        parts: list[str] = []
        for block in resp.content:
            if isinstance(block, TextBlock):
                parts.append(block.text)
        return "".join(parts)

    async def a_generate(self, prompt: str) -> str:
        # for now just call the sync path
        return self.generate(prompt)

    def get_model_name(self) -> str:
        return self.model_name
