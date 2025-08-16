# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Metacoder is a unified interface for command-line AI coding assistants (claude code, gemini-cli, codex, goose, qwen-coder). It provides consistent configuration, MCP support, and evaluation capabilities across different AI coders.

## Development Commands

### Testing
```bash
# Run all tests (pytest, doctests, format check, mypy)
make test

# Run pytest only
uv run pytest

# Run specific test file
uv run pytest tests/test_specific.py

# Run tests marked as LLM tests (excluded by default)
uv run pytest -m llm

# Run integration tests
uv run pytest -m integration
```

### Code Quality
```bash
# Run type checking
uv run mypy src tests

# Run linting
uv run ruff check .

# Format check
make format
```

### Documentation
```bash
# Serve documentation locally
make serve
# or
uv run mkdocs serve

# Build documentation
uv run mkdocs build
```

## Architecture

### Core Components

1. **Coders** (`src/metacoder/coders/`): Implementations for different AI assistants
   - `base_coder.py`: Abstract base class defining the coder interface
   - `claude.py`, `gemini.py`, `goose.py`, `qwen.py`, `codex.py`: Specific implementations
   - Each coder handles its own configuration format and MCP setup

2. **Configuration** (`src/metacoder/configuration.py`): 
   - Pydantic models for configuration validation
   - `CoderConfig`: Main configuration for coders
   - `MCPConfig`: MCP server configuration
   - `MCPCollectionConfig`: Groups of MCP servers

3. **MCP Support** (`src/metacoder/mcps/`):
   - Registry of pre-configured MCPs in `registry/` (basics.yaml, ontology.yaml, scilit.yaml)
   - MCP demo implementation in `demo_lookup.py`

4. **Evaluation Framework** (`src/metacoder/evals/`):
   - `runner.py`: Main evaluation runner using deepeval
   - `eval_model.py`: Evaluation configuration models
   - Supports testing coders with different models and MCPs

5. **CLI** (`src/metacoder/metacoder.py`):
   - Main entry point with Click-based CLI
   - Commands: run tasks, list coders, evaluate, introspect MCPs

### Key Design Patterns

- **Abstract Base Class**: All coders inherit from `BaseCoder` providing consistent interface
- **Configuration-Driven**: YAML-based configuration for coders, MCPs, and evaluations
- **Tool Use Tracking**: Coders can track and report tool/MCP invocations
- **Working Directory Management**: Lock-based system to prevent concurrent operations
- **MCP Registry**: Pre-configured MCP servers available via registry path (e.g., `metacoder.basics`)

## Testing Guidelines

- Tests are organized by component in `tests/` subdirectories
- Use pytest markers for categorization (llm, integration)
- LLM tests are excluded by default (run with `uv run pytest -m llm`)
- Mock external dependencies when possible

## Dependencies

This project uses `uv` for dependency management. Key dependencies:
- `click`: CLI framework
- `pydantic`: Configuration validation
- `deepeval`: Evaluation framework
- `fastmcp`: MCP support
- Development: `pytest`, `mypy`, `ruff`, `mkdocs`