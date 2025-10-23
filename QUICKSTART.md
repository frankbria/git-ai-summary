# Quick Start Guide

Get started with git-ai-summary in 3 steps!

## Step 1: Set Up Virtual Environment & Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source activate.sh
# Or manually: source venv/bin/activate

# Install dependencies (already done if venv exists)
pip install -r requirements.txt
```

## Step 2: Configure Your Provider

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your API key. Choose one of these popular options:

### Option A: OpenAI (GPT)
```env
DEFAULT_AI_PROVIDER=openai
OPENAI_API_KEY=sk-...your-key...
OPENAI_MODEL=gpt-4o-mini
```

### Option B: Anthropic (Claude)
```env
DEFAULT_AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...your-key...
ANTHROPIC_MODEL=claude-3-5-sonnet-latest
```

### Option C: Local Ollama (Free!)
```bash
# First, install and start Ollama
ollama run llama3.1:8b
```

```env
DEFAULT_AI_PROVIDER=ollama
OLLAMA_MODEL=llama3.1:8b
```

## Step 3: Run It!

From your git repository directory:

```bash
/path/to/git-ai-summary.py --provider anthropic
```

Or if Ollama:

```bash
/path/to/git-ai-summary.py --provider ollama
```

## Common Use Cases

### Analyze Recent Commits
```bash
./git-ai-summary.py --provider anthropic
```

### Focus on Security Issues
```bash
./git-ai-summary.py --provider openai --focus security
```

### Save Analysis to File
```bash
./git-ai-summary.py --provider anthropic --output analysis.md
```

### Use Different Model
```bash
./git-ai-summary.py --provider openai --model gpt-4
```

### Copy Prompt to Clipboard (for manual AI)

```bash
./git-ai-summary.py --copy
# Paste into ChatGPT, Claude web interface, etc.
```

### Copy AI Analysis to Clipboard

```bash
./git-ai-summary.py --provider anthropic --output-copy
```
## Where to Get API Keys

- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/settings/keys
- **OpenRouter**: https://openrouter.ai/keys
- **Google Gemini**: https://makersuite.google.com/app/apikey
- **Cohere**: https://dashboard.cohere.com/api-keys
- **Mistral**: https://console.mistral.ai/api-keys

## Troubleshooting

### "Configuration error: Provider X requires Y to be set"
- Check your `.env` file has the correct API key variable
- Make sure the `.env` file is in the same directory as the script

### "Connection failed"
- For Ollama: Make sure `ollama serve` is running
- For others: Check your internet connection

### "Authentication failed"
- Verify your API key is correct
- Check if you have credits/quota remaining

## Need Help?

See the full [README.md](README.md) for comprehensive documentation.
