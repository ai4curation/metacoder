import logging
from pathlib import Path

from metacoder.evals.runner import EvalRunner

logger = logging.getLogger(__name__)


def test_claude_judge_downgrade_success(tmp_path, caplog, monkeypatch):
    """Test that ClaudeJudge is used when OpenAI is disabled."""

    # Temporarily set an invalid OPENAI_API_KEY in order to force OpenAI calls to fail.
    # (no need to reset, `monkeypatch` automatically reverts after the test)
    monkeypatch.setenv("OPENAI_API_KEY", "fake-api-key-for-testing")

    runner = EvalRunner()

    try:
        dataset = runner.load_dataset(
            Path("tests/input/goose_eval_claude_downgrade_test.yaml")
        )

        # Unfortunately, there is nothing available in the eval results that indicate which model DeepEval used.
        # One enhancement might be to introduce metric_model=claude-3-5-sonnet-20240620 to each result at eval time.
        # Instead, resort to capturing the WARNING logs for assertions related to the downgrade.
        with caplog.at_level(logging.WARNING):
            results = runner.run_all_evals(dataset, workdir=tmp_path, coders=["goose"])

            # Verfiy that the downgrade happened.
            assert (
                "OpenAI API quota exhausted or server unavailable; downgrading to claude-3-5-sonnet-20240620"
                in caplog.text
            )

            # Verify that the eval completed by checking for a non-zero score.
            assert results[0].score > 0, (
                f"Expected ClaudeJudge to score {results[0].metric_name} for {results[0].case_name}"
            )

    finally:
        pass
