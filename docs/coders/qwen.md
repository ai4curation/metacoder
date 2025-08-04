# Qwen

<img src="https://avatars.githubusercontent.com/u/141221163?s=200&v=4" alt="Qwen Logo" width="100" align="right"/>

Alibaba Qwen AI assistant integration via qwen-code CLI.

## Installation

### Prerequisites

Ensure you have Node.js version 20 or higher installed.

### Global Installation (Recommended)

```bash
npm install -g @qwen-code/qwen-code
```

### Local Project Installation

```bash
npm i @qwen-code/qwen-code
```

### Usage

After installation, start Qwen Code by running:

```bash
qwen
```

### Notes

- **Token Usage**: Qwen Code may issue multiple API calls per cycle, resulting in higher token usage
- **Free Options**: 
  - ModelScope: 2,000 free API calls/day (mainland China)
  - OpenRouter: Up to 1,000 free API calls/day (worldwide)

## Usage

```bash
metacoder "Your prompt" --coder qwen
```

## Configuration

Qwen uses environment variables for configuration.

### Required Environment Variables

- `OPENAI_API_KEY` - Set to your DASHSCOPE_API_KEY
- `OPENAI_BASE_URL` - Defaults to `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
- `OPENAI_MODEL` - Defaults to `qwen3-coder-plus`

### Setting Up

```bash
# Export your Dashscope API key
export OPENAI_API_KEY="your-dashscope-api-key"

# Or set DASHSCOPE_API_KEY (will be used as OPENAI_API_KEY)
export DASHSCOPE_API_KEY="your-dashscope-api-key"
```

### Config File

While Qwen primarily uses environment variables, you can still use Metacoder config:

```yaml
env:
  OPENAI_API_KEY: ${DASHSCOPE_API_KEY}
  OPENAI_MODEL: qwen3-coder-plus
```

## Available Models

- `qwen3-coder-plus` (default)
- Other Qwen models as supported by Dashscope API

## Notes

- Qwen CLI doesn't provide structured output like some other coders
- Cost information is not available through the CLI