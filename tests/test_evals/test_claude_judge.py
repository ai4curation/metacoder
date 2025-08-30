import logging
from pathlib import Path

from metacoder.evals.runner import EvalRunner


def test_claude_judge_downgrade_success(tmp_path, caplog, monkeypatch):
    """Test that ClaudeJudge is used when OpenAI is disabled."""

    # Temporarily set an invalid OPENAI_API_KEY in order to force OpenAI calls to fail.
    # (no need to reset, `monkeypatch` automatically reverts after the test)
    monkeypatch.setenv("OPENAI_API_KEY", "fake-api-key-for-testing")

    runner = EvalRunner()

    try:
        dataset = runner.load_dataset(Path("tests/input/goose_eval_claude_downgrade_test.yaml"))

        # Unfortunately, there is nothing available in the eval results that indicate which model DeepEval used.
        # Instead, resort to capturing the WARNING logs for assertions related to the downgrade.
        with caplog.at_level(logging.WARNING):
            results = runner.run_all_evals(dataset, workdir=tmp_path, coders=["goose"])
            assert "OpenAI API quota exhausted or server unavailable; downgrading to claude-3-5-sonnet-20240620" in caplog.text

    finally:
        pass
