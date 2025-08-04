# Configuration

Metacoder uses YAML configuration files to configure AI assistants and their extensions.

## Configuration File Format

### Basic Configuration

```yaml
ai_model:
  name: model-name
  provider:
    name: provider-name
    api_key: your-api-key
```

### Extensions (MCPs)

You can extend coders with Model Context Protocol (MCP) servers:

```yaml
ai_model:
  name: gpt-4
  provider: openai

extensions:
  - name: filesystem
    command: npx
    args: [-y, "@modelcontextprotocol/server-filesystem"]
    enabled: true
    type: stdio
    
  - name: github
    command: uvx
    args: [mcp-github]
    env:
      GITHUB_TOKEN: ${GITHUB_TOKEN}
    enabled: true
    type: stdio
```

For detailed information about MCP configuration and usage, see the [MCP Support documentation](mcps.md).

## Using Config Files

```bash
metacoder "Your prompt" --config myconfig.yaml
```

## Environment Variables

Config files support environment variable expansion:

```yaml
ai_model:
  provider:
    api_key: ${OPENAI_API_KEY}
```

## Per-Coder Defaults

Each coder has default configurations that are automatically applied. Custom configs override these defaults.