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

## Custom Instructions

You can provide custom instructions to any coder using the `--instructions` option:

```bash
metacoder "Your prompt" --instructions custom_instructions.md
```

The instructions file is loaded and passed to the coder's instruction handling mechanism. Each coder will use these instructions according to its own configuration:

- **Claude**: Instructions are written to `CLAUDE.md`
- **Goose**: Instructions are written to `.goosehints`
- **Gemini**: Instructions are written to `GEMINI.md`
- **Other coders**: Check the specific coder documentation

Example instructions file:

```markdown
# Custom Instructions

You are an expert Python developer following these guidelines:
1. Use type hints for all functions
2. Write comprehensive docstrings
3. Follow PEP 8 style guidelines
4. Include unit tests for all new functions
```

You can combine instructions with other configuration options:

```bash
metacoder "Refactor this code" \
  --coder claude \
  --instructions style_guide.md \
  --config claude_config.yaml \
  --mcp-collection tools.yaml
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