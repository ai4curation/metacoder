# metacoder/evals/judges.py
import logging
import os

from anthropic import Anthropic
from anthropic.types import MessageParam, TextBlockParam, TextBlock

from deepeval.models.base_model import DeepEvalBaseLLM

logger = logging.getLogger(__name__)


class ClaudeJudge(DeepEvalBaseLLM):
    """
    Wraps Anthropic's Claude models so they can be used as
    the `model` parameter to DeepEval metrics like GEval.
    """

    # Note: Anthropic models can be listed via:
    # curl https://api.anthropic.com/v1/models --header "x-api-key: %ANTHROPIC_API_KEY%" --header "anthropic-version: 2023-06-01"
    # {"data": [{"type": "model", "id": "claude-opus-4-1-20250805", "display_name": "Claude Opus 4.1", "created_at": "2025-08-05T00:00:00Z"}, ... ]}

    def __init__(
        self,
        model_name: str = "claude-sonnet-4-20250514",
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ):
        super().__init__()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise Exception("ANTHROPIC_API_KEY is not set in environment")
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

    def has_available_quota(self) -> bool:
        """
        Try a very lightweight request to check if quota is available.
        Returns True if quota exists, False if Anthropic responds with
        quota-related errors.
        """
        try:
            # Use a minimal "ping" request
            content: list[TextBlockParam] = [{"type": "text", "text": "ping"}]
            messages: list[MessageParam] = [{"role": "user", "content": content}]
            self.client.messages.create(
                model=self.model_name,
                max_tokens=1,  # cheapest possible
                temperature=0.0,
                messages=messages,
            )
            return True
        except Exception as e:
            msg = str(e).lower()
            # Check for insufficient quota:
            # 400 Bad Request. Message: Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.
            if "credit balance is too low" in msg or "400" in msg:
                logger.warning(f"ClaudeJudge quota check failed: {e}")
                return False
            raise
