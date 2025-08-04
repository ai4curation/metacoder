# Metacoder

A unified interface for AI coding assistants that abstracts over tool-specific configurations.

## Motivation

AI coding assistants like Goose, Claude, and others are powerful but each has its own configuration format, command-line interface, and setup requirements. Metacoder provides:

- **Unified CLI**: Single command interface for multiple AI coders
- **Configuration abstraction**: Consistent config format across different tools
- **Tool discovery**: Automatically detect which AI assistants are available
- **Simplified setup**: Manage working directories and contexts consistently

## Quick Start

```bash
# Install
pip install metacoder

# List available coders
metacoder list-coders

# Use with default coder (goose)
metacoder "Write a hello world program in Python"

# Use specific coder
metacoder "Fix the bug in main.py" --coder claude

# Use with config file
metacoder "Analyze this codebase" --config myconfig.yaml

# Use with MCP extensions
metacoder "Search for papers on transformers" --mcp-collection research_mcps.yaml
```

## Evaluations

Metacoder includes a powerful evaluation framework for comparing AI coders across different tasks and metrics:

```bash
# Run evaluations
metacoder eval tests/input/example_eval_config.yaml

# Test specific coders
metacoder eval my_evals.yaml -c claude -c goose

# Custom output location
metacoder eval my_evals.yaml -o results.yaml
```

Example evaluation config:

```yaml
name: pubmed tools evals
description: Testing coders with PubMed MCP integration

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
  - name: "title"
    metrics: [CorrectnessMetric]
    input: "What is the title of PMID:28027860?"
    expected_output: "From nocturnal frontal lobe epilepsy to Sleep-Related Hypermotor Epilepsy: A 35-year diagnostic challenge"
    threshold: 0.9
```

## Available Coders

- **goose** - Goose AI assistant
- **claude** - Anthropic's Claude
- **codex** - OpenAI Codex
- **gemini** - Google Gemini
- **qwen** - Alibaba Qwen
- **dummy** - Test implementation

## Installation

```bash
# Using pip
pip install metacoder

# Using uv
uv add metacoder
```

## Development

```bash
# Clone the repo
git clone https://github.com/cmungall/metacoder
cd metacoder

# Install with dev dependencies
uv add --dev .

# Run tests
uv run pytest

# Build docs
uv run mkdocs serve
```

## Documentation

Full documentation is available at [https://cmungall.github.io/metacoder](https://cmungall.github.io/metacoder)