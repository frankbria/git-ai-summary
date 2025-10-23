# Clipboard & Output Quick Reference

## Understanding the Options

| Option | What it does | Use case |
|--------|-------------|----------|
| `--copy` | Copy **prompt** to clipboard | Paste into ChatGPT/Claude web UI |
| `--output-copy` | Copy **AI analysis** to clipboard | Share results quickly |
| `--output` | Save **AI analysis** to file | Keep permanent record |
| (none) | Print **AI analysis** to screen | Quick viewing |

## Common Workflows

### 1. Manual AI Input (No API key needed)
```bash
# Copy prompt to paste into ChatGPT web interface
./git-ai-summary.py --copy
```
Then paste into ChatGPT, Claude, or any AI interface.

### 2. Automated Analysis to Screen
```bash
# Get AI analysis printed to terminal
./git-ai-summary.py --provider anthropic
```

### 3. Save Analysis to File
```bash
# Get AI analysis and save to markdown file
./git-ai-summary.py --provider openai --output report.md
```

### 4. Copy Analysis to Clipboard
```bash
# Get AI analysis and copy to clipboard for sharing
./git-ai-summary.py --provider anthropic --output-copy
```

### 5. Save AND Copy Analysis
```bash
# Get AI analysis, save to file, and copy to clipboard
./git-ai-summary.py --provider openai --output report.md --output-copy
```

### 6. Hybrid Approach
```bash
# Copy prompt for manual AI (backup/comparison)
./git-ai-summary.py --copy

# Also get automated analysis
./git-ai-summary.py --provider anthropic --output analysis.md
```

## Visual Flow

```
Your Git Commits
       ↓
   Script generates PROMPT
       ↓
       ├─ --copy → Clipboard (prompt) → Paste into AI manually
       │
       └─ --provider specified
              ↓
          AI generates ANALYSIS
              ↓
              ├─ (default) → Screen
              ├─ --output → File
              └─ --output-copy → Clipboard
```

## Troubleshooting

### Clipboard not working?

**Linux (Ubuntu):**
```bash
# Install xclip
sudo apt-get install xclip
```

**macOS:**
pbcopy is built-in, no installation needed.

### When to use what?

**Use `--copy` when:**
- You don't have an API key
- You want to use web-based AI interfaces
- You want to compare multiple AI providers manually

**Use `--output-copy` when:**
- You have an API key configured
- You want to share the AI analysis quickly
- You're pasting results into another tool/document

**Use `--output` when:**
- You want a permanent record
- You're generating reports
- You want to track analysis over time

## Examples by Scenario

### Scenario: Code review preparation
```bash
# Save analysis to file for PR description
./git-ai-summary.py --provider anthropic --since origin/main --output pr-summary.md
```

### Scenario: Security audit
```bash
# Focus on security, save and copy
./git-ai-summary.py --provider openai --focus security --output security-audit.md --output-copy
```

### Scenario: Quick team update
```bash
# Copy analysis to paste into Slack/Discord
./git-ai-summary.py --provider anthropic --output-copy
```

### Scenario: Compare AI providers
```bash
# Copy prompt, then try different AIs manually
./git-ai-summary.py --copy
# Paste into ChatGPT, Claude, Gemini, etc. to compare outputs
```

### Scenario: No API key available
```bash
# Copy prompt to use with free AI web interfaces
./git-ai-summary.py --copy
```
