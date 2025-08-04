# Evaluations

Metacoder provides a powerful evaluation framework built on [DeepEval](https://github.com/confident-ai/deepeval), the open-source LLM evaluation framework. This integration enables systematic testing of AI coders across different models, tasks, and metrics.

## Why Evaluate AI Coders?

Evaluating AI coding assistants is crucial for:

- **Performance Comparison**: Compare different coders on the same tasks
- **Model Selection**: Test various LLMs to find the best fit
- **Regression Testing**: Ensure changes don't degrade performance
- **Tool Integration**: Validate MCP and tool usage accuracy
- **Reproducible Research**: Create benchmarks for academic papers

## Key Features

- **40+ Ready-to-Use Metrics**: Access DeepEval's comprehensive metric suite
- **LLM-Powered Evaluation**: Use any LLM to judge outputs with human-like accuracy
- **Flexible Integration**: Compatible with all DeepEval metrics and custom evaluations
- **Reproducible Benchmarks**: Systematic testing across model × coder × case × metric combinations
- **MCP Support**: Test coders with external tools and services

## How It Works

The evaluation system runs a matrix of tests:

1. **Models**: Different AI models (GPT-4, Claude, etc.)
2. **Coders**: Various coding assistants (Claude Code, Goose, Codex, etc.)
3. **Cases**: Test scenarios with inputs and expected outputs
4. **Metrics**: Quality measures from DeepEval

Each combination produces a scored result, enabling comprehensive comparisons.

## Quick Start

```bash
# Run evaluation suite
metacoder eval tests/input/example_eval_config.yaml

# Compare specific coders
metacoder eval my_evals.yaml -c claude -c goose

# Custom output location
metacoder eval my_evals.yaml -o results.yaml
```

## DeepEval Integration

Metacoder's evaluation system leverages DeepEval's powerful features:

- **Dynamic Metric Loading**: Any DeepEval metric can be used by name
- **LLMTestCase Compatibility**: Our `EvalCase` model maps to DeepEval's test case format
- **Flexible Scoring**: All DeepEval scoring mechanisms and thresholds are supported
- **Custom Metrics**: Create your own metrics using DeepEval's abstractions

## Next Steps

- [Examples](examples.md) - See complete evaluation configurations
- [Configuration Reference](configuration.md) - Detailed API documentation
- [DeepEval Documentation](https://deepeval.com/docs/) - Learn about available metrics