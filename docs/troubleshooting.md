# Troubleshooting

This guide covers common issues and solutions when using Metacoder.

## Platform Compatibility

### OS issues

Metacoder relies heavily on subprocess calls to command-line tools and has only been tested on Unix-like platforms (Linux and macOS). There may be issues with Windows support due to:

- Path handling differences
- Shell command execution differences  
- Environment variable handling
- Process management differences

## Working Directory Issues

### Lock Files

Metacoder uses lock files (`.metacoder.lock`) to prevent multiple processes from running in the same working directory simultaneously. When you run a coder, it:

1. Creates a `.metacoder.lock` file containing the process ID
2. Runs the coder
3. Removes the `.metacoder.lock` file when complete

**Common Issues**:

- **"Lock file exists" error**: This occurs when a previous run was interrupted or crashed
- **Solution**: 
  ```bash
  # Check if process is still running
  cat workdir/.metacoder.lock  # Shows the process ID
  ps -p <PID>        # Check if process exists
  
  # If process is not running, remove the lock file
  rm workdir/.metacoder.lock
  ```

### Config File Cleanup

Metacoder automatically cleans up configuration files before each run. This means:

- Previous configuration files are deleted when `prepare_workdir()` is called
- Each run starts with a fresh configuration
- Any manual changes to config files in the workdir will be lost

**Config files that get cleaned** (varies by coder):
- Claude: `CLAUDE.md`, `.claude.json`, `.mcp.json`, `.claude/`
- Goose: `.goosehints`, `.settings/goose/`, `.settings/goose/config.yaml`
- Others have their own specific files

**Solution**: If you need persistent configuration:
- Use the configuration YAML files in your project root
- Pass configuration via the CLI or API
- Do not manually edit files in the working directory

## Feature Support Matrix

Not all features are implemented for all coders:

| Feature | Claude | Goose | Codex | Gemini | Qwen | Dummy |
|---------|---------|--------|--------|---------|--------|--------|
| MCP Support | ✅ | ✅ | ❌ | ❌ | ❌ | ✅* |
| Tool Use Capture | ✅ | ✅ | ❌ | ❌ | ❌ | ✅* |
| Cost Tracking | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Structured Output | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

*Dummy coder provides simulated support for testing

### MCP Extension Errors

If you configure MCP extensions for a coder that doesn't support them, you'll get:
```
ValueError: MCP extensions are configured but <CoderName> does not support MCP.
Found X enabled MCP extension(s).
Please use a coder that supports MCP (e.g., ClaudeCoder, GooseCoder) or remove MCP extensions from the configuration.
```

**Solution**: Either:
- Use a coder that supports MCP (Claude or Goose)
- Remove MCP extensions from your configuration
- Set `enabled: false` for all MCP extensions

## Unimplemented Features

### Subagents

Subagents are not currently implemented for any coder. The Claude coder has a TODO comment indicating future support.

**Current Status**: 
- No coder supports launching subagents
- Agent configuration directories (`.claude/agents`) are created but not used

### Tool Use for Some Coders

Only Claude and Goose coders capture tool use information. Other coders will have `tool_uses: None` in their output.

## Environment and Authentication Issues

### Missing Command-Line Tools

Each coder requires its specific CLI tool to be installed:

```python
# Check if a coder is available
from metacoder.registry import AVAILABLE_CODERS

for name, coder_class in AVAILABLE_CODERS.items():
    print(f"{name}: {'Available' if coder_class.is_available() else 'Not installed'}")
```

### Environment Variables

Different coders require different environment variables:

- **Claude**: May need AWS credentials in `~/.aws/` for Bedrock
- **Goose**: Copies AWS credentials if using Bedrock
- **Qwen**: Requires `OPENAI_API_KEY` (set to DASHSCOPE_API_KEY)
- **All**: API keys and provider settings via environment variables

**Solution**: Ensure required environment variables are set before running.

### Home Directory Override

Both Claude and Goose override the HOME environment variable; they will change to the working directory
and then effectively run

```bash
HOME=. claude|goose|... ...
```

This means:
- Config files are looked for in the working directory, not your actual home
- AWS credentials may need to be copied to the working directory

## Disk usage

Some coders make a lot of intermediate files, these can end up building up, taking up disk space. Clear workdir folders periodically

## Token usage

Agentic AI can burn through credits quickly. Currently the claude coder will report on total cost in dollars, but for now to get this out of
goose you need to extract the token usages from structured output and calculate this yourself.

## Debugging Tips


### Check Structured Messages

For Claude and Goose, check the `structured_messages` field in the output for detailed execution information:

```python
output = coder.run("your prompt")
if output.structured_messages:
    for msg in output.structured_messages:
        print(msg)
```

### Session Files

Goose saves session files that can be useful for debugging:
- Look for "logging to" in the output
- Session files are in `.local/share/goose/sessions/`
- Contains JSONL formatted messages

## Common Error Messages

### "Lock file exists"
**Cause**: Previous run didn't complete cleanly  
**Solution**: Remove the `.lock` file after verifying no process is running

### "MCP extensions are configured but X does not support MCP"
**Cause**: Using MCP with unsupported coder  
**Solution**: Use Claude or Goose, or disable MCP extensions

### "CalledProcessError"
**Cause**: The underlying CLI tool failed  
**Solution**: Check stderr in the output, ensure the CLI tool is properly installed and configured

### Config File Not Found
**Cause**: Config files are cleaned before each run  
**Solution**: Let Metacoder manage config files automatically

## TODO: Additional Sections

- **Performance Optimization**: Tips for faster execution
- **Network Issues**: Handling API timeouts and retries  
- **Custom Coder Development**: Debugging custom coder implementations
- **Integration Testing**: Best practices for testing with different coders