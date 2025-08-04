# Configuration Reference

This page provides detailed documentation for evaluation configuration using the data models from `metacoder.evals.eval_model`.

## Configuration Models

The evaluation system uses Pydantic models for configuration validation and type safety.

### EvalCase

Individual test case configuration:

::: metacoder.evals.eval_model.EvalCase
    options:
      show_source: false
      show_root_heading: true
      members_order: source

### EvalDataset

Complete evaluation dataset configuration:

::: metacoder.evals.eval_model.EvalDataset
    options:
      show_source: false
      show_root_heading: true
      members_order: source

## Configuration File Structure

A complete evaluation configuration file contains:

```yaml
# Dataset metadata
name: string                    # Required: Name of the evaluation dataset
description: string             # Optional: Description of what's being tested

# Coders to test
coders:                         # Optional: Defaults to all available coders
  claude: {}                    # Empty dict uses default configuration
  goose: 
    custom_option: value        # Coder-specific configuration

# AI models configuration
models:                         # Required: At least one model
  model_name:
    provider: string            # Provider name (openai, anthropic, etc.)
    name: string                # Model identifier

# MCP servers
servers:                        # Optional: MCP server configurations
  server_name:
    name: string
    command: string
    args: [list]
    env: 
      KEY: value

# Test cases
cases:                          # Required: At least one test case
  - name: string                # Required: Unique case identifier
    metrics: [list]             # Required: List of metric names
    input: string               # Required: Input prompt/question
    expected_output: string     # Optional: Expected response
    retrieval_context: string|list  # Optional: Context for RAG metrics
    threshold: float            # Optional: Pass threshold (default: 0.7)
    context: [list]             # Optional: Additional context
    additional_metadata: dict   # Optional: Extra metadata
    comments: string            # Optional: Notes about the test
    tags: [list]                # Optional: Tags for filtering
```

## Field Details

### Model Configuration

The `models` field maps model names to their configurations:

```yaml
models:
  gpt-4o:
    provider: openai
    name: gpt-4
  claude-3:
    provider: anthropic
    name: claude-3-opus
```

### Server Configuration  

The `servers` field defines MCP servers available for evaluation:

```yaml
servers:
  pubmed:
    name: pubmed
    command: uvx
    args: [mcp-simple-pubmed]
    env:
      PUBMED_EMAIL: ${PUBMED_EMAIL}
    type: stdio
    enabled: true
```

### Metrics

Metrics can be specified by name. Common metrics include:

- `CorrectnessMetric` - Built-in factual accuracy metric
- `AnswerRelevancyMetric` - How well answer relates to question
- `FaithfulnessMetric` - Factual accuracy based on context
- `HallucinationMetric` - Detects false information
- `GEval` - Custom criteria evaluation

See [DeepEval metrics](https://deepeval.com/docs/metrics-introduction) for the complete list.

### Test Case Fields

- **name**: Unique identifier for the test case
- **metrics**: List of metric names to apply
- **input**: The prompt or question to send to the coder
- **expected_output**: The expected response (for comparison metrics)
- **retrieval_context**: Context documents for RAG metrics (string or list)
- **threshold**: Score threshold for passing (0.0-1.0, default 0.7)
- **additional_metadata**: Dictionary of extra data for custom metrics
- **comments**: Human-readable notes about the test
- **tags**: List of tags for categorization/filtering

## Command Line Usage

```bash
# Basic evaluation
metacoder eval config.yaml

# Specify output file
metacoder eval config.yaml -o results.yaml

# Test specific coders
metacoder eval config.yaml -c claude -c goose

# Custom working directory
metacoder eval config.yaml -w ./eval_workspace

# Verbose output
metacoder eval config.yaml -v
```

## See Also

- [Examples](examples.md) - Complete configuration examples
- [Evaluation Introduction](index.md) - Overview of the evaluation system