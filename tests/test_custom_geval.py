"""Test custom GEval metric configuration."""

import pytest
from metacoder.evals.eval_model import MetricConfig, RubricItem


def test_evaluation_steps_only():
    """Test creating MetricConfig with only evaluation_steps."""
    m = MetricConfig(
        name="CorrectnessMetric", evaluation_steps=["Check if output is correct"]
    )
    assert m.evaluation_steps == ["Check if output is correct"]
    assert m.criteria is None
    assert m.rubric is None


def test_criteria_only():
    """Test creating MetricConfig with only criteria."""
    m = MetricConfig(name="CorrectnessMetric", criteria="Check correctness")
    assert m.criteria == "Check correctness"
    assert m.evaluation_steps is None
    assert m.rubric is None


def test_rubric_only():
    """Test creating MetricConfig with only rubric."""
    rubric = [
        RubricItem(score=0.0, criteria="Wrong"),
        RubricItem(score=1.0, criteria="Correct"),
    ]
    m = MetricConfig(name="CorrectnessMetric", rubric=rubric)
    assert len(m.rubric) == 2
    assert m.criteria is None
    assert m.evaluation_steps is None


def test_criteria_and_evaluation_steps_mutually_exclusive():
    """Test that providing both criteria and evaluation_steps raises ValueError."""
    with pytest.raises(ValueError, match="Cannot specify both"):
        MetricConfig(
            name="CorrectnessMetric",
            criteria="Check correctness",
            evaluation_steps=["Step 1"],
        )


def test_requires_at_least_one():
    """Test that at least one of criteria/evaluation_steps/rubric is required."""
    with pytest.raises(ValueError, match="Must provide at least one"):
        MetricConfig(name="CorrectnessMetric")


def test_criteria_with_rubric():
    """Test that criteria can be combined with rubric."""
    rubric = [RubricItem(score=0.0, criteria="Wrong")]
    m = MetricConfig(
        name="CorrectnessMetric", criteria="Check correctness", rubric=rubric
    )
    assert m.criteria == "Check correctness"
    assert len(m.rubric) == 1


def test_evaluation_steps_with_rubric():
    """Test that evaluation_steps can be combined with rubric."""
    rubric = [RubricItem(score=1.0, criteria="Correct")]
    m = MetricConfig(
        name="CorrectnessMetric", evaluation_steps=["Step 1"], rubric=rubric
    )
    assert m.evaluation_steps == ["Step 1"]
    assert len(m.rubric) == 1
