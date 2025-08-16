# Metacoder

![Metacoder Logo](docs/assets/metacoder-logo.png)

A unified interface for command line AI coding assistants (claude code, gemini-cli, codex, goose, qwen-coder)

Read [the Metacoder post on Medium](https://medium.com/@cmungall/we-love-vibe-coding-so-much-we-vibe-coded-a-wrapper-for-vibe-coders-we-call-it-metacoder-b9973591755a)

```bash
# Use default coder
metacoder "Write a Python function to calculate fibonacci numbers" -w my-scripts/
...

# list coders
metacoder list-coders
Available coders:
  ✅ goose
  ✅ claude
  ✅ codex
  ✅ gemini
  ✅ qwen
  ✅ dummy

# With a specific coder
metacoder "Write a Python function to calculate fibonacci numbers" -c claude -w my-scripts/
...

# With custom instructions
metacoder "Refactor this code" -c claude --instructions coding_guidelines.md -w my-repo
...

# Using MCPs (e.g. GitHub MCP)
metacoder "Fix issue 1234" -w path/to/my-repo --mcp-collection github_mcps.yaml
...

# Using coders for scientific QA, with a literature search MCP
metacoder "what diseases are associated with ITPR1 mutations" --mcp-collection lit_search_mcps.yaml
...
```

## Why Metacoder?

Each AI coding assistant has its own:

- Configuration format
- Command-line interface
- Working directory setup
- Means of configuring MCPs

Metacoder provides a single interface to multiple AI assistants. This makes it easier to:

- switch between agent tools in [GitHub actions pipelines](https://ai4curation.github.io/aidocs/how-tos/set-up-github-actions/)
- perform matrixed [evaluation](https://ai4curation.github.io/metacoder/evaluations) of different agents and/or MCPs on different tasks

One of the main use cases for metacoder is evaluating *semantic coding agents*, see:

Mungall, C. (2025, July 22). Open Knowledge Bases in the Age of Generative AI (BOSC/BOKR Keynote) (abridged version). Intelligent Systems for Molecular Biology 2025 (ISMB/ECCB2025), Liverpool, UK. Zenodo. <https://doi.org/10.5281/zenodo.16461373>

Mungall, C. (2025, May 28). How to make your KG interoperable: Ontologies and Semantic Standards. NIH Workshop on Knowledge Networks, Rockville. Zenodo. <https://doi.org/10.5281/zenodo.15554695>


## Features

- Unified CLI for all supported coders
- Consistent [configuration](https://ai4curation.github.io/metacoder/configuration) format (YAML-based)
- Unified [MCP configuration](https://ai4curation.github.io/metacoder/mcps)
- Standardized working directory management


## Evaluation Framework

Metacoder includes a comprehensive evaluation framework for systematically testing and comparing AI coders, MCPs, and models.

```bash
# Run evaluation suite
metacoder eval tests/input/example_eval_config.yaml
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

- [Installation and Setuphttps://ai4curation.github.io/metacoder/getting-started)
- [Supported Coders](https://ai4curation.github.io/metacoder/coders/)
- [Configuration Guide](https://ai4curation.github.io/metacoder/configuration)
- [MCP Support](https://ai4curation.github.io/metacoder/mcps) - Extend your AI coders with additional tools
- [Evaluations](https://ai4curation.github.io/metacoder/evaluations/) - Test and compare AI coders
