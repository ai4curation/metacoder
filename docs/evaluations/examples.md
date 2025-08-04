# Evaluation Examples

This page provides complete examples of evaluation configurations for different use cases.

## Basic Example: PubMed Tools Evaluation

Testing AI coders with MCP integration for scientific literature search:

```yaml
name: pubmed tools evals
description: |
  Evaluations for multiple pubmed MCPs

coders:
  claude: {}

models:
  gpt-4o:
    provider: openai
    name: gpt-4

servers:
  pubmed:
    name: pubmed
    command: uvx
    args: [mcp-simple-pubmed]
    env:
      PUBMED_EMAIL: user@example.com

cases:
  - name: "sanity"
    metrics: [CorrectnessMetric]
    input: "What is 1+1"
    expected_output: "2"
    threshold: 0.9
    
  - name: "title"
    metrics: [CorrectnessMetric]
    input: "What is the title of PMID:28027860?"
    expected_output: "From nocturnal frontal lobe epilepsy to Sleep-Related Hypermotor Epilepsy: A 35-year diagnostic challenge"
    threshold: 0.9
    
  - name: "table"
    metrics: [CorrectnessMetric]
    input: "In table 2 of PMID:28027860, what are the 3 levels of certainty"
    expected_output: "Witnessed (possible); Video-documented (clinical); Video-EEG documented (confirmed)"
    threshold: 0.9
```

## Multi-Coder Comparison

Compare multiple coders on the same tasks:

```yaml
name: coder comparison
description: Compare Claude and Goose on coding tasks

coders:
  claude: {}
  goose: {}
  codex: {}  ## TODO: codex does yet support MCPs

models:
  gpt-4o:
    provider: openai
    name: gpt-4
  claude-3:
    provider: anthropic  
    name: claude-3-opus

cases:
  - name: "fibonacci"
    metrics: [CorrectnessMetric]
    input: "Write a Python function to calculate the nth Fibonacci number"
    expected_output: |
      def fibonacci(n):
          if n <= 1:
              return n
          return fibonacci(n-1) + fibonacci(n-2)
    threshold: 0.8
```



## Running Examples

### Basic Run

```bash
metacoder eval examples/pubmed_eval.yaml -o results.yaml
```

### Compare Specific Coders

If there is no `coders:` section in your yaml you can do this:

```bash
metacoder eval examples/coder_comparison.yaml -c claude -c goose
```

### Verbose Output with Custom Directory

```bash
metacoder eval examples/coder_comparison.yaml -v -w ./my_workspace -o results.yaml
```

## Best Practices

1. **Start Simple**: Begin with basic sanity checks
2. **Choose Metrics Wisely**: Use 2-3 system-specific, 1-2 use-case specific metrics
3. **Set Appropriate Thresholds**: Adjust based on task difficulty (0.7-0.9 typical)
4. **Include Edge Cases**: Test error handling and boundary conditions
5. **Use Descriptive Names**: Make test cases self-documenting

## See Also

- [Configuration Reference](configuration.md) - Detailed API documentation
- [Available Metrics](https://deepeval.com/docs/metrics-introduction) - Complete DeepEval metrics list