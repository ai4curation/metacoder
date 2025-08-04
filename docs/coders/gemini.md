# Gemini

<img src="https://www.gstatic.com/ai/web/favicons/favicon-32x32.png" alt="Gemini Logo" width="100" align="right"/>

Google Gemini AI assistant integration.

## Installation

### Node.js (v20+)

Install globally:

```bash
npm install -g @google/gemini-cli
```

Or run directly with npx:

```bash
npx https://github.com/google-gemini/gemini-cli
```

### Homebrew

```bash
brew install gemini-cli
```

### Setup

After installation, run `gemini` to:
1. Pick a color theme
2. Authenticate with your Google account

### API Keys (Optional)

- **Gemini API**: Get a key from [Google AI Studio](https://aistudio.google.com)
- **Vertex AI**: Get a key from [Google Cloud](https://cloud.google.com)

**Note**: When authenticated, you get up to 60 requests per minute and 1,000 requests per day.

## Usage

```bash
metacoder "Your prompt" --coder gemini
```

## Configuration

Gemini configuration is automatically generated in the working directory.

### Default Configuration

The coder creates a `.codex/config.yaml` file with:
- Model: `gemini-2.5-pro`
- Provider: `google`

### Environment Variables

Set your Google API credentials as needed.

### Custom Configuration

Use a Metacoder config file to override defaults:

```yaml
ai_model:
  name: gemini-2.5-pro
  provider:
    name: google
    api_key: ${GOOGLE_API_KEY}
```

## Notes

- Gemini CLI provides debug output that is parsed to extract results
- The coder expects configuration in `.codex/config.yaml`