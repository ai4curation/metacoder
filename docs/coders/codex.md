# Codex

<img src="https://openai.com/favicon.ico" alt="OpenAI Logo" width="100" align="right"/>

OpenAI Codex integration.

## Installation

### NPM (Recommended)

```bash
npm install -g @openai/codex
```

### Homebrew (macOS)

```bash
brew install codex
```

### Direct Binary Download

Download the appropriate binary for your platform from the [latest GitHub Release](https://github.com/openai/codex/releases).

### Setup

After installation, set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key"
```

### Upgrade

To upgrade an existing installation:

```bash
codex --upgrade
```

**Note**: Codex officially supports macOS and Linux. Windows support is experimental and may require WSL2.

## Usage

```bash
metacoder "Your prompt" --coder codex
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key

### Config File

```yaml
ai_model:
  name: code-davinci-002
  provider:
    name: openai
    api_key: ${OPENAI_API_KEY}
```