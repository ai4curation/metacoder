from metacoder.coders.base_coder import BaseCoder, CoderConfigObject, CoderOutput


class DummyCoder(BaseCoder):
    """
    For testing
    """

    @classmethod
    def supports_mcp(cls) -> bool:
        """DummyCoder supports MCP for testing purposes."""
        return True

    def instruction_files(self) -> dict[str, str]:
        # Dummy coder doesn't use instruction files
        return {}

    def default_config_objects(self) -> list[CoderConfigObject]:
        return []

    def run(self, input_text: str) -> CoderOutput:
        return CoderOutput(
            stdout="you said: " + input_text,
            stderr="",
            result_text="you said: " + input_text,
        )
