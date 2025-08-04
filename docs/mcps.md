# Model Context Protocol (MCP) Support

## Overview

Model Context Protocol (MCP) is a standard protocol that enables Large Language Models (LLMs) to securely access external data sources and tools. Metacoder provides first-class support for MCPs, allowing you to extend your AI coders with additional capabilities like database access, API integrations, and specialized tools.

## What are MCPs?

MCPs are server programs that expose specific functionality to AI systems through a standardized interface. They can provide:

- **Data access**: Query databases, search engines, or APIs
- **Tool usage**: Execute commands, manipulate files, or perform calculations
- **Domain-specific capabilities**: Access specialized knowledge bases or perform domain-specific operations

## MCP Configuration

### Basic Structure

MCPs are configured using the `MCPConfig` data model:

```yaml
name: my_mcp          # Unique identifier
description: "..."    # Optional description
command: uvx         # Command to launch the MCP
args: [mcp-example]  # Arguments for the command
env:                 # Environment variables
  API_KEY: ${API_KEY}
enabled: true        # Whether to enable this MCP
type: stdio          # Protocol type (stdio or http)
timeout: 30          # Optional timeout in seconds
```

### MCP Collections

You can organize multiple MCPs into collections using `MCPCollectionConfig`:

```yaml
name: my_mcp_collection
description: "Collection of research tools"
servers:
  - name: pubmed
    command: uvx
    args: [mcp-simple-pubmed]
    env:
      PUBMED_EMAIL: user@example.com
    enabled: true
    type: stdio
    
  - name: arxiv
    command: uvx
    args: [mcp-arxiv]
    enabled: true
    type: stdio
```

## Using MCPs with Metacoder

### Command Line Usage

There are several ways to use MCPs with the `metacoder run` command:

#### 1. Using MCP Collections

Load all enabled MCPs from a collection file:

```bash
metacoder run "Search for papers on transformers" \
  --mcp-collection research_mcps.yaml
```

#### 2. Selective MCP Enabling

Enable only specific MCPs from a collection:

```bash
metacoder run "Find PMID:12345678" \
  --mcp-collection research_mcps.yaml \
  --enable-mcp pubmed
```

You can enable multiple MCPs:

```bash
metacoder run "Research quantum computing" \
  --mcp-collection research_mcps.yaml \
  --enable-mcp arxiv \
  --enable-mcp pubmed
```

#### 3. Combining with Coder Config

MCPs can be combined with existing coder configurations:

```bash
metacoder run "Analyze the paper" \
  --config my_coder_config.yaml \
  --mcp-collection research_mcps.yaml
```

### Configuration File Usage

You can also include MCPs directly in your coder configuration:

```yaml
# coder_config.yaml
ai_model:
  name: gpt-4
  provider: openai

extensions:
  - name: filesystem
    command: npx
    args: [-y, "@modelcontextprotocol/server-filesystem"]
    enabled: true
    type: stdio
```

## Available MCP Servers

Here are some commonly used MCP servers:

### Research & Data

- **mcp-simple-pubmed**: Search and retrieve PubMed articles
- **mcp-arxiv**: Search ArXiv preprints
- **mcp-google-search**: Web search capabilities

### Development Tools

- **@modelcontextprotocol/server-filesystem**: File system access
- **mcp-github**: GitHub repository access
- **mcp-git**: Git operations

### Data Analysis

- **mcp-sqlite**: SQLite database access
- **mcp-postgres**: PostgreSQL database access

## Security Considerations

1. **Environment Variables**: MCPs can access environment variables specified in their configuration. Use `${VAR_NAME}` syntax to reference environment variables safely.

2. **Permissions**: Some coders (like Claude) may require additional permissions to use MCPs. The `--dangerously-skip-permissions` flag is automatically added when needed.

3. **Enabling MCPs**: By default, only MCPs with `enabled: true` are activated. Use the `--enable-mcp` flag to selectively enable specific MCPs.

## Examples

### Example 1: Research Assistant

Create a collection of research tools:

```yaml
# research_mcps.yaml
name: research_tools
description: "MCPs for academic research"
servers:
  - name: pubmed
    command: uvx
    args: [mcp-simple-pubmed]
    env:
      PUBMED_EMAIL: ${PUBMED_EMAIL}
    enabled: true
    type: stdio
    
  - name: arxiv
    command: uvx
    args: [mcp-arxiv]
    enabled: true
    type: stdio
    
  - name: semantic_scholar
    command: uvx
    args: [mcp-semantic-scholar]
    env:
      S2_API_KEY: ${S2_API_KEY}
    enabled: false  # Disabled by default
    type: stdio
```

Use it for literature review:

```bash
# Search across all enabled sources
metacoder run "Find recent papers on protein folding with AlphaFold" \
  --mcp-collection research_mcps.yaml \
  --coder claude

# Use only PubMed
metacoder run "What are the side effects mentioned in PMID:12345678?" \
  --mcp-collection research_mcps.yaml \
  --enable-mcp pubmed \
  --coder claude
```

### Example 2: Development Environment

Create a development-focused MCP collection:

```yaml
# dev_mcps.yaml
name: development_tools
description: "MCPs for software development"
servers:
  - name: filesystem
    command: npx
    args: [-y, "@modelcontextprotocol/server-filesystem"]
    enabled: false  # Enable only when needed
    type: stdio
    
  - name: github
    command: uvx
    args: [mcp-github]
    env:
      GITHUB_TOKEN: ${GITHUB_TOKEN}
    enabled: true
    type: stdio
```

## Troubleshooting

### MCP Not Found

If an MCP command is not found, ensure:
1. The MCP package is installed (e.g., `uvx` or `npx` is available)
2. The MCP server name is correct
3. Required environment variables are set

### Permission Errors

Some coders may require additional permissions to use MCPs. Check the coder-specific documentation for details.

### Environment Variables

If an MCP requires environment variables:
1. Export them in your shell: `export PUBMED_EMAIL=user@example.com`
2. Or use a `.env` file with appropriate tooling
3. Verify they're available: `echo $PUBMED_EMAIL`

## See Also

- [Claude MCP Support](coders/claude-code.md#mcp-support) - Claude-specific MCP configuration
- [Configuration Guide](configuration.md) - General configuration options
- [Model Context Protocol Specification](https://modelcontextprotocol.io) - Official MCP documentation