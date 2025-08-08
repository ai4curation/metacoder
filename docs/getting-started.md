# Getting Started

## Installation

TODO: release on PyPI

```bash
pip install metacoder
```

Bypass installation with `uvx`

```bash
uvx metacoder
```

## Check Available Coders

```bash
metacoder list-coders
```

This shows which AI assistants are installed and available.

For example:

```
Available coders:
  ✅ goose
  ✅ claude
  ✅ codex
  ✅ gemini
  ✅ qwen
  ✅ dummy
```

If you don't see the tick you will need to install the coding assistant.

## Basic Usage

```bash
# Use default coder
metacoder "Your prompt here"

# Use specific coder
metacoder "Your prompt" --coder claude

# Specify working directory
metacoder "Analyze this project" --workdir ./myproject

# Use configuration file
metacoder "Build feature X" --config config.yaml

# Use custom instructions file
metacoder "Review code" --instructions guidelines.md

# Use MCP extensions
metacoder "Search for papers on LLMs" --mcp-collection research_mcps.yaml
```

## Using MCP Extensions

Metacoder supports Model Context Protocol (MCP) servers that extend your AI coders with additional capabilities:

```bash
# Use all enabled MCPs from a collection
metacoder "Find recent AI papers" --mcp-collection mcps.yaml

# Enable specific MCPs only
metacoder "Search PMID:12345" --mcp-collection mcps.yaml --enable-mcp pubmed

# Combine with coder config
metacoder "Analyze database schema" --config claude_config.yaml --mcp-collection db_mcps.yaml
```

## Next Steps

- Learn about [supported coders](coders/index.md)
- Configure your assistants with [configuration files](configuration.md)
- Extend capabilities with [MCP support](mcps.md)