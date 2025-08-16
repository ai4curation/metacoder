"""
Test the deepeval library.

https://github.com/metacoder-ai/deepeval

Note this doesn't actually test any metacoder functonality, it is more to explore
deepeval metrics, it can probably be removed in the future.
"""

from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams
from deepeval import evaluate
from deepeval.metrics import (
    FaithfulnessMetric,
    HallucinationMetric,
)
from deepeval.test_case import LLMTestCase
import pytest


@pytest.mark.llm
@pytest.mark.parametrize("metric_cls", [FaithfulnessMetric])
def test_generic_eval(metric_cls):
    """Test FaithfulnessMetric with correct output matching context."""
    metric = metric_cls(threshold=0.7)
    test_case = LLMTestCase(
        input="What is the title of PMID:28027860?",
        expected_output="The answer to the question 'what is the title of PMID:28027860?' is 'From nocturnal frontal lobe epilepsy to Sleep-Related Hypermotor Epilepsy.'",
        actual_output='The answer to the question "what is the title of PMID:28027860?" is "From nocturnal frontal lobe epilepsy to Sleep-Related Hypermotor Epilepsy."',
        context=[
            "Title: From nocturnal frontal lobe epilepsy to Sleep-Related Hypermotor Epilepsy."
        ],
        retrieval_context=[
            "PMID:28027860? Title: From nocturnal frontal lobe epilepsy to Sleep-Related Hypermotor Epilepsy."
        ],
    )
    results = evaluate([test_case], [metric])
    import yaml

    print(results)
    print(yaml.dump(results.model_dump()))


@pytest.mark.llm
@pytest.mark.parametrize("metric_cls", [HallucinationMetric])
def test_hallucination_eval(metric_cls):
    """Test HallucinationMetric detects incorrect information not supported by context."""
    metric = metric_cls(threshold=0.7)
    test_case = LLMTestCase(
        input="What is the title of PMID:28027860?",
        expected_output="From nocturnal frontal lobe epilepsy to Sleep-Related Hypermotor Epilepsy.",
        actual_output='The title of the article with PMID:28027860 is "Predictors of acute and persisting fatigue in people with relapsing and remitting multiple sclerosis: A cohort study."',
        context=[
            "Title of PMID:28027860: From nocturnal frontal lobe epilepsy to Sleep-Related Hypermotor Epilepsy."
        ],
    )
    results = evaluate([test_case], [metric])
    import yaml

    print(results)
    print(yaml.dump(results.model_dump()))


correctness_metric = GEval(
    name="Correctness",
    criteria="Determine whether the actual output is factually correct based on the expected output.",
    # NOTE: you can only provide either criteria or evaluation_steps, and not both
    evaluation_steps=[
        "Check whether the facts in 'actual output' contradicts any facts in 'expected output'",
        "You should also heavily penalize omission of detail",
        "Vague language, or contradicting OPINIONS, are OK",
    ],
    threshold=0.8,
    evaluation_params=[
        LLMTestCaseParams.INPUT,
        LLMTestCaseParams.ACTUAL_OUTPUT,
        LLMTestCaseParams.EXPECTED_OUTPUT,
    ],
)


@pytest.mark.llm
def test_geval_eval():
    """Test GEval correctness metric catches factual errors in output."""
    metric = correctness_metric
    test_case = LLMTestCase(
        input="What is the title of PMID:28027860?",
        expected_output="From nocturnal frontal lobe epilepsy to Sleep-Related Hypermotor Epilepsy.",
        actual_output='The title of the article with PMID:28027860 is "Predictors of acute and persisting fatigue in people with relapsing and remitting multiple sclerosis: A cohort study."',
    )
    results = evaluate([test_case], [metric])
    import yaml

    print(results)
    print(yaml.dump(results.model_dump()))
