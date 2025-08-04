"""Tests for the evaluation runner.

This uses only dummy coders, so can be used in non-integration contexts.
"""
import pytest
from pathlib import Path
import tempfile
import yaml

from metacoder.evals.runner import EvalRunner
from metacoder.evals.eval_model import EvalCase, EvalDataset
from metacoder.configuration import AIModelConfig, MCPConfig, AIModelProvider


class TestEvalRunner:
    """Test the evaluation runner."""
    
    @pytest.fixture
    def simple_config(self, tmp_path):
        """Create a simple evaluation config for testing."""
        config = {
            "name": "test evals",
            "description": "Test evaluation dataset",
            "models": {
                "test-model": {
                    "provider": {
                        "name": "openai"
                    },
                    "name": "gpt-test"
                }
            },
            "servers": {},
            "cases": [
                {
                    "name": "simple_math",
                    "metrics": ["CorrectnessMetric"],
                    "input": "What is 2+2?",
                    "expected_output": "4",
                    "retrieval_context": "Basic arithmetic: 2+2=4",
                    "threshold": 0.7
                }
            ]
        }
        
        config_path = tmp_path / "test_config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        return config_path
    
    def test_load_dataset(self, simple_config):
        """Test loading a dataset from YAML."""
        runner = EvalRunner()
        dataset = runner.load_dataset(simple_config)
        
        assert dataset.name == "test evals"
        assert "test-model" in dataset.models
        assert len(dataset.cases) == 1
        assert dataset.cases[0].name == "simple_math"
    
    def test_eval_case_model(self):
        """Test EvalCase model validation."""
        case = EvalCase(
            name="test",
            metrics=["CorrectnessMetric"],
            input="Test input",
            expected_output="Test output",
            threshold=0.8
        )
        
        assert case.name == "test"
        assert case.metrics == ["CorrectnessMetric"]
        assert case.threshold == 0.8
    
    def test_dataset_model(self):
        """Test EvalDataset model validation."""
        dataset = EvalDataset(
            name="test",
            description="Test dataset",
            models={
                "model1": AIModelConfig(
                    provider=AIModelProvider(name="openai"),
                    name="gpt-4"
                )
            },
            servers={},
            cases=[
                EvalCase(
                    name="case1",
                    metrics=["CorrectnessMetric"],
                    input="Input",
                    expected_output="Output"
                )
            ]
        )
        
        assert dataset.name == "test"
        assert "model1" in dataset.models
        assert len(dataset.cases) == 1
    
    def test_get_metric_class(self):
        """Test metric class resolution."""
        runner = EvalRunner()
        

        # Test direct metric name
        metric_class = runner.get_metric_class("AnswerRelevancyMetric")
        assert metric_class.__name__ == "AnswerRelevancyMetric"
        
        # Test unknown metric
        with pytest.raises(ValueError, match="Could not find metric class"):
            runner.get_metric_class("UnknownMetric")
    
    def test_create_test_case(self):
        """Test creating a deepeval test case."""
        runner = EvalRunner()
        
        eval_case = EvalCase(
            name="test",
            metrics=["CorrectnessMetric"],
            input="What is 2+2?",
            expected_output="4",
            retrieval_context="2+2=4"
        )
        
        test_case = runner.create_test_case(eval_case, "The answer is 4")
        
        assert test_case.input == "What is 2+2?"
        assert test_case.actual_output == "The answer is 4"
        assert test_case.expected_output == "4"
        assert test_case.retrieval_context == ["2+2=4"]
    
    def test_create_test_case_with_list_context(self):
        """Test creating a test case with list retrieval context."""
        runner = EvalRunner()
        
        eval_case = EvalCase(
            name="test",
            metrics=["CorrectnessMetric"],
            input="What is 2+2?",
            expected_output="4",
            retrieval_context=["Math fact 1", "Math fact 2"]
        )
        
        test_case = runner.create_test_case(eval_case, "4")
        assert test_case.retrieval_context == ["Math fact 1", "Math fact 2"]
    
    def test_run_single_eval_with_dummy(self, simple_config, tmp_path):
        """Test running a single evaluation with dummy coder."""
        runner = EvalRunner()
        dataset = runner.load_dataset(simple_config)
        
        results = runner.run_single_eval(
            "test-model",
            dataset.models["test-model"],
            "dummy",
            dataset.cases[0],
            tmp_path / "workdir"
        )
        
        assert len(results) == 1
        result = results[0]
        assert result.model == "test-model"
        assert result.coder == "dummy"
        assert result.case_name == "simple_math"
        assert result.metric_name == "CorrectnessMetric"
        assert result.actual_output == "you said: What is 2+2?"
        assert result.expected_output == "4"
    
    def test_generate_summary(self):
        """Test summary generation."""
        from metacoder.evals.runner import EvalResult
        
        runner = EvalRunner()
        
        results = [
            EvalResult(
                model="model1",
                coder="coder1",
                case_name="case1",
                metric_name="metric1",
                score=0.9,
                passed=True
            ),
            EvalResult(
                model="model1",
                coder="coder1",
                case_name="case2",
                metric_name="metric1",
                score=0.3,
                passed=False
            ),
            EvalResult(
                model="model2",
                coder="coder1",
                case_name="case1",
                metric_name="metric1",
                score=0.8,
                passed=True
            ),
        ]
        
        summary = runner.generate_summary(results)
        
        assert summary['total_evaluations'] == 3
        assert summary['passed'] == 2
        assert summary['failed'] == 1
        assert summary['errors'] == 0
        
        assert summary['by_model']['model1']['total'] == 2
        assert summary['by_model']['model1']['passed'] == 1
        assert summary['by_model']['model1']['failed'] == 1
        
        assert summary['by_coder']['coder1']['total'] == 3
        assert summary['by_coder']['coder1']['passed'] == 2
        
        assert summary['by_metric']['metric1']['average_score'] == pytest.approx(0.666666, rel=1e-3)
    
    def test_save_and_load_results(self, tmp_path):
        """Test saving and loading results."""
        from metacoder.evals.runner import EvalResult
        
        runner = EvalRunner()
        
        results = [
            EvalResult(
                model="model1",
                coder="coder1", 
                case_name="case1",
                metric_name="metric1",
                score=0.9,
                passed=True,
                actual_output="output",
                expected_output="expected"
            )
        ]
        
        output_path = tmp_path / "results.yaml"
        runner.save_results(results, output_path)
        
        assert output_path.exists()
        
        # Load and verify
        with open(output_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert 'results' in data
        assert 'summary' in data
        assert len(data['results']) == 1
        assert data['results'][0]['model'] == "model1"
        assert data['results'][0]['score'] == 0.9
    
    def test_run_all_evals_with_dummy(self, simple_config, tmp_path):
        """Test running all evaluations with dummy coder."""
        runner = EvalRunner()
        dataset = runner.load_dataset(simple_config)
        
        workdir = tmp_path / "eval_workdir"
        results = runner.run_all_evals(dataset, workdir, coders=["dummy"])
        
        assert len(results) == 1
        result = results[0]
        assert result.coder == "dummy"
        assert result.actual_output == "you said: What is 2+2?"
    