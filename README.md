# Browser Automation Agent with Memory

A browser automation agent powered by local LLM (gpt-oss:20b via Ollama) that maintains action history and learns from failures.

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                     Each Loop                           │
├─────────────────────────────────────────────────────────┤
│  INPUT TO MODEL:                                        │
│    • Goal: "Post something on X"                        │
│    • Previous Actions: Last 10 actions taken            │
│    • Current Browser State: URL, title, elements        │
│    • Failure Context: If last action failed             │
│                                                         │
│  OUTPUT FROM MODEL:                                     │
│    • Single tool call: click(0) or type_text(1, "hi")   │
│                                                         │
│  EXECUTION:                                             │
│    • Execute action with automatic retry (click→js_click)│
│    • Update action history                              │
│    • Refresh browser state                              │
└─────────────────────────────────────────────────────────┘
```

## Key Features

- **Action Memory**: Maintains last 10 actions to provide context
- **Failure Recovery**: Tracks consecutive failures and suggests alternatives
- **Automatic Retry**: Falls back to js_click when regular click fails
- **Smart State Management**: Refreshes page state after most actions
- **Completion Detection**: Recognizes when tasks are done or impossible

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Make sure Ollama is running with gpt-oss:20b
ollama run gpt-oss:20b
```

## Usage

Edit the `PROMPT` in `Prompts_gpt20b.py`:

```python
PROMPT = "post something on x. User name example@gmail.com and password is ****"
```

Then run:

```bash
python brain_with_eyes_hands.py
```

## Files

| File | Description |
|------|-------------|
| `brain_with_eyes_hands.py` | Main agent loop with memory and retry logic |
| `tools.py` | Browser automation functions (Selenium) |
| `Prompts_gpt20b.py` | System prompt, tools schema, and goal |
| `requirements.txt` | Python dependencies |

## Architecture

### Memory System
- **Action History**: Last 10 actions stored in `signals_from_hand`
- **Failure Tracking**: Consecutive failures trigger alternative approach prompts
- **Context Window**: Each model call receives goal + history + current state

### Decision Loop
1. **Eyes** (`get_page_state`): Capture current browser state
2. **Brain** (LLM): Decide next action based on goal + history + state
3. **Hands** (tools): Execute the action with automatic retry
4. **Memory**: Store result and update failure tracking
5. Repeat until task complete or failed

### Retry Logic
When `click()` fails, automatically tries `js_click()` as fallback:
```python
if organ == "click" and "✗" in turn_the_page:
    retry_turn_the_page = await js_click(organ_signals["element_index"])
```

## Example Flow

```
Loop 1: Eyes see Google homepage → Brain: type "twitter" in search
Loop 2: Eyes see search results → Brain: click first result
Loop 3: Eyes see Twitter login → Brain: type username
Loop 4: Eyes see password field → Brain: type password
Loop 5: Eyes see login button → Brain: click login
...
```

## Tool Categories

| Category | Tools |
|----------|-------|
| **Navigation** | `scroll`, `go_back` |
| **Interaction** | `click`, `js_click`, `type_text`, `press_key`, `hover` |
| **Perception** | `get_page_state`, `find_elements_by_text`, `click_element_with_text` |
| **Special** | `upload_file_auto`, `handle_alert` |
| **Completion** | `task_complete`, `task_failed` |

## Metaphor

The code uses a biological metaphor:
- **Brain**: LLM making decisions
- **Eyes**: DOM state observation
- **Hands**: Action execution (click, type, etc.)
- **Signals**: Data flowing between components
- **Nerves**: Function calls connecting brain to organs

## Configuration

Edit `Prompts_gpt20b.py` to customize:
- `SYSTEM_PROMPT`: Agent behavior and rules
- `PROMPT`: Your automation goal
- `BROWSER_TOOLS`: Available tools and their schemas

## Requirements

- Python 3.8+
- Selenium WebDriver
- Ollama with gpt-oss:20b model running on `localhost:11434`
- Chrome/Chromium browser