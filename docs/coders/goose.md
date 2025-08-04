# Goose

<img src="https://block.github.io/goose/img/logo_light.png" alt="Goose Logo" width="100" align="right"/>

Goose AI coding assistant integration.

## Installation

### macOS/Linux

```bash
curl -fsSL https://github.com/block/goose/releases/download/stable/download_cli.sh | bash
```

### Windows

Run in Git Bash, MSYS2, or PowerShell:

```bash
curl -fsSL https://github.com/block/goose/releases/download/stable/download_cli.sh | bash
```

### Silent Installation

For non-interactive installation:

```bash
curl -fsSL https://github.com/block/goose/releases/download/stable/download_cli.sh | CONFIGURE=false bash
```

After installation, you can update Goose with:

```bash
goose update
```

## Usage

```bash
metacoder "Your prompt" --coder goose
```

## Configuration

Goose configuration is automatically generated in the working directory.

### Default Configuration

- Model: `gpt-4o`
- Provider: `openai`
- Extensions: developer, pdfreader

### Custom Configuration

Use a Metacoder config file to override defaults:

```yaml
ai_model:
  name: gpt-4o
  provider:
    name: openai
    api_key: your-key
```