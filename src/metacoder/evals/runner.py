"""
Evaluation runner for metacoder.

Runs evaluations across all combinations of model x coder x case x metric.
"""

import copy
import importlib
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel
import yaml
from deepeval import evaluate
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams


from metacoder.coders.base_coder import BaseCoder, CoderOutput
from metacoder.registry import AVAILABLE_CODERS
from metacoder.evals.eval_model import EvalCase, EvalDataset
from metacoder.configuration import AIModelConfig, CoderConfig


logger = logging.getLogger(__name__)


class DummyMetric(BaseMetric):
    """A dummy metric that always returns a perfect score for testing."""

    def __init__(self, threshold: float = 0.5, **kwargs):
        self.threshold = threshold
        self._name = "DummyMetric"
        self.success: bool = True  # Initialize success

    @property
    def name(self):
        return self._name

    def measure(self, test_case: LLMTestCase) -> float:
        """Always returns a perfect score."""
        self.score = 1.0
        self.success = self.score >= self.threshold
        self.reason = (
            "This is a dummy metric that always returns 1.0 for testing purposes"
        )
        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        """Async version - also returns perfect score."""
        return self.measure(test_case)

    def is_successful(self) -> bool:
        """Check if the metric passed."""
        return self.success


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

# instances
dummy_metric = DummyMetric(threshold=0.5)

METRICS = {
    "CorrectnessMetric": correctness_metric,
    "DummyMetric": dummy_metric,
}


def create_coder(coder_name: str, workdir: str, config=None) -> BaseCoder:
    """Create a coder instance."""
    if coder_name not in AVAILABLE_CODERS:
        available = ", ".join(AVAILABLE_CODERS.keys())
        raise ValueError(f"Unknown coder: {coder_name}. Available: {available}")

    coder_class = AVAILABLE_CODERS[coder_name]

    # Create coder with workdir
    coder = coder_class(workdir=workdir)

    # Apply config if provided
    if config:
        coder.config = config

    return coder



class EvalResult(BaseModel):
    """Result of a single evaluation."""

    model: str
    coder: str
    case_name: str
    metric_name: str
    score: float
    passed: bool
    reason: Optional[str] = None
    actual_output: Optional[str] = None
    execution_metadata: Optional[CoderOutput] = None
    expected_output: Optional[str] = None
    execution_time: Optional[float] = None
    error: Optional[str] = None
    servers: Optional[List[str]] = None


