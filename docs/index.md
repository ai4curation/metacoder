# Metacoder

A unified interface for command line AI coding assistants (claude code, gemini-cli, codex, goose, qwen-coder)

## Why Metacoder?

Each AI coding assistant has its own:

- Configuration format
- Command-line interface
- Working directory setup
- API keys and authentication

Metacoder provides a single interface to multiple AI assistants. This makes it easier to:

- switch between agent tools in GitHub actions pipelines
- perform matrixed evaluation of different agents on different tasks

One of the main use cases for metacoder is evaluating *semantic coding agents*, see:

Mungall, C. (2025, July 22). Open Knowledge Bases in the Age of Generative AI (BOSC/BOKR Keynote) (abridged version). Intelligent Systems for Molecular Biology 2025 (ISMB/ECCB2025), Liverpool, UK. Zenodo. <https://doi.org/10.5281/zenodo.16461373>

Mungall, C. (2025, May 28). How to make your KG interoperable: Ontologies and Semantic Standards. NIH Workshop on Knowledge Networks, Rockville. Zenodo. <https://doi.org/10.5281/zenodo.15554695>


## Features

- Unified CLI for all supported coders
- Consistent configuration format
- Unified MCP configuration
- Standardized working directory management

## Warning

Like any framework that will run MCPs, this should be used with caution, ideally in a sanbox environment.
Care should be taken to vet any MCPs used for malicious behavior.

## Quick Example

```bash
# Use any available coder
metacoder "Write a Python function to calculate fibonacci numbers"

# Specify a particular coder
metacoder "Debug this TypeScript code" --coder claude

# Use MCP extensions for enhanced capabilities
metacoder "Search for papers on transformers" --mcp-collection research_mcps.yaml
```

## Evaluations

Metacoder includes a comprehensive evaluation framework for systematically testing and comparing AI coders:

```bash
# Run evaluation suite
metacoder eval tests/input/example_eval_config.yaml

# Compare specific coders
metacoder eval my_evals.yaml -c claude -c goose -o comparison_results.yaml
```

Example evaluation configuration:

```yaml
name: pubmed tools evals
description: Testing coders with PubMed MCP integration

coders:
  claude: {}
  goose: {}

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
  - name: "title"
    metrics: [CorrectnessMetric]
    input: "What is the title of PMID:28027860?"
    expected_output: "From nocturnal frontal lobe epilepsy to Sleep-Related Hypermotor Epilepsy: A 35-year diagnostic challenge"
    threshold: 0.9
```

## Getting Started

- [Installation and Setup](getting-started.md)
- [Supported Coders](coders/index.md)
- [Configuration Guide](configuration.md)
- [MCP Support](mcps.md) - Extend your AI coders with additional tools
- [Evaluations](evaluations/index.md) - Test and compare AI coders