# Stateless Browser Automation Agent

A reactive browser automation agent powered by local LLM (gpt-oss:20b via Ollama). No conversation history - the model decides actions purely from the current browser state and goal.

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                     Each Loop                           │
├─────────────────────────────────────────────────────────┤
│  INPUT TO MODEL:                                        │
│    • Goal: "Search for weather on google"               │
│    • Browser State: URL, title, [0] input, [1] button   │
│                                                         │
│  OUTPUT FROM MODEL:                                     │
│    • Single tool call: type_text(0, "weather")          │
└─────────────────────────────────────────────────────────┘
```

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Make sure Ollama is running with gpt-oss:20b
ollama run gpt-oss:20b
```

## Usage

```bash
python agent.py
# Enter goal: Go to google.com and search for 'python tutorial'
```

## Files

| File | Description |
|------|-------------|
| `agent.py` | Main event loop - stateless agent |
| `tools.py` | Browser automation functions (Selenium) |
| `tool_schemas.py` | OpenAI-compatible tool definitions |

## Architecture

- **Stateless**: No conversation history, model sees only current state
- **Reactive**: Decides next action based on what's on screen
- **Simple loop**: `get_state → call_model → execute_tool → repeat`

## Git Commit

```
feat: stateless browser agent with local LLM tool calling
```