# API Reference

## CLI Commands

### metacoder

Main command with subcommands for AI coding assistants.

```bash
metacoder [OPTIONS] COMMAND [ARGS]...
```

#### Global Options

- `--version` - Show version
- `--help` - Show help

#### Subcommands

##### run (default)

Run a prompt with the specified coder. This is the default command if no subcommand is specified.

```bash
metacoder [run] [OPTIONS] PROMPT
```

**Arguments:**
- `PROMPT` - The prompt to send to the AI assistant

**Options:**
- `-c, --coder` - Choose coder (goose, claude, codex, dummy)
- `-f, --config` - Path to configuration file
- `-w, --workdir` - Working directory (default: ./workdir)
- `-v, --verbose` - Enable verbose logging
- `--help` - Show help

##### list-coders

List available coders and their installation status.

```bash
metacoder list-coders
```

## Python API

### BaseCoder

Base class for all coders.

```python
from metacoder.coders.base_coder import BaseCoder

class MyCoder(BaseCoder):
    def run(self, prompt: str) -> CoderOutput:
        # Implementation
        pass
```

### CoderOutput

Output from coder execution.

```python
from metacoder.coders.base_coder import CoderOutput

output = CoderOutput(
    stdout="...",
    stderr="...",
    result_text="...",
    total_cost_usd=0.01,
    success=True
)
```