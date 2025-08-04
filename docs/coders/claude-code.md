# Claude Code

<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Claude_AI_logo.svg/1200px-Claude_AI_logo.svg.png" alt="Claude Logo" width="100" align="right"/>

Anthropic's Claude Code CLI integration with full MCP support.

## Installation

### NPM Install (Node.js 18+)

```bash
npm install -g @anthropic-ai/claude-code
```

### Native Install

For macOS, Linux, or WSL:

```bash
curl -fsSL claude.ai/install.sh | bash
```

For Windows PowerShell:

```powershell
irm https://claude.ai/install.ps1 | iex
```

After installation, start Claude Code by running `claude` in your project directory.

## Usage

```bash
metacoder "Your prompt" --coder claude
```

## Configuration

Claude Code supports several configuration methods:

### Environment Variables

- `ANTHROPIC_API_KEY` - Your Anthropic API key (for direct API access)
- AWS credentials may be needed for Bedrock deployment

### Configuration Files

Claude Code recognizes these files in your working directory:

- `CLAUDE.md` - Primary instructions for the assistant
- `.claude.json` - Claude-specific configuration
- `.claude/settings.json` - Additional settings
- `.mcp.json` - MCP server configuration (generated automatically)

### Basic Config

```yaml
ai_model:
  name: claude-3-opus
  provider:
    name: anthropic
    api_key: ${ANTHROPIC_API_KEY}
```

## MCP Support

Claude Code has native support for Model Context Protocol (MCP) servers. When you use MCPs with Claude through Metacoder:

1. MCP configurations are automatically converted to Claude's `.mcp.json` format
2. The `--dangerously-skip-permissions` flag is added when MCPs are enabled
3. MCPs run in the same working directory as your code

### Example with MCPs

```bash
# Use filesystem MCP for file access
metacoder "Analyze all Python files" \
  --coder claude \
  --mcp-collection dev_mcps.yaml \
  --enable-mcp filesystem
```

### MCP Configuration in Coder Config

```yaml
ai_model:
  name: claude-3-opus
  provider: anthropic

extensions:
  - name: github
    command: uvx
    args: [mcp-github]
    env:
      GITHUB_TOKEN: ${GITHUB_TOKEN}
    enabled: true
    type: stdio
```

For more details on MCP configuration, see the [MCP Support documentation](../mcps.md).

## AWS Bedrock Support

For AWS Bedrock deployment, you may need to copy or symlink your AWS credentials:

```bash
cp -r ~/.aws ./workdir/.aws
```

## Cost Tracking

Claude Code provides cost tracking information in its output, which Metacoder displays after each run.