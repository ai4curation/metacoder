import logging
import os
import traceback
from pathlib import Path

from metacoder.evals.runner import EvalRunner

logger = logging.getLogger(__name__)


def test_claude_judge_downgrade_success(tmp_path, caplog, monkeypatch):
    """Test that ClaudeJudge is used when OpenAI is disabled."""

    # # Temporarily set an invalid OPENAI_API_KEY in order to force OpenAI calls to fail.
    # # (no need to reset, `monkeypatch` automatically reverts after the test)
    # monkeypatch.setenv("OPENAI_API_KEY", "fake-api-key-for-testing")

    runner = EvalRunner()

    try:
        dataset = runner.load_dataset(
            Path("tests/input/goose_eval_claude_downgrade_test.yaml")
        )

        # Unfortunately, there is nothing available in the eval results that indicate which model DeepEval used.
        # One enhancement might be to introduce metric_model=claude-3-5-sonnet-20240620 to each result at eval time.
        # Instead, resort to capturing the WARNING logs for assertions related to the downgrade.
        with caplog.at_level(logging.WARNING):
            # Temporarily set an invalid OPENAI_API_KEY in order to force OpenAI calls to fail.
            # (no need to reset, `monkeypatch` automatically reverts after the test)
            # Save the original OPENAI_API_KEY if it exists
            # original_api_key = os.getenv("OPENAI_API_KEY")
            monkeypatch.setenv("OPENAI_API_KEY", "fake-api-key-for-testing")

            results = runner.run_all_evals(
                dataset, workdir=tmp_path, coders=["goose", "dummy"]
            )

            # # Revert the OPENAI_API_KEY to its original value
            # if original_api_key is not None:
            #     monkeypatch.setenv("OPENAI_API_KEY", original_api_key)
            # else:
            #     monkeypatch.delenv("OPENAI_API_KEY", raising=False)

            # Verfiy that the downgrade happened.
            assert (
                "OpenAI API quota exhausted or server unavailable; disabling OpenAI for DeepEval."
                in caplog.text
            )

            # Verify that the eval completed by checking for a non-zero score.
            assert results[0].score > 0, (
                f"Expected ClaudeJudge to score {results[0].metric_name} for {results[0].case_name}"
            )

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        # traceback.print_exc()
        logging.error(traceback.format_exc())
        assert False  # force test to fail if an exception is caught here
    finally:
        pass
