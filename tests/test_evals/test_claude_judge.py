import logging
import traceback
from pathlib import Path

from metacoder.evals.runner import EvalRunner

logger = logging.getLogger(__name__)


def test_claude_judge_downgrade_success(tmp_path, caplog, monkeypatch):
    """Test that ClaudeJudge is used when OpenAI is disabled."""
    # TODO: This test should avoid running the coder and only perform the eval step.
    # Otherwise, it is impossible to get to the eval step if no valid API key is present or no quota is available (testing the wrong part of the process).

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
            monkeypatch.setenv("OPENAI_API_KEY", "fake-api-key-for-testing")

            results = runner.run_all_evals(
                dataset, workdir=tmp_path, coders=["goose", "dummy"]
            )

            # Test that the quota exhaustion fallback logic worked as expected.
            assert (
                "OpenAI API quota exhausted or server unavailable; disabling OpenAI for DeepEval."
                in caplog.text
            )

            # Test that the new evaluation judge was correctly selected for the metric model downgrade.
            assert (
                "Downgrading CorrectnessMetric model from gpt-4.1 to claude-3-5-sonnet-20240620."
                in caplog.text
            )

            # Test that the eval completed by checking for a non-zero score.
            assert results[0].score > 0, (
                f"Expected a {results[0].metric_name} score for {results[0].case_name}."
            )

    except Exception as e:
        # Test that fallback logic does not result in an Exception.
        logger.error(f"An error occurred: {e}")
        logging.error(traceback.format_exc())
        assert False  # This assertion will fail if an Exception is caught here.
    finally:
        pass


def test_correctnessmetric_downgrade_success(tmp_path, caplog, monkeypatch):
    """Test that the CorrectnessMatric is successfully downgraded to DummyMetric if no model is available."""

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
            monkeypatch.setenv("OPENAI_API_KEY", "fake-api-key-for-testing")

            # Delete the Anthropic API Key from the environment to force ClaudeJudge instantiation to fail.
            # (no need to reset, `monkeypatch` automatically reverts after the test)
            monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

            # One more OpenAI API test case also needs to be handled (401 errors):
            # Temporarily set an invalid ANTHROPIC_API_KEY in order to force ClaudeJudge to fail.
            # monkeypatch.delenv("OPENAI_API_KEY", raising=False)

            # One more Anthropic API test case also needs to be handled (401 errors):
            # Temporarily set an invalid ANTHROPIC_API_KEY in order to force ClaudeJudge to fail.
            # monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-api-key-for-testing")

            # TODO: Also need to test this for Anthropic:
            # Provider
            # request
            # failed
            # with status: 400
            # Bad
            # Request.Payload: Some(Object
            # {"error": Object {"message": String("Your credit balance is too low
            #                   to access the Anthropic API.Please go to Plans & Billing to upgrade or purchase
            #                   credits."), "type": String("invalid_request_error")}, "request_id": String("
            #                   req_011CSeQZTjJvmcxzrhXuPES4"), "type": Strin
            #                   g("error")}).Returning
            # error: RequestFailed(
            #     "Request failed with status: 400 Bad Request. Message: Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits."

            results = runner.run_all_evals(dataset, workdir=tmp_path, coders=["dummy"])

            # Test that the quota exhaustion fallback logic worked as expected.
            assert (
                "OpenAI API quota exhausted or server unavailable; disabling OpenAI for DeepEval."
                in caplog.text
            )

            # Test that the new evaluation judge was correctly selected for the metric model downgrade.
            assert (
                "Downgrading CorrectnessMetric model from gpt-4.1 to claude-3-5-sonnet-20240620."
                in caplog.text
            )

            # Test that the ClaudeJudge was unable to be used as the model for the CorrectnessMetric.
            assert (
                "Claude unavailable (ANTHROPIC_API_KEY is not set in environment); downgrading CorrectnessMetric to DummyMetric."
                in caplog.text
            )

            # Test that the CorrectnessMetric was successfully downgraded to DummyMetric.
            assert "Downgraded CorrectnessMetric to DummyMetric." in caplog.text

            # Test that the eval completed by checking for a non-zero score.
            assert results[0].score > 0, (
                f"Expected a {results[0].metric_name} score for {results[0].case_name}."
            )

    except Exception as e:
        # Test that fallback logic does not result in an Exception.
        logger.error(f"An error occurred: {e}")
        logging.error(traceback.format_exc())
        assert False  # This assertion will fail if an Exception is caught here.
    finally:
        pass
