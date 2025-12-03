"""
Stateless Browser Automation Agent
Each loop: goal + current browser state → model → single tool action
"""

import asyncio
import requests
from tool_schemas import BROWSER_TOOLS

# Import all tool functions
from tools import (
    open_browser, open_url, click, js_click, type_text, select_option,
    scroll, get_text, wait_for_element, close_browser, get_page_state,
    press_key, hover, switch_tab, close_tab, upload_file, go_back,
    handle_alert, get_page_text, switch_to_iframe, wait_for_page_load
)

# Tool name → function mapping
TOOL_MAP = {
    "open_browser": open_browser,
    "open_url": open_url,
    "click": click,
    "js_click": js_click,
    "type_text": type_text,
    "select_option": select_option,
    "scroll": scroll,
    "get_text": get_text,
    "wait_for_element": wait_for_element,
    "close_browser": close_browser,
    "get_page_state": get_page_state,
    "press_key": press_key,
    "hover": hover,
    "switch_tab": switch_tab,
    "close_tab": close_tab,
    "upload_file": upload_file,
    "go_back": go_back,
    "handle_alert": handle_alert,
    "get_page_text": get_page_text,
    "switch_to_iframe": switch_to_iframe,
    "wait_for_page_load": wait_for_page_load,
}

SYSTEM_PROMPT = """You are a browser automation agent. You see the current browser state and must decide the NEXT SINGLE ACTION to take.

RULES:
1. Output exactly ONE tool call per response
2. Use element indices [0], [1], etc. from the browser state
3. If the goal is achieved, call task_complete(message="...")
4. If stuck after trying alternatives, call task_failed(reason="...")

TIPS:
- To search: find the input field, type_text(), then click search button or press_key("enter")
- If click() fails, try js_click()
- If element not visible, scroll("down") first
- For dropdowns: click to open, then click the option
"""


def call_model(goal: str, browser_state: str) -> dict:
    """Call local model with goal + current state"""
    
    prompt = f"""GOAL: {goal}

CURRENT BROWSER STATE:
{browser_state}

Based on the current state, what is the next action to achieve the goal?"""

    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "gpt-oss:20b",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "tools": BROWSER_TOOLS,
            "stream": False
        },
        timeout=120
    )
    return response.json()


async def execute_tool(name: str, args: dict) -> str:
    """Execute a tool and return result"""
    func = TOOL_MAP.get(name)
    if func:
        return await func(**args)
    return f"✗ Unknown tool: {name}"


async def run_agent(goal: str, max_steps: int = 30):
    """Main agent loop"""
    
    print(f"\n{'='*60}")
    print(f"GOAL: {goal}")
    print(f"{'='*60}\n")
    
    # Step 0: Open browser (hardcoded)
    print("[Step 0] Opening browser...")
    result = await open_browser()
    print(f"  → {result}")
    
    if "Failed" in result:
        print("Failed to open browser. Exiting.")
        return
    
    # Main loop
    for step in range(1, max_steps + 1):
        print(f"\n[Step {step}]")
        
        # Get current browser state
        browser_state = await get_page_state(include_text=False)
        print(f"  State: {browser_state[:200]}...")
        
        # Call model
        response = call_model(goal, browser_state)
        msg = response.get("message", {})
        
        # Check for tool calls
        tool_calls = msg.get("tool_calls")
        
        if not tool_calls:
            # No tool call - model might be done or confused
            content = msg.get("content", "")
            print(f"  Model said: {content}")
            
            if "complete" in content.lower() or "done" in content.lower():
                print("\n✓ Task appears complete!")
                break
            continue
        
        # Execute the tool
        tc = tool_calls[0]
        name = tc["function"]["name"]
        args = tc["function"].get("arguments", {})
        
        # Handle args if it's a string (some models return JSON string)
        if isinstance(args, str):
            import json
            args = json.loads(args) if args else {}
        
        print(f"  Action: {name}({args})")
        
        # Check for completion signals
        if name == "task_complete":
            print(f"\n✓ TASK COMPLETE: {args.get('message', '')}")
            break
        
        if name == "task_failed":
            print(f"\n✗ TASK FAILED: {args.get('reason', '')}")
            break
        
        # Execute the tool
        result = await execute_tool(name, args)
        print(f"  Result: {result}")
        
        # Small delay between actions
        await asyncio.sleep(0.5)
    
    else:
        print(f"\n⚠ Reached max steps ({max_steps})")
    
    print("\n" + "="*60)


async def main():
    # Example usage
    goal = input("Enter your goal (or press Enter for default): ").strip()
    
    if not goal:
        goal = "Go to google.com and search for 'weather today'"
    
    await run_agent(goal)


if __name__ == "__main__":
    asyncio.run(main())