class EvalRunner:
    """Runs evaluations across models, coders, and cases."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        if verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

    def load_dataset(self, config_path: Path) -> EvalDataset:
        """Load evaluation dataset from YAML file."""
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
        return EvalDataset(**data)

    def get_metric_class(self, metric_name: str) -> Type[BaseMetric]:
        """Get a deepeval metric class by name."""
        # Try to import from deepeval.metrics
        try:
            # Handle common metric name mappings
            # These are convenience mappings for commonly used metrics
            metric_mappings = {
                "Relevancy": "AnswerRelevancyMetric",
                "Faithfulness": "FaithfulnessMetric",
                "ContextRecall": "ContextualRecallMetric",
                "ContextPrecision": "ContextualPrecisionMetric",
                "Hallucination": "HallucinationMetric",
                "Toxicity": "ToxicityMetric",
                "BiasMetric": "BiasMetric",
                "LatencyMetric": "LatencyMetric",
            }

            # Check if we have a mapping for this metric
            mapped_name = metric_mappings.get(metric_name, metric_name)

            # Try direct import
            module = importlib.import_module("deepeval.metrics")
            metric_class = getattr(module, mapped_name)
            return metric_class  # type: ignore
        except (ImportError, AttributeError):
            # Try importing from deepeval.metrics.ragas if it's a RAGAS metric
            try:
                module = importlib.import_module("deepeval.metrics.ragas")
                metric_class = getattr(module, metric_name)
                return metric_class  # type: ignore
            except (ImportError, AttributeError):
                raise ValueError(f"Could not find metric class: {metric_name}")

    def create_test_case(self, case: EvalCase, actual_output: str) -> LLMTestCase:
        """Create a deepeval test case from an eval case and actual output."""
        # Handle retrieval_context which can be string or list
        retrieval_context = case.retrieval_context
        if isinstance(retrieval_context, str):
            retrieval_context = [retrieval_context]

        return LLMTestCase(
            input=case.input,
            actual_output=actual_output,
            expected_output=case.expected_output,
            retrieval_context=retrieval_context,
            context=case.context,
            additional_metadata=case.additional_metadata,
        )

    def run_single_eval(
        self,
        model_name: str,
        model_config: AIModelConfig,
        coder_name: str,
        case: EvalCase,
        workdir: Path,
        coder_config: CoderConfig | None = None,
    ) -> List[EvalResult]:
        """Run evaluation for a single model x coder x case combination."""
        results = []

        # Create coder instance
        coder = create_coder(
            coder_name,
            workdir=str(workdir / f"{model_name}_{coder_name}_{case.name}"),
            config=coder_config,
        )

        # Set environment variables for the model
        coder.env = {
            "OPENAI_MODEL": model_config.name,
        }
        # Add provider info if available
        if model_config.provider:
            if isinstance(model_config.provider, str):
                coder.env["OPENAI_PROVIDER"] = model_config.provider
            elif hasattr(model_config.provider, "name"):
                coder.env["OPENAI_PROVIDER"] = model_config.provider.name

        # Run the coder
        logger.info(f"Running {coder_name} with {model_name} on case '{case.name}'")
        start_time = time.time()

        output: CoderOutput = coder.run(case.input)
        actual_output = output.result_text or output.stdout
        execution_time = time.time() - start_time

        # Run each metric
        for metric_name in case.metrics:
            if metric_name in METRICS:
                metric = METRICS[metric_name]
            else:
                # Get metric class and instantiate
                metric_class = self.get_metric_class(metric_name)
                metric = metric_class(threshold=case.threshold)  # type: ignore

            # Create test case
            test_case = self.create_test_case(case, actual_output)

            # Evaluate
            logger.info(f"Evaluating with {metric_name}")
            eval_results = evaluate([test_case], [metric])

            # Extract results - the structure varies by deepeval version
            test_result = eval_results.test_results[0]

            # Debug: log available attributes
            logger.debug(f"TestResult attributes: {dir(test_result)}")

            # Try different ways to extract the metric result
            # TODO: find a more principled way to extract the metric result
            if hasattr(test_result, "metrics_data") and test_result.metrics_data:
                # Newer deepeval structure
                metric_data = test_result.metrics_data[0]
                score = metric_data.score if hasattr(metric_data, "score") else 0.0
                passed = (
                    metric_data.success if hasattr(metric_data, "success") else False
                )
                reason = metric_data.reason if hasattr(metric_data, "reason") else None
            elif hasattr(test_result, "metrics") and test_result.metrics:
                # Alternative structure
                metric_obj = test_result.metrics[0]
                score = float(metric_obj.score) if hasattr(metric_obj, "score") else 0.0
                passed = score >= case.threshold
                reason = getattr(metric_obj, "reason", None)
            else:
                # Fallback - try to get from the test result directly
                score = getattr(test_result, "score", 0.0)
                passed = getattr(test_result, "success", False)
                reason = getattr(test_result, "reason", None)

            result = EvalResult(
                model=model_name,
                coder=coder_name,
                case_name=case.name,
                metric_name=metric_name,
                score=score if score is not None else 0.0,
                passed=passed,
                reason=reason,
                actual_output=actual_output,
                expected_output=case.expected_output,
                execution_time=execution_time,
                execution_metadata=output,
            )
            results.append(result)

        return results

    def run_all_evals(
        self,
        dataset: EvalDataset,
        workdir: Path = Path("./eval_workdir"),
        coders: Optional[List[str] | dict[str, dict[str, Any]]] = None,
    ) -> List[EvalResult]:
        """Run all evaluations in the dataset."""
        if coders is None:
            if dataset.coders is None:
                coders = {c: {} for c in AVAILABLE_CODERS.keys()}
            else:
                coders = dataset.coders
        if isinstance(coders, list):
            coders = {c: {} for c in coders}

        all_results = []

        # Create workdir if it doesn't exist
        workdir.mkdir(parents=True, exist_ok=True)

        # Determine server combinations to test
        server_combinations = []
        if dataset.server_combinations:
            # Use explicit server combinations
            server_combinations = copy.deepcopy(dataset.server_combinations)
        else:
            # Default behavior: test each server individually (including no server)
            server_combinations.append([])  # No servers
            for server_name in dataset.servers.keys():
                server_combinations.append([server_name])

        # Calculate total combinations including server combinations
        total_combinations = (
            len(dataset.models)
            * len(coders)
            * len(dataset.cases)
            * len(server_combinations)
        )
        current = 0

        for model_name, model_config in dataset.models.items():
            for coder_name, coder_config_base in coders.items():
                # Check if coder is available
                coder_class = AVAILABLE_CODERS.get(coder_name)
                if not coder_class or not coder_class.is_available():
                    logger.warning(f"Skipping {coder_name} - not available")
                    continue

                for server_combo in server_combinations:
                    # Create coder config with selected servers
                    coder_config = None
                    if server_combo:
                        # Import necessary classes
                        from metacoder.configuration import CoderConfig

                        # Build extensions list from selected servers
                        extensions = []
                        for server_name in server_combo:
                            if server_name in dataset.servers:
                                server = dataset.servers[server_name]
                                # Enable the server for this combination
                                server_copy = server.model_copy()
                                server_copy.enabled = True
                                extensions.append(server_copy)

                        # Create coder config with these extensions
                        coder_config = CoderConfig(
                            ai_model=model_config, extensions=extensions
                        )

                        # Merge with any base coder config
                        if coder_config_base:
                            # TODO: Implement proper config merging if needed
                            pass

                    for case in dataset.cases:
                        current += 1
                        server_desc = (
                            f" with servers: {', '.join(server_combo)}"
                            if server_combo
                            else " (no servers)"
                        )
                        logger.info(
                            f"Progress: {current}/{total_combinations} - {coder_name}/{model_name}/{case.name}{server_desc}"
                        )

                        # Create unique workdir for this combination
                        combo_workdir = workdir
                        if server_combo:
                            server_suffix = "_".join(server_combo)
                            combo_workdir = (
                                workdir
                                / f"{model_name}_{coder_name}_{case.name}_{server_suffix}"
                            )
                        else:
                            combo_workdir = (
                                workdir
                                / f"{model_name}_{coder_name}_{case.name}_no_servers"
                            )

                        results = self.run_single_eval(
                            model_name,
                            model_config,
                            coder_name,
                            case,
                            combo_workdir,
                            coder_config,
                        )

                        # Add server info to results
                        for result in results:
                            result.servers = server_combo

                        all_results.extend(results)

        return all_results

    def save_results(self, results: List[EvalResult], output_path: Path):
        """Save evaluation results to file."""
        # Convert to list of dicts
        results_data = []
        for result in results:
            results_data.append(result.model_dump())

        # Save as YAML
        with open(output_path, "w") as f:
            yaml.dump(
                {"results": results_data, "summary": self.generate_summary(results)},
                f,
                default_flow_style=False,
                sort_keys=False,
            )

    def generate_summary(self, results: List[EvalResult]) -> Dict[str, Any]:
        """Generate a summary of evaluation results."""
        summary: Dict[str, Any] = {
            "total_evaluations": len(results),
            "passed": sum(1 for r in results if r.passed),
            "failed": sum(1 for r in results if not r.passed),
            "errors": sum(1 for r in results if r.error is not None),
        }

        # Group by model
        by_model: Dict[str, Dict[str, int]] = {}
        for result in results:
            if result.model not in by_model:
                by_model[result.model] = {"passed": 0, "failed": 0, "total": 0}
            by_model[result.model]["total"] += 1
            if result.passed:
                by_model[result.model]["passed"] += 1
            else:
                by_model[result.model]["failed"] += 1
        summary["by_model"] = by_model

        # Group by coder
        by_coder: Dict[str, Dict[str, int]] = {}
        for result in results:
            if result.coder not in by_coder:
                by_coder[result.coder] = {"passed": 0, "failed": 0, "total": 0}
            by_coder[result.coder]["total"] += 1
            if result.passed:
                by_coder[result.coder]["passed"] += 1
            else:
                by_coder[result.coder]["failed"] += 1
        summary["by_coder"] = by_coder

        # Average scores by metric
        by_metric: Dict[str, Dict[str, Any]] = {}
        for result in results:
            if result.metric_name not in by_metric:
                by_metric[result.metric_name] = {"scores": [], "passed": 0, "failed": 0}
            if not result.error:
                by_metric[result.metric_name]["scores"].append(result.score)
            if result.passed:
                by_metric[result.metric_name]["passed"] += 1
            else:
                by_metric[result.metric_name]["failed"] += 1

        for metric, data in by_metric.items():
            scores = data["scores"]
            if scores:
                data["average_score"] = sum(scores) / len(scores)
            else:
                data["average_score"] = 0.0
            del data["scores"]  # Remove the list to keep summary clean

        summary["by_metric"] = by_metric

        return summary


def main():
    """CLI entry point for the eval runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Run metacoder evaluations")
    parser.add_argument("config", type=Path, help="Path to evaluation config YAML")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("eval_results.yaml"),
        help="Output file for results",
    )
    parser.add_argument(
        "-w",
        "--workdir",
        type=Path,
        default=Path("./eval_workdir"),
        help="Working directory for evaluations",
    )
    parser.add_argument("-c", "--coders", nargs="+", help="Specific coders to test")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    runner = EvalRunner(verbose=args.verbose)

    # Load dataset
    dataset = runner.load_dataset(args.config)

    # Run evaluations
    results = runner.run_all_evals(dataset, args.workdir, args.coders)

    # Save results
    runner.save_results(results, args.output)

    # Print summary
    summary = runner.generate_summary(results)
    print("\nEvaluation Complete!")
    print(f"Total: {summary['total_evaluations']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Errors: {summary['errors']}")
    print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
